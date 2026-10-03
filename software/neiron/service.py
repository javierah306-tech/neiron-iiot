"""Orquesta recepción, persistencia y alarmas; se reemplaza el emisor sin cambiar las reglas."""
from datetime import timedelta
import threading
from .contract import ASSET, DEVICE, PacketError, instant, stamp, utcnow, validate
from .storage import Storage, DEFAULT_RULES
from .profiles import PROFILES
from .alarms import Alarms, validate_rules
from .simulator import Simulator, SCENARIOS

class Service:
    def __init__(self, path, clock=utcnow, profile="washer", input_mode="internal"):
        self.lock = threading.RLock()
        self.clock = clock
        if profile not in PROFILES or input_mode not in {"internal", "external"}:
            raise ValueError("Perfil o modo de recepción inválido.")
        if profile == "motor-pump" and input_mode != "external":
            raise ValueError("El perfil motor-bomba necesita el simulador HTTP externo.")
        self.profile_name, self.input_mode = profile, input_mode
        self.profile = PROFILES[profile]
        defaults = dict(DEFAULT_RULES, temperature_limit=self.profile["temperature_limit"], vibration_limit=self.profile["vibration_limit"])
        self.store = Storage(path, self.profile["asset_id"], self.profile["name"], defaults)
        self.alarms = Alarms(self.store)
        seq = self.store.db.execute("SELECT COALESCE(MAX(sequence),0) FROM measurements WHERE device_id=? AND source='simulated'", (self.profile["device_id"],)).fetchone()[0]
        self.simulator = Simulator(seq)
        self.last = None  # el historial del proceso anterior nunca se presenta como lectura actual
        self.started_at = self.clock() if input_mode == "external" else None
        self.simulator.running = input_mode == "external"
        self.failure = None
        self.alarms.signal(self.simulator.running, 0, self.clock(), self.store.rules())

    def receive(self, raw):
        with self.lock:
            now = self.clock()
            try:
                p = validate(raw, now, asset_id=self.profile["asset_id"], device_id=self.profile["device_id"], method=self.profile["method"])
                exists = self.store.db.execute("SELECT 1 FROM measurements WHERE device_id=? AND source=? AND sequence=?", (p["device_id"], p["source"], p["sequence"])).fetchone()
                if exists:
                    raise PacketError("duplicate", "Paquete duplicado; no se almacena de nuevo.")
                previous = self.store.latest()
                if previous and (p["sequence"] < previous["sequence"] or p["acquired_at"] < previous["acquired_at"]):
                    raise PacketError("out_of_order", "Paquete fuera de orden; no modifica el estado actual.")
                self.store.insert(p)
                self.last = p
                self.alarms.measurement(p, now, self.store.rules())
                return p
            except PacketError as exc:
                self.store.reception_event(stamp(now), exc.code, str(exc))
                raise

    def control(self, raw):
        with self.lock:
            if not isinstance(raw, dict) or set(raw) != {"action"}:
                raise ValueError("Seleccione una acción de simulación válida.")
            action = raw["action"]
            now = self.clock()
            if action == "start":
                if not self.simulator.running:
                    self.started_at, self.last = now, None
                    self.alarms.pending.clear()
                    self.simulator.running = True
            elif action == "stop":
                self.simulator.running = False
                self.last = None
                self.alarms.signal(False, 0, now, self.store.rules())
            elif action in SCENARIOS and self.input_mode == "internal":
                self.simulator.scenario = action
            else:
                raise ValueError("Acción desconocida.")
            self.store.reception_event(stamp(now), "control", str(action))
            return self.status()

    def tick(self):
        with self.lock:
            now = self.clock()
            # Primero invalidar lecturas y duraciones vencidas, también al recuperar la señal.
            if self.simulator.running:
                ref = instant(self.last["received_at"]) if self.last else self.started_at
                age = max(0, (now - ref).total_seconds())
                self.alarms.signal(True, age, now, self.store.rules())
            p = self.simulator.packet(now) if self.input_mode == "internal" else None
            if p:
                try:
                    self.receive(p)
                except PacketError:
                    pass  # rechazo ya auditado; el siguiente paquete se evalúa normalmente
            return self.status()

    def status(self):
        with self.lock:
            now, rules = self.clock(), self.store.rules()
            running = self.simulator.running
            age = max(0, (now - instant(self.last["received_at"])).total_seconds()) if self.last else None
            current = self.last if running and age is not None and age < rules["no_data_s"] and not self.failure else None
            active = self.store.rows("SELECT * FROM alarms WHERE recovered_at IS NULL ORDER BY id DESC")
            state = "stopped" if not running else "no_data" if not current else "alarm" if active else "normal"
            if self.failure:
                state, current = "error", None
            last_stored = self.store.latest()
            return {"asset": {"id": self.profile["asset_id"], "name": self.profile["name"]}, "profile": self.profile_name, "input_mode": self.input_mode, "simulator_port": getattr(self,"simulator_port",8766), "state": state,
                    "current": current, "last_received_at": last_stored["received_at"] if last_stored else None,
                    "server_time": stamp(now), "running": running, "scenario": self.simulator.scenario,
                    "active_alarms": active, "rules": rules, "ai": "disabled", "hardware": "not_connected",
                    "source": "simulated", "error": self.failure,
                    "trend": list(reversed(self.store.rows("SELECT acquired_at,temperature_c,vibration_rms FROM measurements ORDER BY id DESC LIMIT 120"))),
                    "reception_events": self.store.rows("SELECT * FROM reception_events ORDER BY id DESC LIMIT 15")}

    def receiver(self):
        with self.lock:
            seq = self.store.db.execute("SELECT COALESCE(MAX(sequence),0) FROM measurements WHERE device_id=? AND source='simulated'", (self.profile["device_id"],)).fetchone()[0]
            return {"profile": self.profile_name, "input_mode": self.input_mode,
                    "asset_id": self.profile["asset_id"], "device_id": self.profile["device_id"],
                    "method": self.profile["method"], "schema_version": 1,
                    "enabled": self.simulator.running, "last_sequence": seq, "source": "simulated"}

    def configure(self, raw):
        with self.lock:
            rules = validate_rules(raw)
            self.store.save_rules(rules, stamp(self.clock()))
            self.alarms.pending.clear()
            return rules

    def interval(self, query):
        start = instant(query["from"]) if query.get("from") else self.clock() - timedelta(days=1)
        end = instant(query["to"]) if query.get("to") else self.clock()
        if start > end:
            raise ValueError("La fecha inicial debe ser anterior a la fecha final.")
        return stamp(start), stamp(end)

    def history(self, query):
        with self.lock:
            start, end = self.interval(query)
            args = (start, end)
            total = self.store.db.execute("SELECT COUNT(*) FROM measurements WHERE acquired_at BETWEEN ? AND ?", args).fetchone()[0]
            rows = self.store.rows("SELECT * FROM measurements WHERE acquired_at BETWEEN ? AND ? ORDER BY acquired_at DESC,id DESC LIMIT 2000", args)
            return {"rows": rows, "total": total, "limit": 2000, "from": start, "to": end}

    def alarm_history(self):
        with self.lock:
            return {"rows": self.store.rows("SELECT * FROM alarms ORDER BY id DESC LIMIT 500"),
                    "events": self.store.rows("SELECT * FROM alarm_events ORDER BY id DESC LIMIT 2000"),
                    "rules": self.store.rules()}

    def interventions(self):
        with self.lock:
            return {"rows": self.store.rows("SELECT * FROM interventions ORDER BY intervention_at DESC,id DESC LIMIT 1000")}

    def add_intervention(self, raw):
        with self.lock:
            fields = {"asset_id", "intervention_at", "author", "work_type", "observations"}
            if not isinstance(raw, dict) or set(raw) != fields or raw["asset_id"] != self.profile["asset_id"]:
                raise ValueError("Datos o activo de intervención inválidos.")
            at = instant(raw["intervention_at"])
            if at > self.clock() + timedelta(minutes=5):
                raise ValueError("La intervención no puede tener una fecha futura.")
            cleaned = {}
            for key, max_len in (("author", 100), ("work_type", 100), ("observations", 4000)):
                value = raw[key]
                if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_len:
                    raise ValueError(f"{key}: obligatorio, hasta {max_len} caracteres.")
                cleaned[key] = value.strip()
            with self.store.db:
                cur = self.store.db.execute("INSERT INTO interventions(asset_id,intervention_at,recorded_at,author,work_type,observations) VALUES(?,?,?,?,?,?)",
                    (self.profile["asset_id"], stamp(at), stamp(self.clock()), cleaned["author"], cleaned["work_type"], cleaned["observations"]))
            return self.store.rows("SELECT * FROM interventions WHERE id=?", (cur.lastrowid,))[0]

    def acknowledge(self, alarm_id, raw):
        with self.lock:
            if not isinstance(raw, dict) or set(raw) != {"author"} or not isinstance(raw["author"], str) or not 1 <= len(raw["author"].strip()) <= 100:
                raise ValueError("Indique el autor del reconocimiento (1–100 caracteres).")
            self.alarms.acknowledge(alarm_id, raw["author"].strip(), self.clock())

    def close(self):
        with self.lock:
            self.store.close()
