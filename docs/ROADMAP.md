# Recorrido de neiron

**Actualización vigente: 13 de octubre de 2026.** La lavadora será el primer ejemplo físico después de comprar los accesorios. Motor / Lab es el banco virtual complementario para probar la aplicación y compartir ensayos desde un navegador. [Propósito y datos](PROPOSITO_Y_DATOS.md) · [Plan físico](PLAN_LAVADORA_FISICA.md).

## Documentado hasta el 19 de septiembre de 2026

- Definición del prototipo doméstico y selección preliminar de componentes.
- Diseño de gabinete v01, revisión estética v02 y demostración animada v03.
- Separación de cuerpo/tapa y comprobaciones geométricas de STL de prueba.
- Impresión, montaje, estanqueidad y adquisición física pendientes.

## 23 de septiembre de 2026

- Inicio del portafolio público preparado a partir de una selección del proyecto.
- Arquitectura de aplicación local propuesta e integración opcional de MACHINA evaluada documentalmente.
- Sin modelo de IA activado, sin API de pago y sin datos reales de sensores.

## Hitos previstos originalmente · referencia de septiembre de 2026

1. Simulador y panel local: distinguir claramente datos simulados, fallos y ausencia de señal.
2. Persistencia: consultar historial y registrar una intervención en una vista separada.
3. Alarmas: comprobar disparo, recuperación, reconocimiento y persistencia sin IA.
4. ESP32: validar recepción y muestreo; comparar ciclos normales antes de fijar umbrales.
5. Asistente opcional: prueba de MACHINA con documentación del activo y casos conocidos.
6. Validación física: impresión, ajuste, montaje y ensayos antes de nuevas afirmaciones industriales.

Los commits futuros registrarán cambios reales; no se reconstruye un historial Git ficticio de las etapas anteriores.

## 1 de octubre de 2026 · primera versión local 0.1.0

Hitos 1–3 implementados y verificados con simulación: panel local, recepción validada, historial persistente, CSV, formulario de intervenciones y alarmas con recuperación y reconocimiento. Python/SQLite/interfaz web, entorno aislado y lanzadores Windows. 17 pruebas de núcleo/HTTP y recorrido real en Edge con reinicio del proceso; bases temporales. IA desactivada, sin servicios externos y sin publicación ni subida a GitHub. Ver [guía](../software/README.md) y [verificación](../software/VERIFICACION.md).

Siguientes pasos: validar firmware y temporización del ESP32; definir muestreo, filtrado y RMS de aceleración del MPU6050; comprobar temperatura superficial del DS18B20; verificar reloj, identificación y reinicios de secuencia; diseñar transporte autenticado hacia el PC; comparar ciclos físicos normales antes de fijar umbrales. Continúan pendientes impresión, ajuste y montaje del diseño v03. La asistencia opcional se evaluará después, sin condicionar la operación básica.

## 1 de octubre de 2026 · extensión motor–bomba 0.2.0

Simulador local independiente de motor monofásico de 5 HP y bomba centrífuga conectado por HTTP a neiron. Generación continua, física térmica/hidráulica reducida, ventanas triaxiales sintéticas, entorno editable, fallos, señal y persistencia de estado. Lavadora conservada con perfil/base separados. 29 pruebas y recorrido en Edge con reinicios independientes. [Guía](../software/SIMULADOR_MOTOR_BOMBA.md). Pendiente placa del motor concreto, curva de bomba, calibración física e integración ESP32/MPU6050/DS18B20; ninguna nueva afirmación de diagnóstico validado.

## 1–2 de octubre de 2026 · Motor / Lab autónomo 1.0.0

La decisión posterior separa por completo el simulador del paquete neiron para reutilizarlo en otros proyectos. Python propio, SQLite, API genérica, control de condiciones del motor/agua y envío voluntario a otro software. El banco conjunto 0.2 queda como antecedente. El nuevo simulador inicia en 127.0.0.1:8766 sin receptor, con origen `simulated` y salida desactivada al reiniciar. [Guía vigente](MOTOR_LAB.md).

Se corrigió la apertura en Windows con comprobación de disponibilidad, reutilización de instancia y cierre que guarda estado. Posteriormente se mejoraron acabados, motor translúcido, opacidad, vista exterior, acercamiento, piezas seleccionables y detalle de rodamientos. Las ocho causas impuestas se localizan visualmente con calor gradual y vibración amplificada. Geometría supuesta; sin diagnóstico de daños reales.

Motor / Lab: **23 pruebas automáticas + 15 comprobaciones del recorrido completo en Edge + 10 de la vista mecánica** aprobadas. El autor confirmó funcionamiento correcto tras probar todas sus opciones. Publicación de avances preparada con fuentes neiron, capturas de ensayo, distribución descargable de Motor / Lab, arquitectura y [resultados del período](RESULTADOS_2026-10-02.md). El ZIP se genera desde una única carpeta de desarrollo; las bases y entornos no se publican. Se conserva el historial Git real, sin reconstruir commits para fechas pasadas.

## Próxima etapa vigente

Identificación del equipo real, firmware/adquisición ESP32, calibración y comparación de ciclos físicos, transporte validado y ensayos del gabinete. Los hitos de simulación, historial, alarmas e intervenciones ya están disponibles; impresión/montaje, hardware, certificación y diagnóstico industrial siguen pendientes. IA/MACHINA permanece como evaluación opcional futura.

## 13 de octubre de 2026 · Motor / Lab Web 1.1.0

Se adapta Motor / Lab al navegador conservando la vista mecánica y los controles, con física reducida en JavaScript y descarga CSV/JSON por ensayo. Cada pestaña ejecuta una sesión independiente, sin Python, comandos ni dependencia del PC del autor. [Abrir laboratorio](https://neiron-motor-lab.sunsetfly128.chatgpt.site) · [Fuente web](../web/README.md).

La edición web sirve para mostrar el avance y experimentar con datos sintéticos; no crea una base central de visitantes. Retiene hasta 3.600 paquetes en memoria, suspende el avance en pestaña oculta y requiere descargar antes de cerrar/recargar. Las funciones Python/SQLite/REST/SSE se conservan en la entrega local 1.0.0. El modelo web usa las mismas ecuaciones térmicas e hidráulicas, con otro generador de ruido.

Verificación nueva: 16 comprobaciones del modelo, comparación determinista con Python y 12 comprobaciones en Edge, con revisión visual escritorio/móvil. La distribución autónoma Python volvió a pasar sus 23 pruebas. [Detalle y alcance](REVISION_2026-10-13.md).

El autor confirma la lavadora como primer ejemplo físico cuando adquiera los accesorios. Se prepara el plan de hardware, firmware, frecuencia de muestreo, transporte, recepción, trazabilidad y ciclos normales. La documentación relaciona carcasa/animación, neiron y Motor / Lab como laboratorio de desarrollo y pruebas. Firmware y recepción física permanecen pendientes, con criterios de aceptación definidos en el [plan](PLAN_LAVADORA_FISICA.md).
