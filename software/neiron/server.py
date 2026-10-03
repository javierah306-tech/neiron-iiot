"""HTTP exclusivamente local; archivos estáticos propios y API JSON sin servicios externos."""
import argparse
import csv
from contextlib import closing
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os
from pathlib import Path
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from .contract import PacketError
from .service import Service
from . import __version__

STATIC = Path(__file__).parent / "static"
CSV_FIELDS = ["schema_version", "device_id", "asset_id", "sequence", "acquired_at", "received_at", "source", "quality", "temperature_c", "vibration_rms", "vibration_unit", "vibration_method", "window_s"]
CSV_HEADERS = ["version_contrato", "dispositivo", "activo", "secuencia", "adquisicion_UTC_ISO8601", "recepcion_UTC_ISO8601", "origen_simulated_o_real", "calidad", "temperatura_superficial_C", "aceleracion_RMS_m_s2", "unidad_vibracion", "metodo_vibracion", "ventana_s"]

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, service, handler=None):
        self.service = service
        super().__init__(address, handler or Handler)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        logging.info("HTTP %s", fmt % args)

    def headers_common(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")

    def response(self, data, status=200, content_type="application/json; charset=utf-8"):
        if content_type.startswith("application/json"):
            data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.headers_common()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def local_request(self):
        host = self.headers.get("Host", "")
        port = self.server.server_address[1]
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in allowed or self.client_address[0] != "127.0.0.1":
            self.response({"error": "Este servicio solo admite acceso local."}, 403)
            return False
        origin = self.headers.get("Origin")
        if (origin and origin not in {"http://" + h for h in allowed}) or self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.response({"error": "Solicitud desde un sitio externo rechazada."}, 403)
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        try:
            url = urlsplit(self.path)
            query = {k: v[-1] for k, v in parse_qs(url.query).items()}
            s = self.server.service
            if url.path == "/api/status":
                self.response(s.status())
            elif url.path == "/api/receiver":
                self.response(s.receiver())
            elif url.path == "/api/history":
                self.response(s.history(query))
            elif url.path == "/api/alarms":
                self.response(s.alarm_history())
            elif url.path == "/api/interventions":
                self.response(s.interventions())
            elif url.path == "/api/export.csv":
                with s.lock:
                    start, end = s.interval(query)
                # Cursor separado: no bloquea la adquisición durante una descarga extensa.
                import sqlite3
                with closing(sqlite3.connect(s.store.path)) as db:
                    db.row_factory = sqlite3.Row
                    rows = db.execute("SELECT * FROM measurements WHERE acquired_at BETWEEN ? AND ? ORDER BY acquired_at,id", (start, end))
                    self.send_response(200)
                    self.headers_common()
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", 'attachment; filename="neiron_mediciones_UTC.csv"')
                    self.end_headers()
                    buffer = io.StringIO(newline="")
                    writer = csv.writer(buffer, delimiter=";")
                    self.wfile.write(b"\xef\xbb\xbf")  # BOM para Excel Windows
                    writer.writerow(CSV_HEADERS)
                    self.wfile.write(buffer.getvalue().encode("utf-8"))
                    for row in rows:
                        buffer.seek(0)
                        buffer.truncate()
                        writer.writerow([row[k] for k in CSV_FIELDS])
                        self.wfile.write(buffer.getvalue().encode("utf-8"))
            else:
                routes = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/app.css": ("app.css", "text/css; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8")}
                if url.path not in routes:
                    self.response({"error": "Página inexistente."}, 404)
                    return
                name, mime = routes[url.path]
                self.response((STATIC / name).read_bytes(), content_type=mime)
        except ValueError as exc:
            self.response({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            logging.exception("Error GET")
            self.response({"error": "Error local al consultar datos. Revise el registro del servicio."}, 500)

    def do_POST(self):
        if not self.local_request():
            return
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.response({"error": "Use contenido application/json."}, 415)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32768:
                self.response({"error": "Solicitud vacía o mayor que 32 KiB."}, 413)
                return
            raw = json.loads(self.rfile.read(length), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("NaN e Infinity no son válidos.")))
            path, s = urlsplit(self.path).path, self.server.service
            if path == "/api/simulation":
                self.response(s.control(raw))
            elif path == "/api/rules":
                self.response(s.configure(raw))
            elif path == "/api/interventions":
                self.response(s.add_intervention(raw), 201)
            elif path.startswith("/api/alarms/") and path.endswith("/ack"):
                alarm_id = int(path.split("/")[3])
                s.acknowledge(alarm_id, raw)
                self.response({"ok": True})
            elif path == "/api/packets":
                # Punto local de prueba del contrato, habilitado solo mientras el simulador corre.
                with s.lock:
                    if not s.simulator.running:
                        self.response({"error": "Active la recepción o simulación para aceptar paquetes locales."}, 409)
                        return
                    p = s.receive(raw)
                    s.simulator.sequence = max(s.simulator.sequence, p["sequence"])
                self.response({"accepted": True, "received_at": p["received_at"]}, 201)
            else:
                self.response({"error": "Ruta inexistente."}, 404)
        except PacketError as exc:
            self.response({"error": str(exc), "code": exc.code}, 409 if exc.code in {"duplicate", "out_of_order"} else 422)
        except LookupError as exc:
            self.response({"error": str(exc)}, 404)
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            self.response({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            logging.exception("Error POST")
            self.response({"error": "No se pudo guardar. Revise el registro local del servicio."}, 500)

    def setup(self):
        super().setup()
        self.connection.settimeout(10)


def run():
    parser = argparse.ArgumentParser(description="neiron P01 local — datos simulados")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--profile", choices=("washer", "motor-pump"), default="washer")
    parser.add_argument("--input", choices=("internal", "external"), default="internal")
    parser.add_argument("--simulator-port", type=int, default=8766)
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Puerto fuera de rango.")
    if args.data_dir is None:
        folder = "motor-bomba" if args.profile == "motor-pump" else "prototipo-01"
        args.data_dir = Path(os.environ.get("NEIRON_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "neiron" / folder)))
    args.data_dir.mkdir(parents=True, exist_ok=True)
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(handlers=[RotatingFileHandler(args.data_dir / "operacion.log", maxBytes=2000000, backupCount=3, encoding="utf-8")], level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    try:
        service = Service(args.data_dir / "neiron.sqlite3", profile=args.profile, input_mode=args.input)
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    service.simulator_port = args.simulator_port
    stop = threading.Event()
    try:
        server = Server(("127.0.0.1", args.port), service)
    except OSError as exc:
        service.close()
        parser.exit(1, f"No se pudo abrir el puerto local {args.port}: {exc}. Cierre la otra instancia o use --port 8766.\n")

    def simulation_loop():
        while not stop.wait(1.0):
            try:
                service.tick()
            except Exception:
                logging.exception("Simulación interrumpida")
                with service.lock:
                    service.failure = "Error de adquisición o almacenamiento. Detenga el servicio y revise operacion.log."
                stop.set()

    worker = threading.Thread(target=simulation_loop, daemon=True, name="neiron-simulator")
    worker.start()
    url = f"http://127.0.0.1:{args.port}"
    print(f"neiron {__version__} | DATOS SIMULADOS | IA desactivada\nAbrir: {url}\nDatos: {args.data_dir.resolve()}\nCierre: Ctrl+C en esta ventana. Perfil: {args.profile}. Entrada: {args.input}.", flush=True)
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nCerrando neiron; historial conservado.")
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=3)
        service.close()

if __name__ == "__main__":
    run()
