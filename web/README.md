# NEIRON Â· Motor / Lab Web 1.1.0

Laboratorio estÃ¡tico de motor monofÃ¡sico y bomba centrÃ­fuga, adaptado de Motor / Lab Python 1.0.0. La geometrÃ­a SVG, el inspector y los controles se conservan; la fÃ­sica reducida y la adquisiciÃ³n sintÃ©tica se ejecutan en JavaScript en cada pestaÃ±a.

Abre `index.html` o sirve la carpeta `web` en cualquier alojamiento estÃ¡tico. No requiere Python para funcionar, API, CDN, cuenta ni conexiÃ³n con un PC. Sitio pÃºblico: https://neiron-motor-lab.sunsetfly128.chatgpt.site

## Datos y lÃ­mites

Todo paquete tiene `source: simulated`. Cuatro zonas, temperatura superficial, aceleraciÃ³n RMS vectorial en m/sÂ², reloj UTC, identidad, secuencia y revisiÃ³n. CSV incluye ajustes por paquete; JSON aÃ±ade eventos de configuraciÃ³n. Semilla base 512 y versiÃ³n del modelo se exportan. RNG propio: las muestras aleatorias no coinciden punto por punto con Python.

Memoria de pestaÃ±a: 3.600 paquetes recientes; grÃ¡ficos de 240. No hay persistencia tras cerrar o recargar, ni recolecciÃ³n central de visitantes. PestaÃ±a oculta suspende la simulaciÃ³n; al volver espera un paquete nuevo. No reconstruye tiempo ausente. Las ventanas triaxiales de 1 s/1.000 Hz se generan para RMS; el visor dibuja 120 ms y los archivos de ensayo exportan agregados, no las ventanas completas.

El modelo es ilustrativo, sin calibraciÃ³n ni diagnÃ³stico validado. No hay IA ni hardware conectado. SQLite/REST/SSE/POST pertenecen a la distribuciÃ³n local Python, conservada en GitHub.

## VerificaciÃ³n del 13 de octubre de 2026

- 16 comprobaciones del modelo JavaScript (`verify-model.cjs`).
- ComparaciÃ³n de hidrÃ¡ulica, RPM y nodos tÃ©rmicos contra Python en tres instantes con cambio de condiciones y apagado; tolerancia 1e-11.
- 12 comprobaciones en Microsoft Edge, escritorio y viewport mÃ³vil (`verify-browser.cjs`), incluyendo CSV/JSON y dos visitantes. Sin errores JavaScript ni llamadas `/api/`.
- 23 pruebas de la distribuciÃ³n Python original aprobadas con bases temporales.

Compatibilidad prevista: navegadores modernos con SVG, Canvas y JavaScript. Edge probado; Chrome, Firefox y Safari no se ejecutaron en esta revisiÃ³n. El viewport mÃ³vil se verificÃ³ en Edge, no en un dispositivo fÃ­sico.

Repositorio del proyecto, historia y entregas: https://github.com/javierah306-tech/neiron-iiot

## Pruebas de desarrollo

Desde esta carpeta: `node verify-model.cjs`. La comprobación de navegador es opcional y requiere Playwright y Edge en el entorno de desarrollo: `node verify-browser.cjs`. La página pública no necesita estas dependencias. Los archivos temporales de ensayos no forman parte del código distribuido.
