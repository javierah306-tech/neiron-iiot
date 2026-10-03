"""Contrato v1. La recepción añade su propia hora; nunca confía en la del emisor."""
from datetime import datetime, timezone
import math

ASSET = "lavadora-prueba"
DEVICE = "simulador-p01"
METHOD = "synthetic_rms_acceleration"
UNIT = "m/s²"

class PacketError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

def utcnow():
    return datetime.now(timezone.utc)

def instant(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("Fecha inválida: use ISO 8601 con zona horaria.")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Fecha inválida: use ISO 8601 con zona horaria.") from None
    if result.tzinfo is None:
        raise ValueError("La fecha debe incluir zona horaria.")
    return result.astimezone(timezone.utc)

def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

def number(value, low, high, label):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{label}: debe ser un número entre {low} y {high}.")
    return float(value)

def validate(raw, now, *, asset_id=ASSET, device_id=DEVICE, method=METHOD):
    try:
        fields = {"schema_version", "device_id", "asset_id", "sequence", "acquired_at", "source", "quality", "temperature_c", "vibration_rms", "vibration_unit", "vibration_method", "window_s"}
        if not isinstance(raw, dict) or set(raw) != fields:
            raise ValueError("Campos faltantes o desconocidos en el contrato v1.")
        if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
            raise ValueError("Versión de contrato no admitida.")
        if raw["source"] not in ("simulated", "real"):
            raise ValueError("Origen inválido.")
        if raw["source"] == "real":
            raise PacketError("real_disabled", "La recepción real está deshabilitada en P01.")
        if raw["device_id"] != device_id or raw["asset_id"] != asset_id:
            raise ValueError("Dispositivo o activo desconocido.")
        if type(raw["sequence"]) is not int or not 1 <= raw["sequence"] <= 2**63 - 1:
            raise ValueError("Secuencia inválida; debe ser un entero positivo.")
        if raw["quality"] != "synthetic":
            raise ValueError("El simulador solo admite calidad synthetic.")
        if raw["vibration_unit"] != UNIT or raw["vibration_method"] != method:
            raise ValueError("Unidad o método de vibración incorrectos.")
        p = dict(raw)
        p["window_s"] = number(raw["window_s"], 0.01, 60, "Ventana sintética (s)")
        p["temperature_c"] = number(raw["temperature_c"], -55, 125, "Temperatura (°C)")
        p["vibration_rms"] = number(raw["vibration_rms"], 0, 200, "Aceleración RMS (m/s²)")
        acquired = instant(raw["acquired_at"])
        age = (now - acquired).total_seconds()
        if age < -5:
            raise PacketError("future", "Hora de adquisición más de 5 s en el futuro.")
        if age > 10:
            raise PacketError("stale", "Paquete atrasado más de 10 s; no se usa como lectura actual.")
        p["acquired_at"] = stamp(acquired)
        p["received_at"] = stamp(now)
        return p
    except PacketError:
        raise
    except (ValueError, TypeError) as exc:
        raise PacketError("invalid", str(exc)) from None
