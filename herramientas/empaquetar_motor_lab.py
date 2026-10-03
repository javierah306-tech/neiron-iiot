"""Distribución reproducible desde la única carpeta principal del simulador.

No copia el entorno, bases, informes privados ni datos operativos al portafolio.
Se ejecuta con la biblioteca estándar de Python 3.12.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

REPO = Path(__file__).resolve().parents[1]
TOP_LEVEL = {"README.md", "API.md", "MODELO.md", "VERIFICACION.md",
             "requirements.txt", "runtime.txt", ".gitignore",
             "instalar.bat", "iniciar.bat", "cerrar.bat", "probar.bat"}
SUBDIRS = {"twin", "examples", "tests"}
EXTENSIONS = {".py", ".js", ".cjs", ".css", ".html"}
NAME = "motor-lab-1.0.0-vista-mecanica.zip"
INTRO = """# Entrega Motor / Lab 1.0.0 · vista mecánica · 2 de octubre de 2026

Simulador independiente de motor monofásico 5 HP, acoplamiento y bomba de agua
limpia. Todos los datos y efectos son simulados. El interior es ilustrativo.

## Abrir esta entrega en Windows

1. Extrae TODO el ZIP en una carpeta local; no ejecutes archivos dentro del ZIP.
2. Necesitas Python 3.12 disponible para tu usuario. No se instala automáticamente.
3. Haz doble clic en `iniciar.bat`. Crea `.venv` aislado sin descargas ni paquetes
   de terceros y abre http://127.0.0.1:8766. Otro puerto: `iniciar.bat --port 8767`.
4. Pulsa **Acercar motor**, selecciona un componente y prueba los escenarios.
   La salida a otros programas permanece desactivada hasta que la actives.
5. Usa `cerrar.bat` para detener y guardar. Cerrar la pestaña no detiene el servicio.

Los accesos `.lnk` y los lanzadores de la carpeta del proyecto original no forman
parte de este ZIP: usa los `.bat` incluidos aquí. Datos por defecto en
`%LOCALAPPDATA%\\MotorPumpTwin`, fuera de la entrega. Al instalar en el mismo PC
conserva la base existente; no ejecutes dos instancias sobre la misma carpeta de
datos. Para pruebas separadas usa `iniciar.bat --port 8767 --data-dir "D:\\Ensayo"`.

## Contenido editable

`twin/`: modelo, contrato, reloj, SQLite, transporte, servidor, lanzador y web.
`examples/`: consulta Python y receptor local voluntario.
`tests/`: pruebas con bases temporales; `probar.bat` ejecuta el núcleo.
`API.md` y `MODELO.md`: contrato, física reducida y límites.
`VERIFICACION.md`: verificaciones históricas ejecutadas en Windows/Edge.
`README_DESARROLLO.md`: guía completa y contexto de la carpeta original.
`ENTREGA.json`: inventario y SHA-256 de los archivos de esta distribución.

Los ensayos de navegador requieren Node, Playwright y Edge como herramientas
opcionales de desarrollo. No son dependencias de uso del simulador. Configura
`TWIN_PLAYWRIGHT` si Playwright no está disponible como módulo habitual.

Este archivo es una distribución de la carpeta principal de desarrollo, no una
segunda implementación mantenida. No incluye datos, entornos ni el software
neiron. No hay hardware conectado, IA ni diagnóstico validado.
"""


def public_bytes(relative, data, project_root):
    """Normaliza rutas de desarrollo propias sin tocar la física del simulador."""
    if relative.endswith((".md", ".cjs")):
        content = data.decode("utf-8")
        content = content.replace(str(project_root), "CARPETA_DEL_PROYECTO")
        content = re.sub(r"(['\"])[A-Za-z]:/Users/[^/]+/\.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright\1", "'playwright'", content)
        return content.replace("\r\n", "\n").encode("utf-8")
    return data


def build(source, output):
    source = source.resolve(strict=True)
    if not (source / "twin/model.py").is_file():
        raise ValueError("La carpeta fuente debe contener twin/model.py.")
    files = {}
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if not path.is_file() or any(part.startswith(".") or part == "__pycache__" for part in relative.parts[:-1]):
            continue
        allowed = (len(relative.parts) == 1 and relative.name in TOP_LEVEL) or (
            relative.parts[0] in SUBDIRS and path.suffix in EXTENSIONS)
        if not allowed:
            continue
        name = relative.as_posix()
        if name == "README.md":
            name = "README_DESARROLLO.md"
        files[name] = public_bytes(name, path.read_bytes(), source.parent)
    if not {"twin/model.py", "twin/server.py", "twin/static/mechanics.js", "tests/test_twin.py"}.issubset(files):
        raise ValueError("Faltan fuentes esenciales en la selección.")
    files["README.md"] = INTRO.encode("utf-8")
    manifest = {"application": "Motor / Lab", "version": "1.0.0", "revision": "vista-mecanica-2026-10-02",
                "source_policy": "Distribución desde una única carpeta principal; sin datos operativos.",
                "files": [{"path": name, "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(files.items())]}
    files["ENTREGA.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / NAME
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo("MotorLab/" + name, date_time=(2026, 10, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            target.writestr(info, data, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {NAME}\n", encoding="utf-8")
    print(f"{archive.name}: {len(files)} archivos, {archive.stat().st_size} bytes; SHA-256 {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REPO.parent.parent / "07_SIMULADOR_MOTOR_BOMBA")
    parser.add_argument("--output", type=Path, default=REPO / "entregas")
    args = parser.parse_args()
    build(args.source, args.output)
