# neiron P01 · software local 0.2.0

Entrega del 1 de octubre de 2026. Perfiles de **Lavadora de prueba** y **Motor 5 HP · bomba de agua**, exclusivamente con **DATOS SIMULADOS**. Hardware sin conectar e IA desactivada. No instala MACHINA, modelos, servicios de nube ni paquetes externos.

## Nuevo banco motor–bomba

Decisión vigente: **Motor / Lab 1.0.0** es autónomo, con entorno propio y envío opcional desactivado. [Guía y entrega descargable del simulador actual](../docs/MOTOR_LAB.md). Extrae su ZIP y abre el `iniciar.bat` incluido. El código principal de desarrollo permanece en `07_SIMULADOR_MOTOR_BOMBA` del proyecto original; los iniciadores de esta carpeta pertenecen al banco conjunto 0.2 conservado como [antecedente](SIMULADOR_MOTOR_BOMBA.md). Neiron no es una dependencia del simulador vigente.

## Abrir lavadora original en Windows

1. En la carpeta principal del proyecto, abre `INICIAR_NEIRON.bat`. También puedes abrir `software/iniciar.bat` dentro del portafolio.
2. La primera ejecución crea `software/.venv`, un entorno Python aislado. No descarga dependencias ni modifica la configuración global. Se usa Python 3.12 instalado para el usuario, o el runtime de Python existente en Codex como alternativa.
3. Se abre el navegador en **http://127.0.0.1:8765**. Si no aparece, abre esa dirección manualmente. Mantén abierta la ventana de consola.
4. Pulsa **Iniciar** en Monitoreo. La aplicación empieza siempre con la simulación detenida.
5. Para cerrar, pulsa **Ctrl+C** en la consola. Cerrar la pestaña del navegador no detiene el servicio. «Detener» detiene solo la simulación.

Referencia verificada: **CPython 3.12.14 Windows x64 / SQLite 3.53.1**. `runtime.txt` registra las versiones y `requirements.txt` registra que no hay paquetes externos. Otras revisiones 3.12 pueden ejecutar el programa, pero la verificación de esta entrega corresponde a la indicada. Si no existe Python 3.12, el instalador explica el requisito; no instala Python en el sistema. Una vez disponible Python, tanto la preparación del entorno como la operación funcionan sin internet. Node, Playwright y Edge automatizado se utilizaron para desarrollo; no son requisitos de uso.

## Probar los escenarios

Los controles están en Monitoreo y el escenario seleccionado queda visible. Se puede seleccionarlo antes o después de iniciar.

| Control | Resultado esperado con reglas iniciales |
| --- | --- |
| Operación normal | Temperatura alrededor de 31 °C y RMS alrededor de 0,6 m/s². Estado normal. |
| Temperatura elevada | Alrededor de 54 °C. Alarma tras aproximadamente 4 paquetes: duración mínima de 3 s desde el primero alto. |
| Vibración elevada | Alrededor de 3,5 m/s². Alarma después de sostener el umbral durante 3 s. |
| Pérdida de señal | Deja de emitir paquetes. A los 5 s desde la última recepción válida, desaparecen los valores actuales y aparece la alarma de ausencia. |
| Recuperación normal | Vuelven los valores normales. Temperatura y vibración recuperan tras 3 s bajo el umbral menos histéresis; ausencia de señal recupera con el primer paquete válido. |
| Detener | Valores actuales ocultos inmediatamente. Se conserva la fecha de última recepción y el historial. Suspende la supervisión de ausencia; registra ese motivo, sin afirmar recuperación física. |

La vibración es **RMS de aceleración sintético en m/s²**, con método `synthetic_rms_acceleration` y ventana nominal de 1 s. Se genera el indicador directamente: no hay muestras crudas ni cálculo real de RMS. Un paquete por segundo no equivale a muestrear vibración a 1 Hz. No representa velocidad en mm/s, diagnóstico de rodamientos, predicción de fallas ni vida útil.

En **Alarmas**, prueba reconocer una alarma mientras su escenario sigue elevado: la causa continúa activa. El reconocimiento registra autor y hora; no elimina eventos. Los umbrales iniciales ilustrativos son 45 °C / 2 m/s², con histéresis de 3 °C / 0,3 m/s², duración mínima de 3 s y ausencia de 5 s. Guardar nuevas reglas conserva las alarmas existentes y reinicia las duraciones pendientes. Para recuperar una alarma por umbral necesita paquetes válidos bajo el nivel de recuperación, incluso después de reiniciar.

En **Historial**, consulta un intervalo y exporta CSV. La tabla muestra hasta 2.000 mediciones recientes; el CSV incluye **todas** las del intervalo, ordenadas por adquisición. Separador `;`, codificación UTF-8 con BOM para Excel, fechas ISO 8601 UTC con zona, unidades, origen y método. En Excel usa importación de texto UTF-8 con separador punto y coma si no reconoce el formato automáticamente. La base no tiene borrado automático de mediciones.

En **Intervenciones**, registra activo, fecha del trabajo, autor, tipo y observaciones. La fecha de registro la asigna el servidor al guardar. Las entradas son inmutables. Una corrección se registra como una nueva entrada «Corrección de registro», citando el ID original en observaciones; ambas se conservan. No hay edición, borrado ni adjuntos en esta versión. La vista muestra las últimas 1.000 entradas; la base conserva todas. Alarmas muestra las últimas 500 alarmas y los últimos 2.000 eventos; tampoco se borra el historial completo.

## Datos y fechas

Por defecto: **`%LOCALAPPDATA%\neiron\prototipo-01`**, en los datos locales del usuario de Windows y fuera del repositorio.

- `neiron.sqlite3`: mediciones, activo, alarmas, eventos, configuración e intervenciones.
- `neiron.sqlite3-wal` y `neiron.sqlite3-shm`: archivos auxiliares mientras SQLite está abierta.
- `operacion.log` y sus rotaciones: incidencias del servicio, sin contenido de formularios.

Esta ubicación queda fuera del repositorio y de OneDrive. Los archivos de operación, bases, entornos y capturas de prueba además están excluidos en `.gitignore`. El código principal tiene una única ubicación: `06_PORTAFOLIO_GITHUB/neiron-iiot/software`. Los modelos y respaldos existentes se conservaron.

La base almacena instantes normalizados con zona UTC. La interfaz muestra **America/Santiago**, independientemente de la zona del PC. Los formularios convierten desde esa zona mediante `Intl` del navegador. Las horas inexistentes o ambiguas durante cambios de horario se rechazan con explicación; elige una hora fuera del cambio. Mantén correcta la hora del PC: emisor y receptor usan ese reloj en la simulación.

Para una copia segura, cierra el servicio con Ctrl+C y copia la carpeta de datos completa. No copies solamente el archivo principal mientras el servicio está escribiendo. No se ha configurado ni verificado respaldo automático o sincronización.

## Ejecución manual y desarrollo

Desde `software`:

```powershell
.\instalar.bat
.\.venv\Scripts\python.exe -m neiron.server --open-browser
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No necesitas activar el entorno. Si 8765 está ocupado, cierra la otra instancia o inicia con `iniciar.bat --port 8766`, y abre `http://127.0.0.1:8766`. Ejecuta una sola instancia por carpeta de datos. Para pruebas aisladas puedes indicar `--data-dir C:\ruta\temporal\neiron`; esa opción tiene prioridad sobre `NEIRON_DATA_DIR`, que a su vez tiene prioridad sobre la carpeta predeterminada. Usa carpetas fuera de la selección de publicación. El servicio no tiene opción para escuchar en la red: se enlaza siempre a 127.0.0.1. La API rechaza orígenes y cabeceras Host externos.

`probar.bat` ejecuta las pruebas de Python con bases temporales y conserva abierta la consola al terminar. Para la prueba opcional de navegador consulta [VERIFICACION.md](VERIFICACION.md). No hace falta ejecutar pruebas para utilizar la aplicación.

## Módulos

- `simulator.py`: único generador sintético, emite aproximadamente cada segundo.
- `contract.py`: valida versión, campos, valores, fechas, origen y calidad.
- `storage.py`: esquema SQLite y persistencia.
- `alarms.py`: reglas, duración mínima, histéresis y eventos.
- `service.py`: recepción y coordinación, con acceso serializado a SQLite.
- `server.py`: servicio HTTP local y CSV.
- `static/`: cuatro vistas, navegación, estilos y gráficos Canvas propios; fuentes de sistema e iconos de texto, sin CDN.

La aplicación ofrece estados vacíos y errores; no trata valores antiguos como actuales. Tras detener, reiniciar, vencer el plazo o perder conexión del navegador, los indicadores actuales muestran «—». Los gráficos son explícitamente historial y pueden conservar valores anteriores. Las causas de temperatura/vibración no desaparecen por detener el simulador.

## Límites y siguiente etapa

Implementado y probado: simulación, recepción validada, historial persistente, CSV, alarmas locales, reconocimiento y registro de intervenciones. No hay sistema multiusuario, autenticación industrial, retención configurable, adjuntos, análisis predictivo ni IA.

Pendiente ESP32 de 30 pines, MPU6050 y DS18B20: firmware, frecuencia de muestreo y filtrado, cálculo RMS físico, fijación y calibración, sincronización horaria, secuencias tras reinicio, autenticación del enlace y pruebas de datos reales. [CONTRATO_DATOS.md](CONTRATO_DATOS.md) define la interfaz futura y sus límites. El transporte de red se deberá diseñar por separado; el servidor actual permanece exclusivamente local.
