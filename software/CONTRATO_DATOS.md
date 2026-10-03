# Contrato de datos P01 · versión 1

Dos representaciones: paquete de entrada del emisor y registro aceptado por el receptor. La hora de recepción **es propiedad del servidor**, no un dato confiado al emisor. Todos los campos siguientes son obligatorios y no se admiten campos desconocidos.

```json
{
  "schema_version": 1,
  "device_id": "simulador-p01",
  "asset_id": "lavadora-prueba",
  "sequence": 1,
  "acquired_at": "2026-10-01T12:00:00.000000+00:00",
  "source": "simulated",
  "quality": "synthetic",
  "temperature_c": 31.3,
  "vibration_rms": 0.65,
  "vibration_unit": "m/s²",
  "vibration_method": "synthetic_rms_acceleration",
  "window_s": 1.0
}
```

El registro aceptado añade `received_at`, ISO 8601 UTC asignada al recibir. `id` es la clave interna SQLite y no pertenece al contrato del emisor. La secuencia es entera positiva y se conserva a través de reinicios del simulador consultando el máximo guardado. Cada par dispositivo/origen tiene una restricción de unicidad sobre la secuencia.

| Campo | Definición y validación actual |
| --- | --- |
| schema_version | Entero exactamente 1; `true` no cuenta como entero. |
| device_id / asset_id | Solo `simulador-p01` / `lavadora-prueba` en P01. |
| sequence | Entero 1 a 2^63−1. Sin repetición ni retroceso. |
| acquired_at | ISO 8601 con zona; normalización UTC. Hasta 5 s de adelanto y 10 s de antigüedad. |
| received_at | Añadido por el receptor. Su envío en la entrada se rechaza como campo desconocido. |
| source | El esquema SQLite distingue `simulated` y `real`. Recepción de `real` deshabilitada expresamente. |
| quality | Solo `synthetic` en P01; no representa calidad física de un sensor. |
| temperature_c | Número finito −55 a 125 °C; superficie, sintético. |
| vibration_rms | Número finito 0 a 200 m/s²; indicador de aceleración, sintético. |
| vibration_unit / vibration_method | Exactamente `m/s²` / `synthetic_rms_acceleration`. |
| window_s | Número finito 0,01 a 60 s; ventana nominal ilustrativa. |

Son restricciones del prototipo, no validaciones metrológicas. Los números no aceptan cadenas, booleanos, NaN o infinitos. Primero se valida contenido y antigüedad; después duplicado y orden. Un paquete antiguo repetido puede rechazarse como atrasado antes de comprobar la secuencia. Una secuencia ya almacenada se rechaza como `duplicate`; una secuencia nueva menor que la última aceptada o una adquisición anterior se rechaza como `out_of_order`. La misma hora de adquisición es admisible si la secuencia aumenta. Los rechazos se guardan en `reception_events`; no insertan mediciones ni renuevan la actualidad de la señal.

## Interfaz local de prueba

La recepción central es `Service.receive(packet)`; la usan el simulador y `POST /api/packets`. El punto HTTP es **solo local**, requiere JSON y simulación en ejecución. No representa una conexión implementada con ESP32. Responde 201 al aceptar, 409 al duplicar o salir de orden y 422 ante un paquete inválido, atrasado, futuro o real. El esquema rechazado y su causa aparecen en el registro de recepción. Un cuerpo JSON ilegible se rechaza HTTP 400 antes de llegar al contrato, con registro HTTP en el archivo de operación.

Rutas de la interfaz:

| Ruta | Uso |
| --- | --- |
| GET /api/status | Estado, actualidad, último recibo, reglas, causas y tendencia guardada. |
| POST /api/simulation | `{ "action": "start" }`, `stop`, `normal`, `hot`, `vibration`, `signal_loss`, `recovery`. |
| GET /api/history?from=...&to=... | Intervalo inclusivo de adquisición con fechas ISO 8601 y zona. Predeterminado: últimas 24 h. |
| GET /api/export.csv?from=...&to=... | CSV íntegro del mismo intervalo inclusivo. |
| GET /api/alarms | Alarmas y eventos recientes, incluidos recuperados y reconocidos. |
| POST /api/alarms/{id}/ack | `{ "author": "Operador local" }`; idempotente. |
| POST /api/rules | Todos los campos de reglas; configuración auditada en SQLite. |
| GET /api/interventions | Consulta reciente; sin modificación de entradas. |
| POST /api/interventions | asset_id, intervention_at con zona, author, work_type, observations. recorded_at lo asigna el servidor. |

La aplicación no habilita CORS, no usa transporte externo y valida Host y Origin. No es una API industrial expuesta ni un servicio autenticado para varios usuarios.

## Ausencia, parada y reinicio

La señal se supervisa únicamente cuando la simulación está iniciada. Antes del primer paquete usa el instante de inicio como referencia. Un rechazo no reinicia el plazo. Al vencerlo se activa ausencia y se ocultan lecturas; las duraciones pendientes de alarmas por indicador se reinician. Al detener se suspenden las duraciones y ausencia se cierra con motivo explícito de suspensión. Las causas por indicador permanecen hasta una recuperación basada en nuevos paquetes. Reiniciar no reanuda la simulación ni reutiliza como actual el último valor de la base. El navegador también oculta valores si falla la consulta o vence su vigencia local.

## Sustitución futura por ESP32

Mantener recepción, almacenamiento y reglas separados del transporte. Para datos reales se deberá aprobar una nueva capacidad/versionado que admita dispositivos físicos y calidad de sensor; la actual retorna `real_disabled`. Se necesitan pruebas del firmware, identidad/autenticación, tiempo de adquisición confiable, ventanas y muestreo documentados, extracción de gravedad/filtrado y definición del RMS, calibración y política de reinicios de secuencia (posible identificador de sesión en una versión siguiente). También se deben definir reconexión, paquetes atrasados y cuarentena de calidad deficiente. No basta con cambiar `source` a `real`.

El ESP32 no puede acceder al servidor actual desde Wi-Fi: 127.0.0.1 pertenece al PC. Una etapa futura elegirá un puente local o receptor de red autenticado y acotado, sin abrir automáticamente este servicio. No hay firmware, socket de entrada a la LAN, conexión real, IA ni diagnóstico validado en P01.

## Extensión de perfiles · 0.2.0

El formato v1 y el perfil de lavadora se conservan. En modo `--profile motor-pump --input external`, neiron admite exclusivamente `asset_id=motor-bomba-5hp`, `device_id=esp32-motor-simulado`, `vibration_method=synthetic_vector_rms_1000hz`, origen simulated y calidad synthetic. La validación usa la identidad/método del perfil activo. Una base corresponde a un solo activo; se rechaza reutilizar una base de lavadora para motor.

`GET /api/receiver` devuelve perfil, input_mode, activo/dispositivo/método, enabled y last_sequence para el emisor local. El modo externo empieza con recepción supervisada, sin generar paquetes internos; start/stop activa/suspende recepción. Los escenarios físicos se controlan en el simulador independiente. El origen real permanece deshabilitado. [Contrato y modelo motor](SIMULADOR_MOTOR_BOMBA.md).
