> **Antecedente 0.2, reemplazado como simulador principal.** La decisión vigente es Motor / Lab autónomo, con [guía y entrega actuales](../docs/MOTOR_LAB.md). En el proyecto original se desarrolla en `07_SIMULADOR_MOTOR_BOMBA`; en este portafolio se descarga como ZIP y se inicia con su propio `iniciar.bat`, sin neiron y con salida desactivada. Las instrucciones de inicio conjunto de este documento describen la entrega anterior; sus fuentes se conservan para trazabilidad.

# Banco virtual motor–bomba · neiron 0.2.0

Extensión local del 1 de octubre de 2026. **Datos ficticios continuos, no mediciones reales.** El simulador dibuja un motor azul inspirado en la imagen aportada, un acoplamiento protegido, una bomba centrífuga, tuberías, válvula y depósito de recirculación. Una imagen sin placa legible no identifica el fabricante, velocidad ni rendimiento de ese motor concreto.

## Abrir ambas aplicaciones

Cierra la consola del P01 anterior si ocupa el puerto 8765. Haz doble clic en **`INICIAR_MOTOR_BOMBA.bat`**, en la carpeta principal del proyecto. Si falta `.venv`, prepara el mismo entorno aislado ya utilizado por neiron; no descarga paquetes.

Abre dos direcciones distintas:

| Aplicación | Dirección | Función |
| --- | --- | --- |
| Simulador motor–bomba | http://127.0.0.1:8766 | Genera los dos indicadores, ilustra la planta y controla condiciones físicas. |
| neiron receptor | http://127.0.0.1:8765 | Valida, guarda, grafica, exporta y aplica alarmas/intervenciones al perfil motor. |

El motor y la generación comienzan automáticamente. La recepción está activada por defecto en este perfil. «Conectado» en el simulador significa que **neiron confirmó un paquete por HTTP y lo guardó**, no que exista un ESP32 físico conectado. Cada generación produce aproximadamente un paquete por segundo de reloj del PC; las pantallas solo consultan el estado. Cerrar las pestañas no detiene los servicios. **Ctrl+C en la consola del banco cierra ambos.** Si un servicio termina inesperadamente, el lanzador conjunto también cierra el otro para evitar procesos abandonados.

La lavadora original sigue disponible con `INICIAR_NEIRON.bat` y conserva su base e instrucciones. Los dos perfiles no comparten la base de datos. No ejecutes los dos receptores en el mismo puerto. El lanzador detecta puertos ocupados y solicita cerrar la instancia anterior; no mata procesos existentes.

## Recorrido recomendado

1. Comprueba «Conectado» en el simulador y «Motor 5 HP · bomba de agua» en neiron. Los valores llegan por el emisor HTTP; neiron no genera datos internos en este modo.
2. Deja **1×** para evolución normal. Para ver el calentamiento en menos tiempo, selecciona **60×** y pulsa **Aplicar entorno**. La banda «ACELERADO» permanece visible. La temperatura mantiene su valor al cambiar la escala y evoluciona gradualmente.
3. Prueba **Desalineación simulada**. Se eleva la componente 2× de vibración; neiron activa su regla ilustrativa de 3 m/s² tras sostenerla durante 3 s. Reconoce la alarma en neiron: su causa permanece activa. **Recuperación normal** devuelve las amplitudes normales y recupera tras histéresis/duración.
4. Prueba **Cavitación simulada**. Se inyectan ruido y una reducción de caudal/altura; puede activar la misma regla de vibración. Es una condición elegida por el operador, no una conclusión inferida por neiron a partir del RMS.
5. Prueba **Refrigeración reducida** con 60×. Disminuye disipación; el calentamiento tarda decenas de segundos de reloj, dependiendo de la temperatura inicial, ambiente y válvula. No salta instantáneamente a una cifra alta. La alarma térmica inicial de motor es 75 °C; recuperar condiciones normales tampoco enfría instantáneamente.
6. Prueba **Pérdida de señal**. El motor virtual sigue evolucionando, pero no hay paquetes para enviar. Tras 5 s, neiron activa ausencia y oculta temperatura/vibración actuales. **Recuperación normal** vuelve a emitir lecturas recientes.
7. **Apagar motor** mantiene adquisición y envío: las rpm/vibración bajan y la temperatura se enfría lentamente. **Pausar simulación** congela la evolución y corta paquetes; **Reanudar** retoma el estado. **Desconectar envío** deja el modelo en marcha e interrumpe solo HTTP; **Conectar envío** reanuda con paquetes nuevos.
8. Ajusta ambiente o válvula y compara el contexto físico calculado. Más restricción reduce el caudal de esta bomba; no se fuerza artificialmente una sobrecarga al cerrar la válvula.
9. En neiron prueba Historial/CSV e Intervenciones: el activo será el motor, con sus registros y alarmas independientes de la lavadora.

## Referencia adoptada y supuestos

Referencia eléctrica de catálogo: **5 HP / 3,7 kW redondeados, monofásico CSR, 230 V, 50 Hz, 2 polos, 2.910 rpm nominales, rendimiento 85%**. Valores tomados como referencia del [catálogo WEG W22 monofásico, tabla de dos polos](https://static.weg.net/medias/downloadcenter/h52/h99/WEG-w22-single-phase-european-market-50069268-brochure-english-web.pdf). No se afirma que el motor de la imagen sea ese producto. La velocidad calculada varía ligeramente por deslizamiento/carga y queda por debajo de la síncrona de 3.000 rpm.

Supuestos propios del banco: bomba centrífuga de agua, punto de referencia 18 m³/h y 45 m, eficiencia 64%, seis álabes, acoplamiento directo y circuito de recirculación sin altura estática entre depósitos. La altura es carga hidráulica/pérdidas de circuito; no representa una elevación geométrica de 45 m en el dibujo. Temperatura ambiente inicial 22 °C, bajo techo. No hay dimensionamiento de tubería, NPSH, curva comercial ni instalación real validada.

Se intersectan curvas reducidas de bomba y sistema:

- `H_bomba = 65·r² − 20·(Q/18)²`, en metros, con `r = rpm/2910` y Q en m³/h.
- `H_sistema = 45·(Q/18)² / apertura²`; apertura es un coeficiente relativo de resistencia, no una calibración exacta de una válvula física.
- `P_agua = ρ·g·Q·H`, Q convertido a m³/s; potencia de eje = potencia de agua / eficiencia más pérdidas mecánicas ilustrativas.

La relación entre curva de bomba, eficiencia, potencia y velocidad se basa en los [fundamentos del Hydraulic Institute](https://datatool.pumps.org/pump-fundamentals/pump-curves.html). Las curvas numéricas y pérdidas del banco son hipótesis propias. A plena operación inicial el cálculo se estabiliza cerca de 18 m³/h, 45 m y 97% de la potencia nominal de eje; estos son resultados del modelo, no mediciones de una bomba real.

Modelo térmico: `C·dT/dt = pérdidas − G·(T−ambiente)`, capacidad efectiva de 16.000 J/K y resistencia térmica base de 0,055 K/W. Las pérdidas a carga nominal concuerdan con el rendimiento eléctrico de referencia; al apagar el ventilador se supone una conductancia menor. La refrigeración reducida usa el 42% de la disipación normal. El contacto del sensor añade un retardo supuesto de 8 s. La carcasa se calienta/enfría gradualmente; estos coeficientes requieren identificación experimental con el motor físico. No se interpreta temperatura superficial como temperatura de devanado o clase de aislamiento.

## Dos canales emulados y contrato

**Temperatura superficial:** emulación de DS18B20 a 12 bits, con ruido ilustrativo pequeño y cuantización de 0,0625 °C. Esta resolución figura en la [hoja de datos DS18B20](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf). No se simula exactamente el protocolo 1-Wire, su tiempo de conversión, tolerancia ni errores de contacto. Si el modelo supera su rango, el valor se limita a 125 °C y la pantalla del simulador avisa de saturación.

**Vibración:** ventana sintética de 1.000 muestras por eje a 1.000 Hz durante 1 s. Componentes 1× giro, 2× giro, 100 Hz eléctricos, seis veces giro por álabes y ruido. Se retira la media de cada eje y se calcula `√media(ax²+ay²+az²)`, en **m/s²**. La vista de forma de onda solo muestra los primeros 120 ms; el RMS usa las 1.000 muestras. Este muestreo sintético es independiente del paquete HTTP por segundo. El [datasheet MPU-6000/6050](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf) es referencia futura; aquí no se configura ni captura un MPU6050 real. No se calcula velocidad en mm/s ni diagnóstico de rodamientos.

La escala temporal acelera el estado físico entre paquetes. Las ventanas de aceleración son aproximaciones cuasiestacionarias en el estado calculado al final del paso. Las marcas `acquired_at` y `received_at` siguen siendo instantes UTC **del PC**, no el tiempo físico acelerado. `elapsed_s` y `time_scale` aparecen en el simulador y su archivo de estado. Las alarmas de neiron usan segundos de recepción reales; no se acelera su duración mínima. Cambios de escenario/entorno se auditan en `eventos_simulador.jsonl`, con hora UTC y tiempo del modelo.

Se conserva el formato de contrato v1 con estos valores del perfil:

```json
{
  "schema_version": 1,
  "device_id": "esp32-motor-simulado",
  "asset_id": "motor-bomba-5hp",
  "sequence": 123,
  "acquired_at": "2026-10-01T12:00:00.000000+00:00",
  "source": "simulated",
  "quality": "synthetic",
  "temperature_c": 54.0625,
  "vibration_rms": 0.7614,
  "vibration_unit": "m/s²",
  "vibration_method": "synthetic_vector_rms_1000hz",
  "window_s": 1.0
}
```

Los únicos valores de sensores son `temperature_c` y `vibration_rms`. Rpm, caudal, altura, carga y forma de onda son contexto interno ficticio del simulador, no canales medidos ni enviados a neiron. El receptor asigna `received_at` y valida los mismos campos y límites; real sigue deshabilitado. Los valores numéricos se guardan sin modificarlos; la pantalla los redondea para lectura y CSV conserva la precisión del paquete.

`GET /api/receiver` permite comprobar perfil/modo/identidad y última secuencia. El emisor consulta exclusivamente 127.0.0.1, no usa proxies ni sigue redirecciones, verifica motor/recepción externa y después envía a `POST /api/packets`. La conexión ocurre desde Python, no como petición cruzada del navegador. Cada página conserva su protección de origen y no se abre CORS.

La secuencia persiste en el simulador y se sincroniza contra el máximo guardado en neiron al reconectar. No hay cola de paquetes durante una interrupción: se descartan los antiguos y se envía el siguiente actual. Una consulta fallida, perfil incorrecto, suspensión o rechazo tiene un estado visible. Pausar/desconectar/pérdida de señal no recupera por sí sola causas térmicas o de vibración en neiron.

## Ubicación de archivos de operación

- Receptor de lavadora original: `%LOCALAPPDATA%\neiron\prototipo-01` (conservado).
- Receptor motor: `%LOCALAPPDATA%\neiron\motor-bomba\neiron.sqlite3`, auxiliares SQLite y `operacion.log`.
- Simulador: `%LOCALAPPDATA%\neiron\simulador-motor\simulador_estado.json`, `eventos_simulador.jsonl` y `simulador.log`.

El estado guarda secuencia, temperatura, tiempo físico, velocidad, fase y parámetros. Al reiniciar el simulador continúa desde ese estado; el tiempo cerrado no se considera tiempo simulado ni enfriamiento real. La adquisición se reanuda, con los escenarios/motor guardados. Las estadísticas de entregas de la pantalla son de la sesión actual. El historial persistente está en neiron.

Se mantienen fuera de la selección publicable y de OneDrive. No hay nuevas dependencias: CPython 3.12.14, SQLite estándar y recursos HTML/CSS/JavaScript/SVG propios. No se instala IA, MACHINA, nube, Docker ni firmware. El código principal sigue en una sola carpeta `software/`.

## Ejecutar servicios por separado y editar

Desde `software`, `iniciar_simulador_motor.bat` abre solo 8766 y `iniciar_receptor_motor.bat` abre solo neiron con perfil motor en 8765. También puedes usar:

```powershell
.\.venv\Scripts\python.exe -m neiron.server --profile motor-pump --input external --port 8765
.\.venv\Scripts\python.exe -m neiron.motor_server --port 8766 --receiver-port 8765
```

Para otras direcciones locales, usa `iniciar_banco_motor.bat --receiver-port 8775 --simulator-port 8776`; ambas páginas actualizan sus enlaces. El host sigue siendo 127.0.0.1, sin acceso LAN. Para pruebas, `--data-dir C:\ruta\temporal\banco` en el lanzador crea `receiver` y `simulator` bajo esa raíz. Esa opción evita tocar las bases del usuario. Una base de otro activo se rechaza, no se reutiliza ni migra silenciosamente.

Módulos nuevos: `motor_model.py` para fórmulas/amplitudes, `motor_engine.py` para evolución/estado/control, `motor_transport.py` para entrega y reconexión, `motor_server.py` para HTTP, `motor_lab.py` para inicio conjunto y `motor_static/` para interfaz. `profiles.py` declara las identidades y umbrales iniciales ilustrativos. Los coeficientes del modelo se editan en Python, el entorno se ajusta en pantalla. Mantén consistentes fórmulas, parámetros y documentación al cambiar la referencia física.

## Validación y siguiente etapa

Se aprobaron **29 pruebas de Python**: 17 anteriores y 12 nuevas, con bases temporales. Las nuevas comprueban balance térmico/hidráulico, continuidad, enfriamiento, apertura de válvula, condiciones inyectadas, RMS analítico y rechazo DC, cuantización, contrato, recepción por HTTP, identidad de los valores enviados/guardados, pérdida/recuperación, secuencia, persistencia, aislamiento de activos y protección de origen.

Se inició cada servicio como proceso real y se recorrieron ambas pantallas en Edge: recepción, cambio de válvula/60×, fallos de vibración y térmico, reconocimiento/recuperación, pérdida, apagar/pausar/desconectar/reanudar, intervención, historial/CSV y reinicios independientes. La simulación siguió funcionando al cerrar neiron, que recuperó datos frescos al reiniciar. El simulador conservó estado/secuencia al reiniciar. Se revisó la pantalla de 390 px sin desbordamiento y no se detectaron errores JavaScript ni peticiones externas. Capturas e informe quedan en `.test-artifacts/motor/`, excluida de Git.

Para repetir: `probar.bat` o `python -m unittest discover -s tests -v` usando `.venv`. Prueba de desarrollo en navegador: `node tests/browser_motor.cjs`, con Playwright y Edge disponibles; no son dependencias del producto. No se desconectó físicamente internet del PC: se bloquearon rutas externas en la prueba y se comprobó que todos los recursos/peticiones fueron locales. No se validaron sensores, montaje, ruido metrológico, umbrales industriales ni ensayos de larga duración.

Para concordar con **el motor físico concreto** faltan placa, curva de bomba y mediciones de ciclos reales, ambiente y fijación de sensores. Después se podrán identificar pérdidas/inercia térmica y niveles de vibración, escribir firmware y validar muestreo/transporte. Esta entrega comprueba el funcionamiento de neiron con datos ficticios plausibles, no certifica el comportamiento de la máquina de la foto.

Se verificó también el archivo `INICIAR_MOTOR_BOMBA.bat` de la raíz en los puertos predeterminados: simulador conectado, paquete confirmado y lectura del mismo dispositivo/secuencia en neiron. Se cerraron las instancias de prueba; el primer inicio del usuario empleará las carpetas predeterminadas documentadas. El recorrido de la lavadora se repitió en Edge después de la extensión y volvió a pasar.
