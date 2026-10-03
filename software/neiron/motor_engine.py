"""Evolución continua independiente de las pantallas y del receptor HTTP."""
from collections import deque
from dataclasses import asdict
import json
from pathlib import Path
import threading
from .contract import utcnow, stamp, number, instant
from .motor_model import MotorModel, Settings, PARAMETERS, SCENARIOS

class MotorEngine:
    def __init__(self, data_dir):
        self.lock = threading.RLock()
        self.state_path = Path(data_dir) / "simulador_estado.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.model = MotorModel()
        self.signal = True
        self.latest_packet = None
        self.last_generated_at = None
        self.trend = deque(maxlen=180)
        self.error = None
        self.link = {"enabled": True, "state": "connecting", "message": "Esperando conexión local a neiron.",
                     "accepted": 0, "rejected": 0, "failures": 0, "last_received_at": None, "last_sequence": None,
                     "receiver_port": 8765}
        if self.state_path.exists():
            saved = json.loads(self.state_path.read_text(encoding="utf-8"))
            if saved.get("version") != 1:
                raise ValueError("Estado del simulador incompatible; conserve el archivo y use otra carpeta.")
            self.model.settings = Settings.validated(saved["settings"])
            for key in ("surface_c", "probe_c", "rpm", "phase", "elapsed_s"):
                setattr(self.model, key, number(saved[key], -55 if key.endswith("_c") else 0, 1e12, key))
            if type(saved["sequence"]) is not int or not 0 <= saved["sequence"] < 2**63-1:
                raise ValueError("Secuencia persistente inválida.")
            self.model.sequence = saved["sequence"]
            self.model.motor_on = bool(saved["motor_on"])
            self.model.scenario = saved["scenario"] if saved["scenario"] in SCENARIOS else "normal"
            # Un inicio del servicio reanuda adquisición. No acumula tiempo físico mientras estuvo cerrado.
            self.signal = self.model.scenario != "signal_loss"

    def audit(self, event, detail):
        with (self.state_path.parent / "eventos_simulador.jsonl").open("a",encoding="utf-8") as stream:
            stream.write(json.dumps({"at":stamp(utcnow()),"elapsed_s":self.model.elapsed_s,"sequence":self.model.sequence,"event":event,"detail":detail},ensure_ascii=False)+"\n")

    def persist(self):
        m = self.model
        record = {"version": 1, "saved_at": stamp(utcnow()), "settings": asdict(m.settings),
                  **{key:getattr(m,key) for key in ("surface_c","probe_c","rpm","phase","elapsed_s","sequence","motor_on","scenario")}}
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.state_path)

    def tick(self, real_dt=1.0, now=None):
        with self.lock:
            m = self.model
            if not m.running:
                self.latest_packet = None
                return
            m.step(real_dt)
            packet = m.packet(now or utcnow())
            self.last_generated_at = packet["acquired_at"]
            self.latest_packet = packet if self.signal else None
            self.trend.append({"at":packet["acquired_at"],"temperature_c":packet["temperature_c"],
                               "vibration_rms":packet["vibration_rms"],"elapsed_s":m.elapsed_s})
            self.persist()

    def command(self, raw):
        with self.lock:
            if not isinstance(raw,dict) or set(raw)!={"action"} or not isinstance(raw["action"],str):
                raise ValueError("Seleccione una acción del banco de pruebas.")
            action=raw["action"]
            if action=="motor_start": self.model.motor_on=True
            elif action=="motor_stop": self.model.motor_on=False
            elif action=="pause": self.model.running=False;self.latest_packet=None
            elif action=="resume": self.model.running=True
            elif action=="connect": self.link["enabled"]=True;self.link["state"]="connecting"
            elif action=="disconnect": self.link["enabled"]=False;self.link["state"]="disconnected";self.link["message"]="Envío desconectado por el operador; el modelo sigue evolucionando."
            elif action in SCENARIOS:
                self.model.scenario=action
                self.signal=action!="signal_loss"
                if not self.signal: self.latest_packet=None
            else: raise ValueError("Acción desconocida.")
            self.persist()
            self.audit("control",raw)
            return self.status()

    def configure(self, raw):
        with self.lock:
            self.model.settings=Settings.validated(raw)
            self.persist()
            self.audit("settings",raw)
            return self.status()

    def reserve_sequence(self, floor):
        with self.lock:
            if floor>self.model.sequence:
                self.model.sequence=floor
                self.persist()
            if self.latest_packet and self.latest_packet["sequence"]<=floor:
                self.latest_packet=None

    def status(self):
        with self.lock:
            m=self.model
            return {"source":"simulated","quality":"synthetic","ai":"disabled","hardware":"emulated",
                "model_version":"motor-pump-1", "motor_on":m.motor_on,"running":m.running,"signal":self.signal,
                "scenario":m.scenario,"settings":asdict(m.settings),"parameters":PARAMETERS,
                "elapsed_s":m.elapsed_s,"server_time":stamp(utcnow()),"last_generated_at":self.last_generated_at,
                "current":{"temperature_c":m.temperature_c,"vibration_rms":round(m.rms,4)} if self.last_generated_at and m.running and not self.error and (utcnow()-instant(self.last_generated_at)).total_seconds()<5 else None,
                "context":dict(m.context),"waveform":list(m.waveform),"trend":list(self.trend),
                "packet":dict(self.latest_packet) if self.latest_packet else None,
                "sequence":m.sequence,"link":dict(self.link),"error":self.error}
