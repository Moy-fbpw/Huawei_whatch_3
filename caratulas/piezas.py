"""Exporta las piezas sueltas de cada carátula para armarlas en Theme Studio.

Cada pieza se dibuja en su posición real sobre un lienzo de 466x466, se
convierte a PNG con Chrome y se recorta con Pillow. Así el recorte da también
la coordenada exacta donde va la pieza, que se guarda en `guia.json`.

Uso: .venv/bin/python piezas.py
"""

import json
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import generar as g

C = g.C
SALIDA = g.RAIZ / "piezas"
SOMBRA_PIEZA = (0, 0)  # Centrada: en Theme Studio la sombra gira junto con la manecilla.
DIAS = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]

# Textos dinámicos: (fuente, peso, tamaño, espaciado, opacidad, centro x, centro y).
# Los centros coinciden con la vista previa de generar.py.
TEXTOS = {
    "hora": ("Avenir Next", 500, 13, .5, .8, C, 313.5),
    "fecha": ("Avenir Next", 500, 13, 0, 1, C + 166, C + 1),
    "bateria": ("Avenir Next", 500, 11, 0, .75, C + 10, 333),
}
AOD_TEXTOS = {
    "hora": ("Avenir Next", 500, 15, 1, 1, C, 317),
    "fecha": ("Avenir Next", 500, 15, 1.5, 1, C, 147),
}


def texto(car, fuente, peso, tam, espaciado, opacidad, color, ancla="middle"):
    """Un carácter o palabra en el centro del lienzo (centrado, o empezando ahí con ancla="start")."""
    return (f'<text x="{C}" y="{C}" font-family="{fuente}" font-weight="{peso}" font-size="{tam}" '
            f'letter-spacing="{espaciado}" text-anchor="{ancla}" dominant-baseline="central" '
            f'fill="{color}" opacity="{opacidad}">{car}</text>')


class Lote:
    """Junta las piezas de una carátula, las convierte en paralelo y las recorta."""

    def __init__(self, carpeta, p):
        self.carpeta, self.p = carpeta, p
        self.piezas = []  # (ruta relativa, svg, modo de recorte)

    def agregar(self, ruta, cuerpo, recorte="auto"):
        self.piezas.append((ruta, g.svg(cuerpo, self.p, SOMBRA_PIEZA), recorte))

    def exportar(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            def convertir(i):
                ruta_svg = tmp / f"{i}.svg"
                ruta_svg.write_text(self.piezas[i][1], encoding="utf-8")
                g.a_png(ruta_svg, tmp / f"{i}.png")
                return Image.open(tmp / f"{i}.png").convert("RGBA")

            with ThreadPoolExecutor(max_workers=8) as hilos:
                imagenes = list(hilos.map(convertir, range(len(self.piezas))))

        cajas = {}
        # Los grupos (dígitos de un mismo tipo) comparten tamaño para alinearse en Theme Studio.
        for (ruta, _, recorte), im in zip(self.piezas, imagenes):
            if recorte.startswith(("grupo:", "izq:")):
                caja = im.getbbox()
                if caja:
                    a = cajas.setdefault(recorte, [C, C, C, C])
                    a[0], a[1] = min(a[0], caja[0]), min(a[1], caja[1])
                    a[2], a[3] = max(a[2], caja[2]), max(a[3], caja[3])

        guia = {}
        for (ruta, _, recorte), im in zip(self.piezas, imagenes):
            if recorte == "completo":
                caja = (0, 0, g.TAM, g.TAM)
            elif recorte.startswith("sep:"):
                # "sep:<grupo>[:aire]": ancho propio, altura del grupo y aire opcional a los lados.
                _, nombre, *aire = recorte.split(":")
                aire = int(aire[0]) if aire else 0
                propia, grupo = im.getbbox(), cajas["grupo:" + nombre]
                caja = (propia[0] - aire, grupo[1], propia[2] + aire, grupo[3])
            elif recorte.startswith("izq:"):
                # Grupo alineado a la izquierda: misma caja para todos, sin centrar.
                caja = tuple(int(v) for v in cajas[recorte])
            elif recorte.startswith("grupo:"):
                x0, y0, x1, y1 = cajas[recorte]
                medio = max(C - x0, x1 - C)  # Simétrico respecto al centro para no descuadrar.
                caja = (int(C - medio), y0, int(C + medio + .5), y1)
            else:
                caja = im.getbbox()
            destino = self.carpeta / ruta
            destino.parent.mkdir(parents=True, exist_ok=True)
            im.crop(caja).save(destino)
            guia[ruta] = dict(x=caja[0], y=caja[1], ancho=caja[2] - caja[0], alto=caja[3] - caja[1])

        # Theme Studio pide, en cada número armado con dígitos, una imagen transparente del tamaño de un dígito.
        for grupo in ("hora", "fecha", "bateria"):
            if f"{grupo}/0.png" in guia:
                info = guia[f"{grupo}/0.png"]
                Image.new("RGBA", (info["ancho"], info["alto"])).save(self.carpeta / grupo / "transparente.png")
        # Y en am/pm, una casilla «blank» para cuando el reloj está en formato de 24 horas.
        if "hora/am.png" in guia:
            ancho = max(guia["hora/am.png"]["ancho"], guia["hora/pm.png"]["ancho"])
            alto = max(guia["hora/am.png"]["alto"], guia["hora/pm.png"]["alto"])
            Image.new("RGBA", (ancho, alto)).save(self.carpeta / "hora" / "ampm-vacio.png")
        return guia


def pivote(info):
    """Punto de giro dentro de la imagen recortada (el centro de la esfera)."""
    return dict(x=round(C - info["x"], 1), y=round(C - info["y"], 1))


def textos_dinamicos(lote, tabla, color, prefijo=""):
    for clave, (fuente, peso, tam, esp, op, _, _) in tabla.items():
        for d in range(10):
            lote.agregar(f"{prefijo}{clave}/{d}.png", texto(d, fuente, peso, tam, esp, op, color), f"grupo:{clave}")
    fuente, peso, tam, esp, op, _, _ = tabla["hora"]
    lote.agregar(f"{prefijo}hora/dos-puntos.png", texto(":", fuente, peso, tam, esp, op, color), "sep:hora")
    if "fecha" in tabla:
        fuente, peso, tam, esp, op, _, _ = tabla["fecha"]
        lote.agregar(f"{prefijo}fecha/guion.png", texto("-", fuente, peso, tam, esp, op, color), "sep:fecha:4")


def ubicaciones(tabla):
    return {clave: dict(centro_x=v[5], centro_y=v[6], fuente=v[0], tamaño=v[2]) for clave, v in tabla.items()}


def caratula(p):
    carpeta = SALIDA / p["clave"]
    lote = Lote(carpeta, p)
    tinta = p["tinta"]

    lote.agregar("fondo.png", g.capa_fondo(p) + g.marco_fecha(p), "completo")
    lote.agregar("manecillas/hora.png", g.horario(p, 0))
    lote.agregar("manecillas/minuto.png", g.minutero(p, 0))
    lote.agregar("manecillas/segundo.png", g.segundero(p, 0))
    lote.agregar("manecillas/centro.png", g.centro(p))

    textos_dinamicos(lote, TEXTOS, tinta)
    for sufijo in ("am", "pm"):
        lote.agregar(f"hora/{sufijo}.png", texto(sufijo, "Avenir Next", 500, 13, .5, .8, tinta))
    lote.agregar("bateria/porcentaje.png", texto("%", "Avenir Next", 500, 11, 0, .75, tinta), "sep:bateria")
    for nivel in range(0, 101, 10):
        lote.agregar(f"bateria/icono-{nivel:03d}.png", g.icono_bateria(p, nivel))
    for i, dia in enumerate(DIAS, 1):
        lote.agregar(f"dias/{i}-{dia.lower()}.png",
                     texto(dia, p["fuente_dia"], 400, 14, 3.5, .9, tinta), "grupo:dias")

    piezas = lote.exportar()
    shutil.copy(g.SALIDA / f"{p['clave']}.png", carpeta / "vista-previa.png")
    return dict(nombre=p["nombre"], piezas=piezas, ubicaciones=ubicaciones(TEXTOS),
                giro=dict(hora=pivote(piezas["manecillas/hora.png"]),
                          minuto=pivote(piezas["manecillas/minuto.png"]),
                          segundo=pivote(piezas["manecillas/segundo.png"]),
                          posicion=dict(x=C, y=C)))


def aod():
    carpeta = SALIDA / "00-aod"
    lote = Lote(carpeta, dict(g.ESTILOS[0]))
    lote.agregar("fondo.png", g.aod_fondo(), "completo")
    lote.agregar("manecillas/hora.png", g.aod_manecilla(118, 12, 0))
    lote.agregar("manecillas/minuto.png", g.aod_manecilla(200, 9, 0))
    lote.agregar("manecillas/centro.png", g.aod_centro())
    textos_dinamicos(lote, AOD_TEXTOS, g.AOD_GRIS)
    for i, dia in enumerate(DIAS, 1):
        lote.agregar(f"dias/{i}-{dia.lower()}.png", texto(dia, "Avenir Next", 500, 15, 1.5, 1, g.AOD_GRIS, "start"), "izq:dias")

    piezas = lote.exportar()
    shutil.copy(g.SALIDA / "00-aod.png", carpeta / "vista-previa.png")
    return dict(nombre="AOD (todas)", piezas=piezas, ubicaciones=ubicaciones(AOD_TEXTOS),
                giro=dict(hora=pivote(piezas["manecillas/hora.png"]),
                          minuto=pivote(piezas["manecillas/minuto.png"]),
                          posicion=dict(x=C, y=C)))


def main(claves):
    """Exporta todas las carátulas, o sólo las claves indicadas (p. ej. `00-aod 04-vino`)."""
    trabajos = [(p["clave"], lambda p=p: caratula(p)) for p in g.ESTILOS] + [("00-aod", aod)]
    for clave, trabajo in trabajos:
        if claves and clave not in claves:
            continue
        for sub in ("manecillas", "hora", "fecha", "bateria", "dias"):  # Las portadas se conservan.
            shutil.rmtree(SALIDA / clave / sub, ignore_errors=True)
        guia = trabajo()
        (SALIDA / clave / "guia.json").write_text(json.dumps(guia, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{clave}: {len(guia['piezas'])} piezas")
    print(f"Listo: {SALIDA}")


if __name__ == "__main__":
    main(sys.argv[1:])
