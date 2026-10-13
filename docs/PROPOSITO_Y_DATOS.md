# Propósito, datos y laboratorio virtual

Actualizado el 13 de octubre de 2026. La lavadora será el primer ejemplo físico una vez adquiridos los accesorios. Motor / Lab permanece como banco virtual para probar aplicaciones e ideas con datos simulados.

## Qué problema se quiere explorar

Un sistema accesible de monitoreo debe convertir lecturas en un historial comprensible: identificar el equipo, expresar unidades, distinguir una lectura nueva de una antigua, mostrar cambios y dejar constancia de alarmas e intervenciones. neiron explora esa cadena para activos pequeños y aplicaciones futuras en pequeñas empresas industriales. Todavía no se ha demostrado su desempeño con sensores físicos.

## Por qué empezar por simulación

La electrónica y el montaje no estaban disponibles para una adquisición real. Generar datos sintéticos permite desarrollar y repetir ensayos de software: operación normal, señales elevadas, detención, ausencia, recuperación y reinicio. En Motor / Lab las causas son entradas explícitas, por lo que se sabe qué se modificó y se puede comparar la respuesta prevista por el modelo.

La simulación motor–bomba se realizó para proporcionar un banco con comportamiento variable y un contrato de telemetría, con el que comprobar si una aplicación registra y muestra correctamente los datos. El banco 0.2 ensayó la recepción en neiron; Motor / Lab 1.0.0 se separó para reutilizarlo con receptores genéricos elegidos por el usuario. La web 1.1.0 ofrece revisión pública y experimentos independientes. No conecta automáticamente el simulador autónomo con neiron.

## Qué aporta cada idea

| Idea | Aporte al conjunto |
| --- | --- |
| Lavadora como primer caso | Equipo concreto para aprender sobre ciclos, montaje y variaciones normales cuando exista la electrónica. |
| Gabinete Blender/STL | Espacio previsto de electrónica, fabricación reproducible y prueba de ajuste. |
| Animación de lavadora | Comunicación visual de la cadena sensores/ESP32/red/PC. |
| neiron | Persistencia, visualización, reglas de alarma, reconocimiento e intervenciones. |
| Motor / Lab | Escenarios controlados, modelo reducido, datos sintéticos y pruebas de integración. |
| Edición web | Permite que otras personas exploren y revisen sin depender del PC del autor. |

El laboratorio virtual es la combinación de estos trabajos. Su enfoque de innovación consiste en reducir la barrera para experimentar: diseño reproducible, electrónica de bajo costo prevista, trazabilidad y visualización explicable. Es una propuesta de desarrollo; no una demostración de superioridad industrial ni de novedad patentable.

## Qué datos se producen

Motor / Lab representa un motor monofásico de referencia de aproximadamente 3,7 kW, 230 V y 50 Hz, acoplado a una bomba centrífuga de agua limpia. Estos parámetros son supuestos, no la placa de un equipo identificado. Cuatro zonas: rodamiento posterior NDE, carcasa, rodamiento delantero DE y bomba.

- Temperatura de contacto superficial sintética, resolución 0,0625 °C y saturación virtual explícita entre −55 y 125 °C. No mide bobinado ni temperatura interna real.
- Aceleración triaxial sintética a 1.000 Hz durante 1 s. Se elimina el valor medio de cada eje y se calcula RMS vectorial en m/s². No equivale a velocidad RMS en mm/s.
- Contexto calculado: RPM, caudal, altura manométrica, presión, potencia y carga supuestas.
- Identidad de sesión, secuencia, origen `simulated`, calidad, revisión, tiempo físico y adquisición UTC.

La escala 1×/10×/60× acelera el avance físico, sin multiplicar las muestras por eje ni la tasa de publicación. El ruido JavaScript usa un generador distinto de Python: comparte causas y ecuaciones, pero no las muestras aleatorias exactas.

## Qué se puede comprobar con ellos

Recepción y validación del contrato, unidades, orden y duplicados, persistencia, CSV, gráficos, umbrales de prueba, reconocimiento de alarmas, intervenciones, ausencia de señal y recuperación. Las alarmas completas pertenecen a neiron; Motor / Lab muestra referencias visuales y produce telemetría.

No permite concluir que un sensor está calibrado, que el montaje funciona, que los umbrales son adecuados para una lavadora concreta, ni que una falla física se diagnostica con precisión. Un conjunto sintético puede probar código de análisis o aprendizaje; su desempeño no demuestra generalización a equipos reales.

## Cómo realizar un ensayo virtual útil

1. Abrir una sesión nueva, mantener operación normal y descargar una referencia.
2. Modificar una sola causa y anotar hipótesis, valor y escala de tiempo. Observar la transición, no solo el estado final.
3. Exportar CSV y JSON antes de cerrar. Comparar zona, temperatura y RMS con la referencia; el JSON conserva eventos de ajustes.
4. Restaurar “Normal” para comprobar recuperación. El calor acumulado se conserva y desciende gradualmente.
5. Ensayar pérdida de señal y pausa por separado: la pérdida de telemetría permite que la planta continúe; la pausa detiene el avance.
6. Registrar resultado como “comportamiento del modelo / prueba de software”, indicando versión y límites.

La web retiene 3.600 paquetes recientes en memoria por pestaña y no recibe datos de otros visitantes. Al ocultarla suspende el avance; al cerrarla o recargarla se pierde el ensayo no exportado. El JSON/CSV contiene agregados y configuración, no ventanas triaxiales completas. Para ensayos extensos persistentes usar la distribución Python/SQLite.

## Cómo se pasa a datos reales

El [plan de lavadora física](PLAN_LAVADORA_FISICA.md) prepara compra verificada, identificación, firmware, montaje, adquisición, transporte y comparación de ciclos. Se conservará origen y trazabilidad para distinguir real/simulado. El software actual no habilita recepción física; esa transición exige implementación y pruebas nuevas.
