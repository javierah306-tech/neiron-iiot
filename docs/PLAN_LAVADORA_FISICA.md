# Plan preparado · primer ejemplo físico: lavadora

Decisión confirmada por el autor el 13 de octubre de 2026: **la lavadora será el primer ensayo físico una vez comprados los accesorios**. Motor / Lab se mantiene como laboratorio virtual complementario para pruebas de aplicación. El plan está documentado; firmware, cableado definitivo y recepción real todavía no están implementados.

## Objetivo de la primera entrega física

Obtener temperatura superficial y aceleración de una lavadora identificada, enviarlas al PC con origen y unidades verificables, guardar un historial y comparar ciclos normales. La primera aceptación se centra en calidad del dato y funcionamiento de la cadena; el diagnóstico predictivo no es requisito de esta etapa.

## Preparar antes de comprar

| Elemento | Referencia prevista | Confirmación necesaria |
| --- | --- | --- |
| Controlador | ESP32 de 30 pines, Micro USB | Variante, placa/pinout exactos y dimensiones; no asumir intercambiabilidad entre anuncios. |
| Acelerómetro | MPU6050 GY-521 externo | Variante de módulo, alimentación/interfaz admitidas, orientación y método de fijación. |
| Temperatura | DS18B20 externo cableado | Variante y conexiones documentadas; comprobar cable y dimensiones físicos. |
| Alimentación | Adaptador externo regulado USB 5 V/2 A y cable Micro USB | Modelo comercial, documentación y cable de datos necesario para programación. |
| Gabinete | Cuerpo/tapa de prueba nominales 120 × 90 × 55 mm | Cotas de placas y conectores, tornillería, entradas, junta y soporte. |
| Banco | Lavadora concreta | Marca/modelo, ubicación, superficie de fijación y ciclos disponibles. |

Presupuesto histórico aproximado: 100.000 CLP como referencia flexible; no es una cotización actual. Montaje previsto detrás de la lavadora, bajo techo. Recorrido objetivo de cable del acelerómetro ≈20 cm: medir recorrido completo y comprobar comunicación; no asumir que funciona por esa distancia.

No se fija todavía un mapa de pines, resistencias o instrucciones de cableado: deberán derivarse de las placas efectivamente adquiridas y sus fichas. El prototipo usa sensores externos y alimentación externa USB; no prevé incorporar red eléctrica ni modificar la instalación interna de la lavadora.

## Trabajo de software que debe quedar resuelto

| Etapa | Acción concreta | Criterio para avanzar |
| --- | --- | --- |
| 1. Identificación | Inventariar equipo, variantes, sensores, orientación y montaje; asignar identidad estable de dispositivo/activo | Registro inequívoco del hardware y del lugar de medida. |
| 2. Firmware básico | Leer sensores por separado; registrar estados de error, desconexión y reinicio | Valores con unidades, tiempos y calidad explícitos; sin sustituir una falla por un dato inventado. |
| 3. Muestreo de vibración | Definir tasa real sostenible, ventana, filtrado y cálculo RMS tras quitar DC; conservar muestras de validación | Frecuencia efectiva medida y RMS contrastado con cálculo independiente. No copiar 1.000 Hz del simulador sin comprobarlo. |
| 4. Tiempo y contrato | Definir adquisición UTC/reloj no sincronizado, secuencia, sesión de arranque, origen `real` y versión | Paquetes distinguibles entre reinicios; sin confundir hora de adquisición y recepción. |
| 5. Transporte | Implementar ESP32 → router → PC, receptor validado y autenticado con alcance de red decidido | Rechazo de identidad/formato inválidos, duplicados y datos viejos; desconexión y reconexión probadas. |
| 6. Integración neiron | Añadir modo real y adaptador explícito; conservar simulación y pruebas previas | Panel muestra origen; datos de prueba y físicos se identifican y separan. |
| 7. Registro físico | Guardar datos, configuración y metadatos del ciclo; exportar CSV con unidades | Paquetes recibidos coinciden con historial y exportación; pausa/ausencia no aparentan lectura actual. |
| 8. Comparación | Repetir ciclos normales y estudiar variaciones antes de definir umbrales | Referencia contextualizada por carga, fase, montaje y calidad; resultados documentados. |

El servidor actual escucha en 127.0.0.1 y rechaza orígenes externos; **el ESP32 no puede usarlo directamente por Wi-Fi desde otro equipo**. Habrá que diseñar y verificar el receptor de red y su adaptación. Cambiar una dirección de escucha no completa la adquisición real.

## Montaje y gabinete

Primero revisar placas/conectores contra el modelo 3D e imprimir una prueba de ajuste. Resolver fijación del sensor, repetibilidad de orientación, recorrido de cables, entrada USB y pasos de sensores. La lectura de superficie depende de su ubicación/contacto; no representa automáticamente temperatura interna. La vibración depende del montaje y de la fase del ciclo.

Los STL actuales son cuerpo/tapa de prueba: pared/fondo nominales 3 mm, sin junta definitiva ni soporte mural funcional. Impresora, material, holguras, cierre y montaje siguen pendientes. IP54 es objetivo histórico, sin certificación. No afirmar estanqueidad ni cumplimiento a partir del render.

## Ensayos cuando llegue la electrónica

1. **Banco de mesa:** alimentación/programación, identidad, lectura separada de sensores, reinicio y errores controlados.
2. **Cadena al PC:** validar paquetes, guardar historial, exportar y recuperar señal. Medir tasa de adquisición y publicación por separado.
3. **Lavadora quieta:** fijación y línea base, orientación del acelerómetro, temperatura ambiente/superficial y ruido de referencia.
4. **Ciclos normales observados:** registrar fases, carga, hora, montaje y duración. Repetir condiciones para evaluar consistencia; no introducir fallas deliberadas en la lavadora.
5. **Revisión de datos:** faltantes, duplicados, saturación, tiempos, cambios de montaje y comparación de ciclos. Ajustar reglas de prueba después de entender la referencia.

Registro mínimo por ensayo: identificador, fecha UTC y local, firmware/software, dispositivo/activo, ubicación/orientación, carga y fase conocida, frecuencia/ventana reales, configuración, eventos, observación humana y archivos exportados. Determinar duración y número de repeticiones cuando se conozcan equipo y ciclos; no inventar un mínimo validado.

## Aceptación de la primera prueba

- Lecturas etiquetadas `real`, unidades y calidad correctas; no mezcladas con pruebas `simulated`.
- Muestreo, ventana RMS y cadencia de publicación verificados, sin asumir que “envío cada segundo” equivale a “muestreo a 1 Hz”.
- Datos nuevos, viejos, ausentes y reinicios diferenciados; pérdida de señal visible.
- Historial/exportación consistentes y montaje registrado para poder repetir la prueba.
- Resultados de ciclos normales documentados; umbrales y conclusiones limitados a la evidencia obtenida.

Con esta etapa aceptada se podrá decidir si conviene mejorar gabinete, sensores, reportes o análisis. La IA/MACHINA sigue como opción futura y no es necesaria para operar el núcleo.
