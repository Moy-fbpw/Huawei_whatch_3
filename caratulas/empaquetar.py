"""Convierte el .hwt que exporta Theme Studio en uno que acepta el Watch 3.

Theme Studio 11 mete un `watchface.bin` compilado dentro del paquete interno
(`com.huawei.watchface`). El Watch 3 con HarmonyOS 3.0 recibe ese archivo por
Gadgetbridge, confirma la instalación y luego lo descarta sin avisar. Sin el
`.bin` lee directo `watch_face_config.xml` y las imágenes de `res/`, como las
carátulas de la tienda para este modelo. También se quitan `hashCode` y
`ability.xml`, que esas carátulas no traen.

Uso: python3 empaquetar.py hwt/"Burdeos Fume.hwt" [...]
Deja el resultado en `hwt/reloj/` con el mismo nombre.
"""

import io
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "hwt" / "reloj"
INTERNO = "com.huawei.watchface"
SOBRANTES_INTERNOS = {"watchface.bin"}
SOBRANTES_EXTERNOS = {"hashCode", "ability.xml"}


def paquete_interno(datos):
    """El zip interno sin el `.bin`, conservando las carpetas y el orden original."""
    salida = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(datos)) as origen, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino:
        for info in origen.infolist():
            if info.filename not in SOBRANTES_INTERNOS:
                destino.writestr(info.filename, origen.read(info),
                                 zipfile.ZIP_STORED if info.is_dir() else zipfile.ZIP_DEFLATED)
    return salida.getvalue()


def empaquetar(ruta):
    destino = SALIDA / ruta.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ruta) as origen:
        if INTERNO not in origen.namelist():
            raise SystemExit(f"{ruta}: no trae {INTERNO}; ¿es un .hwt de carátula?")
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_STORED) as hwt:
            for info in origen.infolist():
                if info.filename in SOBRANTES_EXTERNOS or info.is_dir():
                    continue
                datos = origen.read(info)
                hwt.writestr(info.filename, paquete_interno(datos) if info.filename == INTERNO else datos)
    return destino


def main(rutas):
    if not rutas:
        raise SystemExit(__doc__)
    for ruta in map(Path, rutas):
        destino = empaquetar(ruta)
        print(f"{ruta.name}: {ruta.stat().st_size // 1024} KB → {destino.relative_to(RAIZ)}: {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1:])
