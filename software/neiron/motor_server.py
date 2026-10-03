"""Segunda aplicación HTTP: modelo motor-bomba y emisor de telemetría a neiron."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import threading
import time
import webbrowser
from urllib.parse import urlsplit
from .server import Handler, Server, STATIC
from .motor_engine import MotorEngine
from .motor_transport import LocalSender

MOTOR_STATIC=Path(__file__).parent/"motor_static"

class MotorHandler(Handler):
    def do_GET(self):
        if not self.local_request(): return
        try:
            path=urlsplit(self.path).path
            if path=="/api/status": self.response(self.server.service.status());return
            routes={"/":(MOTOR_STATIC/"index.html","text/html; charset=utf-8"),
                "/app.css":(STATIC/"app.css","text/css; charset=utf-8"),
                "/sim.css":(MOTOR_STATIC/"sim.css","text/css; charset=utf-8"),
                "/sim.js":(MOTOR_STATIC/"sim.js","text/javascript; charset=utf-8")}
            if path not in routes: self.response({"error":"Página inexistente."},404);return
            file,mime=routes[path];self.response(file.read_bytes(),content_type=mime)
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            logging.exception("Error simulador GET")
            self.response({"error":"No se pudo consultar el simulador. Revise el registro local."},500)

    def do_POST(self):
        if not self.local_request(): return
        try:
            if self.headers.get("Content-Type","").split(";")[0]!="application/json": self.response({"error":"Use application/json."},415);return
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=32768: self.response({"error":"Solicitud vacía o demasiado grande."},413);return
            raw=json.loads(self.rfile.read(length),parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Número no finito.")))
            path=urlsplit(self.path).path
            if path=="/api/control": self.response(self.server.service.command(raw))
            elif path=="/api/settings": self.response(self.server.service.configure(raw))
            else: self.response({"error":"Ruta inexistente."},404)
        except (ValueError,TypeError,UnicodeDecodeError) as exc: self.response({"error":str(exc)},400)
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            logging.exception("Error simulador POST")
            self.response({"error":"No se pudo guardar el cambio. Revise el registro local."},500)

def run():
    parser=argparse.ArgumentParser(description="Simulador ficticio de motor monofásico y bomba")
    parser.add_argument("--port",type=int,default=8766)
    parser.add_argument("--receiver-port",type=int,default=8765)
    parser.add_argument("--data-dir",type=Path,default=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/".local"/"share")))/"neiron"/"simulador-motor")
    parser.add_argument("--open-browser",action="store_true")
    args=parser.parse_args()
    if not 1<=args.port<=65535 or not 1<=args.receiver_port<=65535 or args.port==args.receiver_port:
        parser.error("Use puertos distintos entre 1 y 65535.")
    args.data_dir.mkdir(parents=True,exist_ok=True)
    logging.Formatter.converter=time.gmtime
    logging.basicConfig(handlers=[RotatingFileHandler(args.data_dir/"simulador.log",maxBytes=2000000,backupCount=3,encoding="utf-8")],level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",datefmt="%Y-%m-%dT%H:%M:%SZ")
    try:
        engine=MotorEngine(args.data_dir)
        sender=LocalSender(engine,args.receiver_port)
        server=Server(("127.0.0.1",args.port),engine,MotorHandler)
    except (ValueError,OSError) as exc: parser.exit(1,f"No se pudo iniciar el simulador: {exc}\n")
    stop=threading.Event()

    def model_loop():
        previous=time.monotonic()
        deadline=previous
        while not stop.is_set():
            deadline+=1
            if stop.wait(max(0,deadline-time.monotonic())): break
            now=time.monotonic()
            try: engine.tick(min(120,max(0,now-previous)))
            except Exception:
                logging.exception("Modelo detenido por error")
                with engine.lock: engine.error="Error del modelo o persistencia. Cierre y revise simulador.log."
                return
            previous=now
            if deadline<now-1: deadline=now

    def sender_loop():
        while not stop.wait(1):
            try: sender.send_latest()
            except Exception:
                logging.exception("Error del emisor")
                sender.update(state="error",message="Error del emisor local. Revise simulador.log.")

    workers=[threading.Thread(target=model_loop,daemon=True,name="motor-model"),threading.Thread(target=sender_loop,daemon=True,name="motor-sender")]
    for worker in workers: worker.start()
    url=f"http://127.0.0.1:{args.port}"
    print(f"Simulador motor–bomba | DATOS FICTICIOS / ESP32 EMULADO\nSimulador: {url}\nReceptor neiron: http://127.0.0.1:{args.receiver_port}\nEstado: {args.data_dir.resolve()}\nMotor y generación iniciados. Cierre con Ctrl+C.",flush=True)
    if args.open_browser: webbrowser.open(url)
    try: server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt: print("\nCerrando simulador.")
    finally:
        stop.set();server.server_close()
        for worker in workers: worker.join(timeout=3)
        with engine.lock: engine.persist()

if __name__=="__main__": run()
