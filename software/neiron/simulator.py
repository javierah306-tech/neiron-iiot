"""Indicadores sintéticos: no calcula RMS a partir de muestras de acelerómetro."""
import math
from .contract import ASSET, DEVICE, METHOD, UNIT, stamp

SCENARIOS = {"normal", "hot", "vibration", "signal_loss", "recovery"}

class Simulator:
    def __init__(self, sequence=0):
        self.sequence = sequence
        self.running = False
        self.scenario = "normal"

    def packet(self, now):
        if not self.running or self.scenario == "signal_loss":
            return None
        self.sequence += 1
        wave = math.sin(self.sequence * 0.43)
        return {"schema_version": 1, "device_id": DEVICE, "asset_id": ASSET,
                "sequence": self.sequence, "acquired_at": stamp(now),
                "source": "simulated", "quality": "synthetic",
                "temperature_c": round((54 if self.scenario == "hot" else 31) + wave * 0.8, 2),
                "vibration_rms": round((3.5 if self.scenario == "vibration" else 0.6) + wave * 0.12, 3),
                "vibration_unit": UNIT, "vibration_method": METHOD, "window_s": 1.0}
