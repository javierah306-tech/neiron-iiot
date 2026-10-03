# Resultados del proyecto · 2 de octubre de 2026

El proyecto pasó de una demostración de gabinete/sensores a dos aplicaciones locales utilizables: **neiron P01** para monitoreo simulado de lavadora y **Motor / Lab** como banco autónomo motor–bomba. El autor probó todas las opciones del simulador y confirmó funcionamiento correcto. Esa aceptación es funcional; no sustituye ensayos de hardware ni validación de diagnóstico.

## Entregables alcanzados

| Área | Resultado disponible | Evidencia y límite |
| --- | --- | --- |
| Diseño mecánico neiron | Blender v03, escena explicativa y cuerpo/tapa STL separados | Archivos y comprobaciones geométricas en el repositorio. Piezas de prueba; impresión, ajuste, junta y montaje definitivos pendientes. |
| Monitoreo neiron | Lavadora simulada, temperatura y aceleración RMS; estado y última recepción | Aplicación local con origen visible. Sin lectura física de ESP32. |
| Historial neiron | SQLite, consulta por fechas y CSV | Persistencia comprobada tras reinicio; unidades, origen y fechas en exportación. |
| Alarmas neiron | Temperatura, vibración y ausencia; umbrales, histéresis/duración y reconocimiento | Inicio, recuperación y reconocimiento registrados; reconocer no elimina causa ni historial. Umbrales ilustrativos. |
| Intervenciones neiron | Formulario y consulta persistentes | Fecha del trabajo distinta de fecha de registro; entradas inmutables y correcciones por referencia. |
| Simulador autónomo | Motor monofásico 5 HP, acoplamiento y bomba centrífuga de agua limpia | Física térmica/hidráulica reducida; cuatro zonas, once ajustes continuos y escala temporal. Constantes de laboratorio sin calibración. |
| Vista mecánica | Motor translúcido, opacidad, exterior, acercamiento y siete componentes | Rotor/eje/ventilador y bolas animados; detalle de DE/NDE. Geometría supuesta, sin reconstrucción exacta del motor fotografiado. |
| Condiciones de ensayo | Ocho causas adversas, combinables, y recuperación | Lubricación, contaminación, defecto, desalineación, desequilibrio, holgura, ventilación y cavitación. La localización deriva de causas impuestas. |
| Señales y estados | Temperatura superficial, RMS de aceleración, gráficos y ventanas X/Y/Z | 1.000 Hz sintéticos / ventana de 1 s; paquete aproximadamente cada segundo. Sin datos antiguos presentados como actuales. |
| Integración reusable | REST, SSE, CSV y POST local voluntario con contrato versionado | Receptor de ejemplo validado con paquetes inválidos/duplicados; salida desactivada al reiniciar. Firmware físico pendiente. |
| Uso en Windows | Entornos aislados, inicio/cierre y datos fuera del código | Loopback 127.0.0.1; sin servicios externos, paquetes de terceros ni IA. |

## Verificaciones ejecutadas

- **Motor / Lab: 23 pruebas automáticas aprobadas**, con bases temporales: física reducida, balance térmico, RMS/DC, contrato, secuencias, persistencia, pausa/ausencia, HTTP, CSV, SSE y lanzador.
- **15 comprobaciones en Edge del recorrido completo**: controles, calor/vibración, recuperación, agua/NPSH, pérdida de señal, pausa/apagado, receptor optativo, inválidos/duplicados, CSV y reinicio. Copia autónoma iniciada sin neiron.
- **10 comprobaciones en Edge de la vista mecánica**: capas, giro, piezas, teclado, opacidad, ocho causas localizadas, calor, señal perdida, recuperación, movimiento reducido y 390 px sin desbordamiento. Cero errores JavaScript y cero solicitudes externas observadas.
- **Neiron y su banco histórico: 29 pruebas de núcleo/integración aprobadas** en la verificación de publicación. Los 17 casos originales de lavadora son parte de ese conjunto; no se suman nuevamente.
- Recorridos históricos de neiron en Edge: cuatro vistas, reconocimiento/recuperación de alarmas, intervención, CSV y persistencia tras reinicio; documentados en [VERIFICACION.md](../software/VERIFICACION.md).
- **Revisión del autor:** confirmación de que todas las opciones del simulador funcionan correctamente en su PC, al cierre de esta etapa.

Las 25 comprobaciones de navegador son pasos de integración, no 25 pruebas unitarias adicionales. Los conjuntos de 23 y 29 pertenecen a aplicaciones/fases diferentes; sus tamaños no constituyen una tasa de precisión ni validación industrial. Ver [resumen publicable de evidencia](evidencia/motor-lab-verificacion.json). Las capturas proceden de bases temporales con señales ficticias; bases, registros y rutas personales de ejecución quedan fuera de la entrega.

La entrega descargable se comprobó después de extraerla: **31 archivos, inventario SHA-256 válido y 23 pruebas aprobadas desde el ZIP**. Dos empaquetados produjeron el mismo SHA-256. Se verificaron exclusiones de bases/entornos/registros y enlaces locales de README/documentación. Esta repetición verifica la distribución; no suma otros 23 casos distintos.

## Comportamiento obtenido en el laboratorio

El arranque y la temperatura evolucionan de forma gradual. Las condiciones adversas elevan el RMS y/o el calor de acuerdo con el modelo, con mayor respuesta de desalineación junto a DE/acoplamiento. Normal reduce pronto la vibración y conserva la inercia térmica. NPSH bajo modifica caudal y ruido de la bomba; contaminación del lubricante no convierte el agua en agua contaminada.

Se comprobó que pausar, perder señal o cerrar el servicio impide presentar el último paquete como una lectura actual. Al restaurar señal se exige una adquisición nueva. Al reiniciar se conservan historial, secuencia y estado físico, mientras el envío externo vuelve desactivado. El programa puede funcionar solo y conectarse más adelante a un receptor elegido por el usuario.

## Próximos resultados por demostrar

1. Identificar placa del motor, rodamientos, curva de bomba, montaje, régimen eléctrico y puntos de sensor reales.
2. Implementar firmware ESP32, adquirir MPU6050/DS18B20 y comprobar frecuencia de muestreo, filtros, unidades, reloj y calidad.
3. Validar transporte hacia el PC, identidad/secuencias y reconexión; cualquier acceso de red requerirá una etapa propia.
4. Comparar ensayos físicos normales y anomalías controladas para calibrar coeficientes, geometría y umbrales.
5. Imprimir y ensayar cuerpo/tapa, ajuste, entradas, fijación y sellado del gabinete v03.

La IA/MACHINA sigue en evaluación documental, sin instalar ni activar. No se han demostrado predicción de fallas, vida útil, identificación de pista dañada, protección IP ni cumplimiento industrial certificado. Tampoco se realizaron pruebas de semanas de duración ni en todos los navegadores.
