"""Inicio conjunto de dos procesos locales; no reemplaza instancias existentes."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import webbrowser


def free_port(port):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        if hasattr(socket,"SO_EXCLUSIVEADDRUSE"): sock.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        sock.bind(("127.0.0.1",port))


def run():
    parser=argparse.ArgumentParser(description="Abrir el banco motor-bomba y neiron receptor")
    parser.add_argument("--receiver-port",type=int,default=8765)
    parser.add_argument("--simulator-port",type=int,default=8766)
    parser.add_argument("--data-dir",type=Path,help="Raíz opcional; crea subcarpetas receiver y simulator")
    parser.add_argument("--open-browser",action="store_true")
    args=parser.parse_args()
    if not 1<=args.receiver_port<=65535 or not 1<=args.simulator_port<=65535 or args.receiver_port==args.simulator_port:
        parser.error("Use dos puertos locales distintos entre 1 y 65535.")
    try:
        free_port(args.receiver_port);free_port(args.simulator_port)
    except OSError:
        parser.exit(1,"Un puerto del banco está ocupado. Cierre la ventana anterior de neiron/simulador y vuelva a abrir. Se conservan los datos y no se detiene ningún proceso ajeno.\n")
    base=Path(__file__).parent.parent
    receiver=[sys.executable,"-m","neiron.server","--profile","motor-pump","--input","external","--port",str(args.receiver_port),"--simulator-port",str(args.simulator_port)]
    simulator=[sys.executable,"-m","neiron.motor_server","--port",str(args.simulator_port),"--receiver-port",str(args.receiver_port)]
    if args.data_dir:
        receiver.extend(["--data-dir",str(args.data_dir.resolve()/"receiver")])
        simulator.extend(["--data-dir",str(args.data_dir.resolve()/"simulator")])
    children=[]
    environment=dict(os.environ,PYTHONUTF8="1")
    def relay(process,name):
        for line in process.stdout:
            print(f"[{name}] {line.rstrip()}",flush=True)
    try:
        for command,name in [(receiver,"neiron"),(simulator,"simulador")]:
            child=subprocess.Popen(command,cwd=base,env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8")
            children.append(child)
            threading.Thread(target=relay,args=(child,name),daemon=True).start()
        print(f"Banco listo: simulador http://127.0.0.1:{args.simulator_port} | neiron http://127.0.0.1:{args.receiver_port}\nMantenga esta ventana abierta. Ctrl+C cierra ambos servicios.",flush=True)
        opened=False
        started=time.monotonic()
        while True:
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError("Un servicio del banco terminó. Revise el mensaje anterior; se cerrará el otro.")
            if args.open_browser and not opened and time.monotonic()-started>1.5:
                webbrowser.open(f"http://127.0.0.1:{args.simulator_port}")
                webbrowser.open(f"http://127.0.0.1:{args.receiver_port}")
                opened=True
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nCerrando banco; mediciones y estado conservados.",flush=True)
    except (OSError,RuntimeError) as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)
    finally:
        # Ctrl+C también llega a los hijos de la misma consola. Dar tiempo al cierre antes de terminar rezagados.
        for child in children:
            if child.poll() is None:
                try: child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try: child.wait(timeout=3)
                    except subprocess.TimeoutExpired: child.kill();child.wait()

if __name__=="__main__":run()
