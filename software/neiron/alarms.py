"""Reglas deterministas independientes del simulador y sin dependencia de IA."""
from .contract import number, stamp
from .storage import DEFAULT_RULES

def validate_rules(raw):
    if not isinstance(raw, dict) or set(raw) != set(DEFAULT_RULES):
        raise ValueError("Envíe todos los campos de umbrales, sin campos adicionales.")
    r = {k: number(raw[k], *limits, k) for k, limits in {
        "temperature_limit": (-40, 120), "temperature_hysteresis": (0.1, 30),
        "vibration_limit": (0.1, 190), "vibration_hysteresis": (0.01, 30),
        "minimum_duration_s": (1, 60), "no_data_s": (2, 120)}.items()}
    if r["vibration_hysteresis"] >= r["vibration_limit"]:
        raise ValueError("La histéresis de vibración debe ser menor que su umbral.")
    return r

class Alarms:
    def __init__(self, storage):
        self.store = storage
        self.pending = {}

    def active(self, kind):
        rows = self.store.rows("SELECT * FROM alarms WHERE kind=? AND recovered_at IS NULL", (kind,))
        return rows[0] if rows else None

    def update(self, kind, bad, recovered, now, duration=0, value=None, limit=None, detail=""):
        active = self.active(kind)
        key = (kind, "recovery" if active else "start")
        condition = recovered if active else bad
        if not condition:
            self.pending.pop(key, None)
            return
        since = self.pending.setdefault(key, now)
        if (now - since).total_seconds() < duration:
            return
        at = stamp(now)
        with self.store.db:
            if active:
                self.store.db.execute("UPDATE alarms SET recovered_at=? WHERE id=?", (at, active["id"]))
                alarm_id, event = active["id"], "recovered"
            else:
                cur = self.store.db.execute("INSERT INTO alarms(kind,started_at,start_value,start_limit) VALUES(?,?,?,?)", (kind, at, value, limit))
                alarm_id, event = cur.lastrowid, "started"
            self.store.db.execute("INSERT INTO alarm_events(alarm_id,at,event,detail) VALUES(?,?,?,?)", (alarm_id, at, event, detail))
        self.pending.pop(key, None)

    def measurement(self, packet, now, rules):
        for kind, field, prefix in (("temperature", "temperature_c", "temperature"), ("vibration", "vibration_rms", "vibration")):
            value, limit = packet[field], rules[prefix + "_limit"]
            self.update(kind, value >= limit, value <= limit - rules[prefix + "_hysteresis"], now,
                        rules["minimum_duration_s"], value, limit,
                        f"Indicador simulado: {value}; umbral ilustrativo: {limit}.")
        self.update("no_data", False, True, now, detail="Se recibió un paquete válido.")

    def signal(self, running, age, now, rules):
        if not running:
            self.pending.clear()
            self.update("no_data", False, True, now, detail="Supervisión suspendida: simulación detenida por el operador. No confirma señal física.")
        elif age >= rules["no_data_s"]:
            self.pending.clear()  # no acumular duración de una lectura que ya dejó de ser actual
            self.update("no_data", True, False, now, value=age, limit=rules["no_data_s"], detail="No se reciben paquetes válidos dentro del plazo ilustrativo.")

    def acknowledge(self, alarm_id, author, now):
        rows = self.store.rows("SELECT * FROM alarms WHERE id=?", (alarm_id,))
        if not rows:
            raise LookupError("Alarma inexistente.")
        if rows[0]["acknowledged_at"]:
            return  # reconocimiento idempotente, no elimina ni recupera la causa
        at = stamp(now)
        with self.store.db:
            self.store.db.execute("UPDATE alarms SET acknowledged_at=?,acknowledged_by=? WHERE id=?", (at, author, alarm_id))
            self.store.db.execute("INSERT INTO alarm_events(alarm_id,at,event,detail) VALUES(?,?,?,?)", (alarm_id, at, "acknowledged", f"Reconocida por {author}."))
