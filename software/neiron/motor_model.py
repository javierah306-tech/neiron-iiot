"""Banco motor-bomba reducido, ilustrativo. No identifica ni calibra el motor de la foto."""
from dataclasses import dataclass
import math
import random
from .contract import number, stamp, UNIT
from .profiles import PROFILES

SCENARIOS = {"normal", "blocked_cooling", "misalignment", "cavitation", "signal_loss", "recovery"}
PARAMETERS = {"rated_power_w": 3700.0, "voltage_v": 230.0, "line_hz": 50.0,
    "poles": 2, "rated_rpm": 2910.0, "rated_efficiency": 0.85,
    "flow_nominal_m3h": 18.0, "head_nominal_m": 45.0,
    "pump_efficiency": 0.64, "thermal_capacity_j_k": 16000.0,
    "thermal_resistance_k_w": 0.055, "sample_rate_hz": 1000, "window_s": 1.0,
    "impeller_blades": 6}

@dataclass
class Settings:
    ambient_c: float = 22.0
    valve_opening: float = 1.0
    time_scale: float = 1.0

    @classmethod
    def validated(cls, raw):
        if not isinstance(raw, dict) or set(raw) != {"ambient_c", "valve_opening", "time_scale"}:
            raise ValueError("Envíe ambiente, apertura de válvula y escala temporal.")
        vals = {"ambient_c": number(raw["ambient_c"], 0, 45, "Ambiente (°C)"),
                "valve_opening": number(raw["valve_opening"], 0.25, 1.2, "Apertura relativa de válvula"),
                "time_scale": number(raw["time_scale"], 1, 60, "Escala temporal")}
        if vals["time_scale"] not in {1, 10, 60}:
            raise ValueError("Las escalas disponibles son 1×, 10× y 60×.")
        return cls(**vals)

class MotorModel:
    def __init__(self, seed=512):
        self.seed = seed
        self.settings = Settings()
        self.running = True
        self.motor_on = True
        self.scenario = "normal"
        self.elapsed_s = 0.0
        self.rpm = 0.0
        self.surface_c = self.settings.ambient_c
        self.probe_c = self.surface_c
        self.phase = 0.0
        self.sequence = 0
        self.context = {}
        self.waveform = []
        self.rms = 0.0
        self.temperature_c = self.surface_c

    def hydraulics(self, rpm):
        r = max(0.0, rpm / PARAMETERS["rated_rpm"])
        q_ratio = r * math.sqrt(65 / (20 + 45 / self.settings.valve_opening**2))
        flow = PARAMETERS["flow_nominal_m3h"] * q_ratio
        head = 45 / self.settings.valve_opening**2 * q_ratio**2
        if self.scenario == "cavitation":
            flow *= 0.78
            head *= 0.8
        relative_bep = q_ratio / max(r, 0.001)
        efficiency = max(0.38, 0.64 * math.exp(-0.7 * (relative_bep - 1)**2))
        hydraulic = 1000 * 9.80665 * (flow / 3600) * head
        shaft = hydraulic / efficiency + 120 * r**3
        return {"flow_m3h": flow, "head_m": head, "pressure_bar": head * 1000 * 9.80665 / 100000,
                "hydraulic_power_w": hydraulic, "shaft_power_w": shaft,
                "pump_efficiency": efficiency, "load_fraction": shaft / 3700}

    def step(self, real_dt):
        if not self.running:
            return
        dt = number(real_dt, 0, 120, "Paso de reloj (s)") * self.settings.time_scale
        # Subpasos de <=1 s mantienen la inercia y el retardo del sensor a cualquier escala.
        count = max(1, math.ceil(dt))
        delta = dt / count
        for _ in range(count):
            hydraulic = self.hydraulics(self.rpm)
            target_rpm = 3000 - (30 + 60 * min(1.5, hydraulic["load_fraction"])) if self.motor_on else 0
            tau_speed = 1.1 if self.motor_on else 1.8
            self.rpm += (target_rpm - self.rpm) * (1 - math.exp(-delta / tau_speed))
            hydraulic = self.hydraulics(self.rpm)
            if self.motor_on:
                # A carga nominal: pérdidas ~653 W, coherentes con rendimiento de referencia 85%.
                losses = 180 + (3700 / 0.85 - 3700 - 180) * hydraulic["load_fraction"]**2
                conductance = (1 / 0.055) * (0.35 + 0.65 * self.rpm / 2910)
                if self.scenario == "blocked_cooling":
                    conductance *= 0.42
            else:
                losses, conductance = 0.0, 5.5
            target_c = self.settings.ambient_c + losses / conductance
            self.surface_c += (target_c - self.surface_c) * (1 - math.exp(-conductance * delta / 16000))
            self.probe_c += (self.surface_c - self.probe_c) * (1 - math.exp(-delta / 8))
            self.elapsed_s += delta
            hydraulic.update({"rpm": self.rpm, "losses_w": losses,
                "electrical_power_w": hydraulic["shaft_power_w"] + losses if self.motor_on else 0,
                "surface_model_c": self.surface_c, "equilibrium_model_c": target_c,
                "thermal_tau_s": 16000 / conductance})
            self.context = hydraulic

    def vibration_window(self):
        rng = random.Random(self.seed + self.sequence)
        speed_ratio = min(1.1, max(0.0, self.rpm / 2910))
        f = self.rpm / 60
        load = self.context.get("load_fraction", 0)
        modulation = 1 + 0.04 * math.sin(self.elapsed_s / 23)
        imbalance = (0.60 + 0.18 * load) * speed_ratio**2 * modulation
        alignment = (5.8 if self.scenario == "misalignment" else 0.15) * speed_ratio**2
        blade = (1.1 if self.scenario == "cavitation" else 0.2) * speed_ratio**2
        electrical = 0.22 * speed_ratio if self.motor_on else 0
        noise = (3.0 if self.scenario == "cavitation" else 0.035) * speed_ratio + 0.015
        axes = [[], [], []]
        for i in range(1000):
            t = i / 1000
            phase = self.phase + 2 * math.pi * f * t
            a = imbalance * math.sin(phase)
            b = alignment * math.sin(2 * phase + 0.2)
            c = blade * math.sin(6 * phase + 0.7)
            e = electrical * math.sin(2 * math.pi * 100 * t)
            # Banda de ruido ilustrativa, sin un diagnóstico de cavitación validado.
            rough = noise * rng.gauss(0, 1)
            axes[0].append(a + b + 0.5 * c + 0.35 * rough)
            axes[1].append(0.8 * imbalance * math.cos(phase) + 0.35 * b + e + rough)
            axes[2].append(0.35 * a + 0.7 * b + 0.45 * c + 0.5 * rough)
        # Aceleración dinámica: remover media, equivalente ilustrativo a retirar gravedad/DC.
        means = [sum(v) / len(v) for v in axes]
        dynamic = [[v - mean for v in axis] for axis, mean in zip(axes, means)]
        self.rms = math.sqrt(sum(sum(v*v for v in axis) for axis in dynamic) / 1000)
        self.waveform = [{"t_ms": i, "x": round(dynamic[0][i], 4),
                          "y": round(dynamic[1][i], 4), "z": round(dynamic[2][i], 4)} for i in range(120)]
        self.phase = (self.phase + 2 * math.pi * f) % (2 * math.pi)
        self.context.update({"rotation_hz": f, "electrical_harmonic_hz": 100,
            "blade_pass_hz": 6 * f, "sample_rate_hz": 1000, "sample_count": 1000,
            "gravity_removed": True, "rms_definition": "sqrt(mean(ax²+ay²+az²))",
            "rms_unrounded": self.rms})
        self.temperature_c = round(min(125, max(-55, self.probe_c + rng.gauss(0, 0.018))) * 16) / 16
        self.context["temperature_saturated"] = not -55 <= self.probe_c <= 125

    def packet(self, now):
        self.sequence += 1
        self.vibration_window()
        p = PROFILES["motor-pump"]
        return {"schema_version": 1, "device_id": p["device_id"], "asset_id": p["asset_id"],
                "sequence": self.sequence, "acquired_at": stamp(now), "source": "simulated",
                "quality": "synthetic", "temperature_c": self.temperature_c,
                "vibration_rms": round(self.rms, 4), "vibration_unit": UNIT,
                "vibration_method": p["method"], "window_s": 1.0}
