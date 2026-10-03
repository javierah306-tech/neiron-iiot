"""Un activo por perfil/base. La lavadora original y el banco motor no mezclan historial."""
from .contract import ASSET, DEVICE, METHOD
PROFILES = {
    "washer": {"asset_id": ASSET, "name": "Lavadora de prueba", "device_id": DEVICE,
               "method": METHOD, "temperature_limit": 45.0, "vibration_limit": 2.0},
    "motor-pump": {"asset_id": "motor-bomba-5hp", "name": "Motor 5 HP · bomba de agua",
                   "device_id": "esp32-motor-simulado", "method": "synthetic_vector_rms_1000hz",
                   "temperature_limit": 75.0, "vibration_limit": 3.0},
}
