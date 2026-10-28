"""Arma el .hwt instalable de cada carátula directo desde las piezas, sin Theme Studio.

El Watch 3 (HarmonyOS 3.0) lee la carátula de `watch_face_config.xml` y las
imágenes de `res/` (ver `empaquetar.py`). Este script escribe ese XML con las
mismas capas que Theme Studio armó para Burdeos Fume, calculando cada posición
desde `guia.json`, y empaqueta todo en `hwt/reloj/<título>.hwt`.

Requiere haber corrido antes `piezas.py` y `portadas.py`.
Uso: .venv/bin/python hwt.py [claves]
"""

import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path

from PIL import Image

import generar as g
import piezas as pz

C = g.C
PIEZAS = g.RAIZ / "piezas"
SALIDA = g.RAIZ / "hwt" / "reloj"
VERSION = "2.1.1"
AUTOR = "Moy_fbpw"

# Título que muestra el reloj y título corto (Theme Studio lo pide como «título chino»).
TITULOS = {
    "01-negro": ("Esmoquin", "Esmoquin"),
    "02-blanco-dorado": ("Porcelana", "Porcelana"),
    "03-blanco": ("Bauhaus", "Bauhaus"),
    "04-vino": ("Burdeos Fume", "Burdeo"),
    "05-verde-militar": ("Campo", "Campo"),
    "06-azul-cielo": ("Rayos de sol", "Rayos"),
    "07-amarillo": ("Ambar", "Ambar"),
    "08-rojo-sangre": ("Cotes de Geneve", "Cotes"),
}

DIA_Y = 127  # Centro vertical del día; validado en el reloj.
AIRE_AMPM = 4  # Espacio entre los minutos y am/pm.
# Fecha y día del AOD: posiciones validadas en el reloj (el día va alineado a la izquierda).
AOD_FECHA_X, AOD_SEMANA_X = 175, 238
CONTENEDOR = (183, 284, 283, 384)  # Recorte de la vista previa que muestra el editor de la batería.

# value_type de Huawei.
HORA, MINUTO, DIA_MES, MES, SEMANA, AMPM = 12, 13, 17, 51, 52, 50
BATERIA, BATERIA_ICONO = 9, 54
MANECILLA_HORA, MANECILLA_MINUTO, MANECILLA_SEGUNDO = 150, 153, 154


def redondear(v):
    """Redondeo hacia arriba en .5, como las posiciones que validamos en Theme Studio."""
    return math.floor(v + .5)


class Recursos:
    """Imágenes de `res/` con nombres A100_NNN; las idénticas se guardan una sola vez."""

    def __init__(self):
        self.archivos = {}  # nombre → bytes
        self.por_contenido = {}

    def agregar(self, datos):
        clave = hashlib.sha256(datos).digest()
        if clave not in self.por_contenido:
            nombre = f"A100_{len(self.archivos) + 1:03d}.png"
            self.por_contenido[clave] = nombre
            self.archivos[nombre] = datos
        return self.por_contenido[clave]

    def lista(self, rutas):
        return ",".join(self.agregar(Path(r).read_bytes()) for r in rutas)


class Carpeta:
    """Acceso a las piezas de una carátula y a su `guia.json`."""

    def __init__(self, clave, recursos):
        self.raiz = PIEZAS / clave
        self.guia = json.loads((self.raiz / "guia.json").read_text(encoding="utf-8"))
        self.recursos = recursos

    def __getitem__(self, ruta):
        return self.guia["piezas"][ruta]

    def res(self, *rutas):
        return self.recursos.lista(self.raiz / r for r in rutas)

    def digitos(self, grupo):
        return self.res(*(f"{grupo}/{d}.png" for d in range(10)))


def capa(i, tipo, ambiente, **atributos):
    """Una capa del XML; `ambient_mode` (1 = AOD) va después de `value_type`, como en Theme Studio."""
    pares = list(atributos.items())
    nombres = [k for k, _ in pares]
    pares.insert(nombres.index("value_type") + 1 if "value_type" in nombres else 0, ("ambient_mode", ambiente))
    return f'<layer index="{i}" draw_type="{tipo}" ' + " ".join(f'{k}="{v}"' for k, v in pares) + "/>"


def unica(i, ambiente, res, x, y):
    return capa(i, "single_res", ambiente, res_name=res, res_position=f"{x},{y}")


def seleccion(i, ambiente, valor, res, x, y):
    return capa(i, "selected_res", ambiente, value_type=valor, res_name=res, res_position=f"{x},{y}")


def numero(i, ambiente, valor, res, vacio, x, y, alinear="left"):
    return capa(i, "combined_res", ambiente, res_align=alinear, value_type=valor, res_name=res,
                res_invalid=vacio, res_default=vacio, res_sign="", res_position=f"{x},{y}")


def manecilla(i, ambiente, valor, res, giro):
    largo = giro["y"]
    caja = f"{redondear(C - largo)},{redondear(C - largo)},{redondear(2 * largo)},{redondear(2 * largo)}"
    return capa(i, "hand_res", ambiente, value_type=valor, res_left=res, rotate_start_angel=0,
                rotate_end_angel=360, rotate_point_hand=f"{giro['x']:g},{giro['y']:g}", rotate_rect=caja)


def alto(p, pieza, centro_y):
    """Posición vertical de una pieza dibujada en el centro del lienzo, movida a su renglón."""
    return redondear(centro_y + p[pieza]["y"] - C)


def hora_digital(p, centro_x):
    """Posiciones de HH, dos puntos, MM (y am/pm) centradas como en la vista previa."""
    w = p["hora/0.png"]["ancho"]
    dos = p["hora/dos-puntos.png"]["ancho"]
    tiene_ampm = "hora/am.png" in p.guia["piezas"]
    ampm = AIRE_AMPM + max(p["hora/am.png"]["ancho"], p["hora/pm.png"]["ancho"]) if tiene_ampm else 0
    x0 = centro_x - (4 * w + dos + ampm) / 2
    return dict(hh=redondear(x0), dos=redondear(x0 + 2 * w), mm=redondear(x0 + 2 * w + dos),
                ampm=redondear(x0 + 4 * w + dos + AIRE_AMPM))


def config(p, aod):
    """Las capas en el mismo orden que Theme Studio: fondo, batería, fecha y hora."""
    hx, hy = pz.TEXTOS["hora"][5:7]
    fx, fy = pz.TEXTOS["fecha"][5:7]
    bx, by = pz.TEXTOS["bateria"][5:7]
    vacio = p.res("fecha/transparente.png")
    vacio_hora = p.res("hora/transparente.png")
    vacio_bat = p.res("bateria/transparente.png")
    aod_vacio = aod.res("fecha/transparente.png")

    # Batería: el número va alineado a la derecha y el % lo sigue; centrados con dos dígitos.
    wb, wp = p["bateria/0.png"]["ancho"], p["bateria/porcentaje.png"]["ancho"]
    ancla = redondear(bx - (2 * wb + wp) / 2 + 2 * wb)
    icono = p["bateria/icono-000.png"]
    contenedor = Image.open(p.raiz / "vista-previa.png").crop(CONTENEDOR)
    vista = io.BytesIO()
    contenedor.save(vista, "PNG")

    # Fecha dd - MM en la ventana de las 3.
    wf, wg = p["fecha/0.png"]["ancho"], p["fecha/guion.png"]["ancho"]
    f0 = fx - (4 * wf + wg) / 2
    f_y = alto(p, "fecha/0.png", fy)

    h = hora_digital(p, hx)
    h_y = alto(p, "hora/0.png", hy)
    a = hora_digital(aod, pz.AOD_TEXTOS["hora"][5])
    a_y = alto(aod, "hora/0.png", pz.AOD_TEXTOS["hora"][6])
    af_y = alto(aod, "fecha/0.png", pz.AOD_TEXTOS["fecha"][6])
    aw, ag = aod["fecha/0.png"]["ancho"], aod["fecha/guion.png"]["ancho"]
    # El reloj numera la semana de 1 (lunes) a 7; la posición 0 no se usa y Theme Studio repite el lunes.
    dias = [f"dias/{i}-{d.lower()}.png" for i, d in enumerate(pz.DIAS, 1)]
    dias = dias[:1] + dias

    capas = f"""<?xml version="1.0" encoding="utf-8"?>
<watchface>
    <element label="background" is_support_option="false" res_preview="">
        {unica(1, 0, p.res("fondo.png"), 0, 0)}
        {unica(2, 1, aod.res("fondo.png"), 0, 0)}
    </element>
    <element label="widget">
        <container index="1" data_type="17" res_preview="{p.recursos.agregar(vista.getvalue())}" rect="0,0,100,100" is_support_option="false">
            {seleccion(1, 0, BATERIA_ICONO, p.res(*(f"bateria/icono-{n:03d}.png" for n in range(0, 101, 10))), icono["x"], icono["y"])}
            {numero(2, 0, BATERIA, p.digitos("bateria"), vacio_bat, ancla, alto(p, "bateria/0.png", by), "right")}
            {unica(3, 0, p.res("bateria/porcentaje.png"), ancla, alto(p, "bateria/porcentaje.png", by))}
        </container>
    </element>
    <element label="date" is_support_option="false" res_preview="">
        {numero(1, 0, DIA_MES, p.digitos("fecha"), vacio, redondear(f0), f_y)}
        {unica(2, 0, p.res("fecha/guion.png"), redondear(f0 + 2 * wf), f_y)}
        {numero(3, 0, MES, p.digitos("fecha"), vacio, redondear(f0 + 2 * wf + wg), f_y)}
        {seleccion(4, 0, SEMANA, p.res(*dias), p[dias[0]]["x"], alto(p, dias[0], DIA_Y))}
        {numero(5, 1, DIA_MES, aod.digitos("fecha"), aod_vacio, AOD_FECHA_X, af_y)}
        {unica(6, 1, aod.res("fecha/guion.png"), AOD_FECHA_X + 2 * aw, af_y)}
        {numero(7, 1, MES, aod.digitos("fecha"), aod_vacio, AOD_FECHA_X + 2 * aw + ag, af_y)}
        {seleccion(8, 1, SEMANA, aod.res(*dias), AOD_SEMANA_X, alto(aod, dias[0], pz.AOD_TEXTOS["fecha"][6]))}
    </element>
    <element label="time" is_support_option="false" res_preview="">
        {unica(1, 0, p.res("hora/dos-puntos.png"), h["dos"], h_y)}
        {numero(2, 0, MINUTO, p.digitos("hora"), vacio_hora, h["mm"], h_y)}
        {seleccion(3, 0, AMPM, p.res("hora/am.png", "hora/pm.png", "hora/ampm-vacio.png"), h["ampm"], alto(p, "hora/am.png", hy))}
        {numero(4, 0, HORA, p.digitos("hora"), vacio_hora, h["hh"], h_y)}
        {manecilla(5, 0, MANECILLA_HORA, p.res("manecillas/hora.png"), p.guia["giro"]["hora"])}
        {manecilla(6, 0, MANECILLA_MINUTO, p.res("manecillas/minuto.png"), p.guia["giro"]["minuto"])}
        {manecilla(7, 0, MANECILLA_SEGUNDO, p.res("manecillas/segundo.png"), p.guia["giro"]["segundo"])}
        {unica(8, 0, p.res("manecillas/centro.png"), p["manecillas/centro.png"]["x"], p["manecillas/centro.png"]["y"])}
        {numero(9, 1, HORA, aod.digitos("hora"), aod.res("hora/transparente.png"), a["hh"], a_y)}
        {unica(10, 1, aod.res("hora/dos-puntos.png"), a["dos"], a_y)}
        {numero(11, 1, MINUTO, aod.digitos("hora"), aod.res("hora/transparente.png"), a["mm"], a_y)}
        {manecilla(12, 1, MANECILLA_HORA, aod.res("manecillas/hora.png"), aod.guia["giro"]["hora"])}
        {manecilla(13, 1, MANECILLA_MINUTO, aod.res("manecillas/minuto.png"), aod.guia["giro"]["minuto"])}
        {unica(14, 1, aod.res("manecillas/centro.png"), aod["manecillas/centro.png"]["x"], aod["manecillas/centro.png"]["y"])}
    </element>
</watchface>
"""
    return capas


def descripcion(titulo, corto, nombre):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<HwTheme>
  <title>{titulo}</title>
  <title-cn>{corto}</title-cn>
  <author>{AUTOR}</author>
  <designer>{AUTOR}</designer>
  <screen>HWHD09</screen>
  <version>{VERSION}</version>
  <font>Default</font>
  <font-cn>默认</font-cn>
  <briefinfo>{json.dumps({"en_US": nombre}, ensure_ascii=False)}</briefinfo>
</HwTheme>
"""


def armar(estilo):
    clave = estilo["clave"]
    titulo, corto = TITULOS[clave]
    recursos = Recursos()
    portadas = PIEZAS / clave / "portadas"
    recursos.agregar((portadas / "res.png").read_bytes())  # A100_001: vista previa del editor.
    xml = config(Carpeta(clave, recursos), Carpeta("00-aod", recursos))
    info = descripcion(titulo, corto, estilo["nombre"].replace(" · ", " - "))

    interno = io.BytesIO()
    with zipfile.ZipFile(interno, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("watchface/", b"", zipfile.ZIP_STORED)
        z.writestr("watchface/res/", b"", zipfile.ZIP_STORED)
        for nombre, datos in recursos.archivos.items():
            z.writestr(f"watchface/res/{nombre}", datos)
        z.writestr("watchface/watch_face_config.xml", xml)
        z.writestr("watchface/watch_face_info.xml", info)

    destino = SALIDA / f"{titulo}.hwt"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_STORED) as hwt:
        hwt.writestr("com.huawei.watchface", interno.getvalue())
        hwt.writestr("description.xml", info)
        hwt.write(portadas / "aod.jpg", "preview/aod.jpg")
        hwt.write(portadas / "cover.jpg", "preview/cover.jpg")
        hwt.write(portadas / "icon.jpg", "preview/icon_small.jpg")
    return destino, len(recursos.archivos)


def main(claves):
    for estilo in g.ESTILOS:
        if claves and estilo["clave"] not in claves:
            continue
        destino, n = armar(estilo)
        print(f"{estilo['clave']}: {destino.relative_to(g.RAIZ)} ({n} imágenes, {destino.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1:])
