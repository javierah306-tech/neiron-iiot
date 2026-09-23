# neiron - Demostración y piezas de prueba v03

## 1. Escena interactiva en Blender

Archivo: blend_files/neiron_lavadora_demo_v03.blend.

- Reproducir/pausar con el botón Play de la línea de tiempo o Espacio según mapa de teclas.
- Recorrer fotogramas 1-240 para mover tambor, abrir/cerrar tapa y seguir paquetes hacia el PC.
- Vista inicial: fotograma 120, tapa abierta. Rueda para acercar y botón central para orbitar. Teclado numérico 0 alterna cámara y vista libre.
- Colección 18: cámaras general, instalación posterior e interior. Seleccionar una cámara y usar la opción de establecer cámara activa para inspeccionar otra vista.
- Los componentes son objetos seleccionables; las colecciones separan entorno, sensores, hardware, flujo y rótulos.
- Copia grande del gabinete identificada como detalle x3: es una ampliación del mismo nodo, no un segundo equipo.

La lavadora se inspira en las fotos 46377.jpg y 46378.jpg. No se reproducen desorden, calefón ni objetos ajenos al sistema. Dimensiones y transmisión mecánica internas son esquemáticas: no se inspeccionó la máquina. El nodo se propone detrás, accesible, con fuente USB externa. Ubicación y recorrido de aproximadamente 20 cm deben medirse en instalación real.

Flujo explicado: movimiento del motor -> vibración de carcasa -> MPU6050 y temperatura superficial DS18B20 -> ESP32 -> Wi-Fi/router -> PC que guarda, grafica y compara ciclos. Los sensores no llevan radio independiente.

Todos los gráficos, valores y paquetes son simulados. La muestra no está conectada a hardware ni demuestra predicción de falla, vida útil o diagnóstico de rodamientos. La temperatura superficial no equivale a temperatura interna del motor. La frecuencia de muestreo de vibración no es la frecuencia de envío de un paquete por segundo.

## 2. Cuerpo y tapa sin electrónica

Archivo: blend_files/neiron_carcasa_y_tapa_PRUEBA_v03.blend. Contiene exactamente dos objetos de malla: cuerpo vacío y tapa a un lado. No contiene accesorios, luces, cámaras ni electrónica.

Archivos STL individuales en impresion_prueba, unidades numéricas en mm:

- neiron_cuerpo_120x90x51_PRUEBA.stl: 120 x 90 x 51 mm.
- neiron_tapa_120x90x4_PRUEBA.stl: 120 x 90 x 4 mm.

Paredes/fondo nominales de 3 mm; cuatro pilares integrados. Tapa con pasos de 3.4 mm y cuerpo con pilotos de 2.5 mm para repasar/roscar según tornillería final. Las entradas de cable están cerradas y señaladas con tres pequeñas marcas de centro: se mecanizan a la cota del prensaestopas o solución USB elegida.

Se entregan para una primera impresión de ajuste, no como gabinete industrial terminado. Faltan selección/ensayo de junta, alojamiento de sellado, fijación mural funcional y ajuste a componentes comerciales. No hay certificación IP ni perfil de impresión/G-code: la impresora sigue pendiente. No instalar la fuente de red dentro.

Imprimir por separado: cada STL ocupa 120 x 90 mm. El conjunto extendido ocupa aproximadamente 260 x 90 mm y no cabe completo en una cama de 256 mm. Importar a escala 100% en mm, comprobar las cotas indicadas y que el fondo plano apoye en la cama. Cuerpo con cavidad hacia arriba; tapa plana. Configuración de material/capas/relleno se fijará con impresora y filamento reales.

## 3. Verificación realizada

- Revisión visual de renders de escena y piezas.
- Comprobación de mallas: una componente conectada por pieza, sin aristas abiertas/no manifold y volumen positivo.
- Segunda lectura independiente de los STL: dimensiones correctas, cada arista compartida por dos triángulos, sin triángulos degenerados y volumen positivo.
- Informes: impresion_prueba/validacion_geometria.json y validacion_stl_independiente.json.
- Estas comprobaciones no sustituyen una vista por capas del laminador ni prueba física de ajuste y sellado.
