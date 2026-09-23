# Evaluación de MACHINA — 23 de septiembre de 2026

Decisión propuesta: candidato para una capa opcional de asistencia de mantenimiento. No instalar ni activar modelos/API en esta etapa. Evaluación documental, no validación de funcionamiento, seguridad ni precisión con nuestros datos.

## Qué aporta y qué falta

[MACHINA](https://github.com/LGDiMaggio/machina) organiza agentes, conectores y entidades de mantenimiento. Su documentación presenta consulta de manuales, historial y flujos de trabajo. Necesita un proveedor LLM: ofrece ejemplos con Ollama local o API externas. No equivale a un modelo previamente entrenado y validado para nuestra lavadora. Sus demostraciones utilizan información de muestra y no prueban conocimiento universal ni ausencia de errores.

La detección de anomalías y la estimación de vida remanente aparecen en la hoja de ruta; no las damos por resueltas para neiron. [Fuente: README del autor](https://github.com/LGDiMaggio/machina#readme).

El [paquete](https://github.com/LGDiMaggio/machina/blob/main/pyproject.toml) declara Python >=3.11, versión 0.3.0 y madurez prealfa. Mantendremos un entorno separado y fijaremos versión/commit y dependencias después de una prueba reproducible. La instalación completa incluye extensiones que nuestro prototipo no necesita.

## Integración propuesta, aún no implementada

1. neiron recibe, valida y almacena telemetría; calcula indicadores y alarmas por reglas configurables.
2. Un adaptador reúne ventanas de indicadores, calidad de datos, estado de la máquina, alarmas y reportes confirmados por el operador.
3. MACHINA consulta ese contexto y documentación autorizada; devuelve una explicación y sugerencias con referencias.
4. La interfaz muestra la respuesta como asistencia, con evidencia y limitaciones. El operador confirma cualquier intervención o cambio de registro.

No enviar cada muestra al LLM. No permitir que el agente cambie umbrales, borre historial o actúe sobre la máquina. Los fallos, demoras y desconexión del servicio de IA no deben interrumpir las alarmas locales. No habilitar canales de correo, Telegram ni mensajería: las señales se muestran dentro de la app.

## Coste y despliegue

El framework tiene [licencia Apache 2.0](https://github.com/LGDiMaggio/machina/blob/main/LICENSE). Eso no elimina el coste de cómputo, operación ni de un proveedor externo. Un modelo local necesita recursos y evaluación; una futura instalación centralizada podría atender PCs ligeros. La elección del modelo y su propia licencia se revisará al integrar.

No es necesario un fork para utilizarlo como dependencia. Un fork tendría sentido si modificamos el framework; conservaría su atribución y licencia. Este portafolio no incorpora código de MACHINA. Antes de distribuir una integración se revisarán las obligaciones y avisos de todas las dependencias.

## Condiciones para aceptar una integración

- Pruebas con respuestas conocidas y referencias a documentos/reportes reales autorizados.
- Respuesta explícita cuando falta evidencia; ninguna promesa de diagnóstico infalible.
- Operación del monitoreo con IA apagada, lenta o fallando.
- Versiones fijadas, coste/latencia medidos y control del destino de los datos.
- Confirmación humana de propuestas y registro de qué contexto/modelo produjo cada respuesta.
