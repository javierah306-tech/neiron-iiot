# Generadores Blender incluidos

- neiron_demo_v03.py: demostración esquemática animada del sistema.
- neiron_carcasa_prueba_v03.py: cuerpo y tapa de prueba, STL y comprobación geométrica.
- prototipo_01_neiron_v02.py: dependencia necesaria con funciones geométricas compartidas.

Ejecutar desde la raíz del repositorio con Blender instalado:

    blender --background --python 03_SCRIPTS_BLENDER_CODEX/neiron_demo_v03.py
    blender --background --python 03_SCRIPTS_BLENDER_CODEX/neiron_carcasa_prueba_v03.py

Si Blender no está en PATH, sustituir blender por la ruta del ejecutable local. Los scripts usan rutas relativas para sus salidas. Reinician la escena: ejecutar en proceso separado y respaldar las salidas editadas manualmente antes de regenerarlas. Los informes JSON generados pueden contener rutas locales; revisarlos antes de publicar.

Esta selección no contiene todo el historial de scripts ni los informes privados del proyecto original.
