# Verificación ejecutada · 1 de octubre de 2026

Entorno: Windows, CPython 3.12.14 dentro de `.venv`, SQLite 3.53.1, Edge en modo headless y Playwright disponible en las herramientas locales de desarrollo. Sin datos reales y con IA desactivada. Las pruebas usaron bases temporales separadas de la carpeta de datos del usuario.

## Núcleo y HTTP

Comando: `.venv\Scripts\python.exe -m unittest discover -s tests -v`.

**17 pruebas aprobadas.** Incluyen estado normal/detenido; duración mínima; histéresis ante oscilaciones; temperatura/vibración; inicio, reconocimiento idempotente y recuperación persistentes; ausencia desde inicio y tras pérdida; suspensión explícita; interrupción de duración por pérdida; persistencia de mediciones, secuencia, reglas e intervenciones al reabrir la base; fechas distintas de trabajo/registro; intervalos; valores no finitos, booleanos, campos adicionales, fecha sin zona, real deshabilitado, futuro, atraso, duplicados y fuera de orden; continuidad de simulación tras rechazos; CSV con UTC, unidades y origen; recursos locales, API, controles y rechazo de Host/Origin externos.

## Servicio iniciado y recorrido en navegador

`tests/browser_smoke.cjs` inicia un **proceso real** de `python -m neiron.server`, en un puerto libre de 127.0.0.1 y una base temporal, y recorre la aplicación en Edge:

- Inicio detenido y marca permanente DATOS SIMULADOS.
- Iniciar, valores y gráficos visibles; operación normal.
- Temperatura elevada, reconocimiento conservando causa activa y modificación de reglas.
- Recuperación, vibración elevada y recuperación.
- Pérdida de señal: alarma, ambas lecturas ocultas y recuperación.
- Registrar intervención desde el formulario separado y consultar sus dos fechas.
- Consultar fechas en Historial y descargar CSV con método, unidades y origen.
- Detener, cerrar el proceso y comprobar la pantalla sin lecturas actuales.
- Reiniciar el proceso: persisten mediciones, intervención, reglas y eventos; inicia detenido.
- Pantalla de 390 px: navegación visible y sin desbordamiento horizontal.
- Sin excepciones JavaScript y sin solicitudes fuera de 127.0.0.1; las rutas externas se bloquean en el navegador de prueba.

Se inspeccionaron visualmente las capturas de las cuatro vistas y la vista móvil. Las capturas, exportación, registro de consola e informe JSON se guardan en `software/.test-artifacts/`, excluida de Git. La limpieza de SQLite temporal puede necesitar un segundo intento en Windows si hay archivos bloqueados; no modifica la base operativa del usuario.

Para repetir la prueba opcional, se necesita Node, Playwright y Edge. La aplicación no necesita estas herramientas. Si Playwright está disponible como módulo habitual, ejecuta `node tests/browser_smoke.cjs`. Para el entorno de desarrollo usado aquí:

```powershell
$env:NEIRON_PLAYWRIGHT_MODULE = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright"
node tests/browser_smoke.cjs
```

El navegador de prueba usa la ubicación estándar de Edge indicada en ese archivo; adapta el ejecutable si tu instalación difiere. No incorpora Playwright como dependencia del producto ni lo descarga.

## Límites de lo comprobado

No se hicieron pruebas con ESP32, MPU6050, DS18B20, firmware, muestreo físico, calibración o enlace Wi-Fi. No se validaron umbrales físicos, IP, diagnósticos ni IA. No se desconectó físicamente internet del PC: se verificó que la interfaz utiliza recursos locales y no realiza solicitudes externas, con bloqueo de estas rutas en el navegador. El instalador y la aplicación no descargan paquetes. No se ha hecho una prueba de resistencia de varios días ni una auditoría industrial de seguridad. No se publicó ni se subió contenido a GitHub.

También se ejecutó `INICIAR_NEIRON.bat` desde la raíz, con datos de prueba separados, y se verificó respuesta HTTP 200 en 127.0.0.1:8765. El servicio de prueba se cerró al completar la revisión. La carpeta predeterminada del usuario no se utilizó para las pruebas.

## Extensión motor–bomba 0.2.0

29 pruebas aprobadas (17 originales + 12 motor). `tests/browser_motor.cjs` recorre dos procesos reales, modelo continuo, controles, recepción HTTP, alarmas, ausencia, CSV, intervención y reinicios de ambos servicios. Incluye recuperación del emisor con receptor cerrado, preservación de estado/secuencia y pantalla de 390 px. Sin errores JavaScript ni peticiones fuera de los dos servicios locales. [Detalle, límites y comandos](SIMULADOR_MOTOR_BOMBA.md). Capturas e informe en `.test-artifacts/motor/`. Datos temporales, ninguna base operativa del usuario empleada.
