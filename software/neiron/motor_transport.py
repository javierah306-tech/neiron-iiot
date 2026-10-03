"""Emisor exclusivamente a 127.0.0.1. Sin proxies, redirecciones ni servicios externos."""
import http.client
import json
from .profiles import PROFILES

class LocalSender:
    def __init__(self, engine, port=8765):
        if type(port) is not int or not 1<=port<=65535:
            raise ValueError("Puerto del receptor inválido.")
        self.engine=engine
        self.port=port
        self.last_attempt=None
        engine.link["receiver_port"]=port

    def request(self, method, path, data=None):
        connection=http.client.HTTPConnection("127.0.0.1",self.port,timeout=0.6)
        try:
            body=None if data is None else json.dumps(data,ensure_ascii=False,allow_nan=False).encode("utf-8")
            connection.request(method,path,body=body,headers={"Content-Type":"application/json"} if data is not None else {})
            response=connection.getresponse()
            payload=response.read(65537)
            if len(payload)>65536: raise ValueError("Respuesta local demasiado grande.")
            return response.status,json.loads(payload)
        finally: connection.close()

    def update(self, **values):
        with self.engine.lock: self.engine.link.update(values)

    def send_latest(self):
        with self.engine.lock:
            e=self.engine
            if not e.link["enabled"]: return
            if not e.model.running:
                self.update(state="paused",message="Simulador pausado: no se generan ni envían paquetes.")
                return
            if not e.signal:
                self.update(state="signal_loss",message="Pérdida de señal simulada: modelo en marcha, envío interrumpido.")
                return
            packet=dict(e.latest_packet) if e.latest_packet else None
        if packet is None or packet["sequence"]==self.last_attempt: return
        self.last_attempt=packet["sequence"]
        try:
            code, receiver=self.request("GET","/api/receiver")
            p=PROFILES["motor-pump"]
            if code!=200 or receiver.get("profile")!="motor-pump" or receiver.get("input_mode")!="external" or receiver.get("asset_id")!=p["asset_id"] or receiver.get("device_id")!=p["device_id"]:
                self.update(state="wrong_profile",message="El puerto responde, pero no es el perfil motor–bomba externo. Abra INICIAR_MOTOR_BOMBA.bat; conserve cerrada la lavadora en ese puerto.")
                return
            if not receiver.get("enabled"):
                self.update(state="suspended",message="Recepción suspendida en neiron. Pulse Activar recepción allí.")
                return
            floor=receiver.get("last_sequence")
            if type(floor) is not int or not 0<=floor<2**63-1:
                raise ValueError("Secuencia del receptor inválida.")
            if floor>=packet["sequence"]:
                e.reserve_sequence(floor)
                self.update(state="connecting",message="Secuencia sincronizada con el historial; esperando un paquete nuevo.")
                return
            code,result=self.request("POST","/api/packets",packet)
            if code==201 and result.get("accepted"):
                with e.lock:
                    e.link["accepted"]+=1
                    e.link.update(state="connected",message="neiron confirmó la recepción y guardado del último paquete.",
                                  last_received_at=result["received_at"],last_sequence=packet["sequence"])
            else:
                with e.lock: e.link["rejected"]+=1
                self.update(state="rejected",message="neiron rechazó el paquete: "+str(result.get("error","respuesta desconocida")))
        except (OSError,ValueError,http.client.HTTPException) as exc:
            with e.lock: e.link["failures"]+=1
            self.update(state="unavailable",message="neiron no está disponible en 127.0.0.1:"+str(self.port)+". Se reintentará con datos nuevos; no se acumulan paquetes atrasados.")
