"""Genera las carátulas del Huawei Watch 3 (466x466) en SVG y PNG.

Cada carátula se arma por capas (fondo, datos, manecillas) para que después
se puedan exportar como piezas sueltas para Theme Studio. Todas comparten la
misma ubicación de datos (día arriba, fecha a las 3, hora digital y batería
abajo) y cambian el estilo: textura, números, índices y manecillas.

Uso: python3 generar.py
"""

import math
import subprocess
from pathlib import Path

TAM = 466
C = TAM / 2
RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "vista-previa"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Metales: (claro, medio, oscuro)
PLATA = ("#ffffff", "#c4c8ce", "#5f646c")
ORO = ("#fff0c0", "#cfa83c", "#7a5b16")
CHAMPAN = ("#fff4dc", "#d6b98a", "#7e6238")
LATON = ("#f3e3b8", "#b99a5c", "#5e4c25")
ACERO_NEGRO = ("#7d858f", "#24282e", "#08090b")
ACERO_AZUL = ("#b8cde4", "#34557f", "#0f2643")
ORO_PROFUNDO = ("#f7df96", "#b98a2c", "#4f390c")

# Hora de muestra para la vista previa (la clásica de los catálogos).
MUESTRA = dict(h=10, m=8, s=36, dia="LUNES", fecha="26 - 10", bateria=60)

TODOS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # El 3 lo ocupa la ventana de fecha.

ESTILOS = [
    # Esmoquin: negro con cepillado circular apenas visible, números en relieve y luminiscencia dorada.
    dict(clave="01-negro", nombre="Negro · Esmoquin", fondo=("#121212", "#000000"), textura="circular",
         tinta="#cfd2d6", metal=PLATA, segundero="#d8d8d8", aguja="fina", lume="#d9b04a",
         numeros=dict(fuente="Avenir Next Condensed", peso=500, tam=31, radio=172, metal=True),
         indices="aplicado", pista="lineas", manecillas="delfina", fuente_dia="Avenir Next"),
    # Porcelana: esfera blanca de vestir, índices dorados largos, perlas doradas y agujas finas.
    dict(clave="02-blanco-dorado", nombre="Blanco y oro · Porcelana", fondo=("#ffffff", "#ece8df"),
         textura="liso", tinta="#5a4318", metal=ORO_PROFUNDO, segundero="#9c7424", aguja="fina",
         numeros=dict(fuente="Didot", peso=700, tam=23, radio=170, color="#7a5a18"),
         indices="aplicado", largo_indice=30, pista="perlas", manecillas="aguja", fuente_dia="Didot"),
    # Bauhaus: blanco mate, tipografía geométrica impresa, agujas alfa negras y segundero azul acero.
    dict(clave="03-blanco", nombre="Blanco · Bauhaus", fondo=("#fcfcfc", "#e2e2e2"), textura="liso",
         tinta="#1b1c1e", metal=ACERO_NEGRO, segundero="#2456b0", aguja="fina",
         numeros=dict(fuente="Futura", peso=500, tam=26, radio=176),
         indices="trazo", pista="lineas", manecillas="alfa", fuente_dia="Futura"),
    # Burdeos: fumé con rayos de sol, índices aplicados en champán y doble índice a las 12.
    dict(clave="04-vino", nombre="Vino · Burdeos fumé", fondo=("#8a2440", "#1e0309"), textura="rayos",
         fume=True, tinta="#ead6b0", metal=CHAMPAN, segundero="#e3c27e", aguja="contrapeso",
         numeros=dict(fuente="Optima", peso=400, tam=23, radio=170, metal=True),
         indices="aplicado", pista="lineas", manecillas="delfina", fuente_dia="Optima"),
    # Campo: oliva granulado, números condensados color crema y luminiscencia crema en las agujas.
    dict(clave="05-verde-militar", nombre="Verde militar · Campo", fondo=("#5c6644", "#252b1a"),
         textura="granulado", tinta="#e8dfc2", metal=LATON, segundero="#d2ae5c", aguja="fina",
         lume="#efe6c8",
         numeros=dict(fuente="Futura", peso=500, tam=27, radio=182, ancho=.85),
         indices="ninguno", pista="ferrocarril", manecillas="alfa", fuente_dia="Futura"),
    # Azul acero: rayos de sol marcados, índices y agujas bastón en plata pulida.
    dict(clave="06-azul-cielo", nombre="Azul · Rayos de sol", fondo=("#5b80b0", "#1f3558"), textura="rayos",
         rayos_fuerza=.055, tinta="#eef2f7", metal=PLATA, segundero="#eef2f7", aguja="fina",
         numeros=dict(fuente="Avenir Next", peso=500, tam=23, radio=168, metal=True),
         indices="aplicado", largo_indice=28, pista="lineas", manecillas="baston", fuente_dia="Avenir Next"),
    # Ámbar: mostaza con rayos de sol, números pequeños impresos y agujas de hoja en acero negro.
    dict(clave="07-amarillo", nombre="Amarillo · Ámbar", fondo=("#f3cd5a", "#b98510"), textura="rayos",
         tinta="#1c1a16", metal=ACERO_NEGRO, segundero="#1c1a16", aguja="contrapeso",
         numeros=dict(fuente="Avenir Next", peso=500, tam=23, radio=176),
         indices="trazo", pista="lineas", manecillas="hoja", fuente_dia="Avenir Next"),
    # Granate: rojo profundo con Côtes de Genève, números Bodoni y agujas delfina en plata.
    dict(clave="08-rojo-sangre", nombre="Rojo sangre · Côtes de Genève", fondo=("#9a0b0b", "#2a0000"),
         textura="cotes", fume=True, tinta="#efe3e3", metal=PLATA, segundero="#e6e6e6", aguja="fina",
         numeros=dict(fuente="Bodoni 72", peso=400, tam=28, radio=170, metal=True),
         indices="aplicado", pista="lineas", manecillas="delfina", fuente_dia="Bodoni 72"),
]


def polar(radio, grados):
    """Punto a `radio` del centro; 0 grados = las 12, sentido horario."""
    a = math.radians(grados - 90)
    return C + radio * math.cos(a), C + radio * math.sin(a)


def defs(p):
    m1, m2, m3 = p["metal"]
    f1, f2 = p["fondo"]
    return f"""<defs>
  <clipPath id="esfera"><circle cx="{C}" cy="{C}" r="{C}"/></clipPath>
  <radialGradient id="fondo" cx="50%" cy="44%" r="60%">
    <stop offset="0" stop-color="{f1}"/><stop offset="1" stop-color="{f2}"/>
  </radialGradient>
  <radialGradient id="fume" cx="50%" cy="48%" r="50%">
    <stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/>
  </radialGradient>
  <linearGradient id="metalV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{m1}"/><stop offset=".55" stop-color="{m2}"/><stop offset="1" stop-color="{m3}"/>
  </linearGradient>
  <linearGradient id="metalClaro" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{m2}"/><stop offset="1" stop-color="{m1}"/>
  </linearGradient>
  <linearGradient id="metalOscuro" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{m3}"/><stop offset="1" stop-color="{m2}"/>
  </linearGradient>
  <linearGradient id="franja" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".07"/>
    <stop offset="1" stop-color="#000" stop-opacity=".08"/>
  </linearGradient>
  <filter id="grano" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .22 0"/>
  </filter>
  <filter id="sombra" x="-50%" y="-50%" width="200%" height="200%">
    <feDropShadow dx="1.5" dy="2.5" stdDeviation="1.6" flood-color="#000" flood-opacity=".38"/>
  </filter>
</defs>"""


def textura(p):
    tipo = p["textura"]
    partes = []
    if tipo == "rayos":
        n = 200
        for i in range(n):
            x1, y1 = polar(C, 360 * i / n)
            x2, y2 = polar(C, 360 * (i + 0.5) / n)
            color = "#ffffff" if i % 2 else "#000000"
            partes.append(f'<path d="M{C},{C} L{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f} Z" '
                          f'fill="{color}" opacity="{p.get("rayos_fuerza", .03)}"/>')
    elif tipo == "circular":
        for i, r in enumerate(range(6, 232, 2)):
            color = "#ffffff" if i % 3 else "#000000"
            partes.append(f'<circle cx="{C}" cy="{C}" r="{r}" fill="none" stroke="{color}" '
                          f'stroke-width="1" opacity=".035"/>')
    elif tipo == "guilloche":
        for i, r in enumerate(range(14, 228, 4)):
            color = "#ffffff" if i % 2 else "#0b2a4a"
            partes.append(f'<circle cx="{C}" cy="{C}" r="{r}" fill="none" stroke="{color}" '
                          f'stroke-width="1.6" opacity=".07"/>')
    elif tipo == "cotes":
        for x in range(-8, TAM + 8, 26):
            partes.append(f'<rect x="{x}" y="0" width="26" height="{TAM}" fill="url(#franja)" '
                          f'transform="rotate(-18 {C} {C})"/>')
    elif tipo == "granulado":
        partes.append(f'<rect width="{TAM}" height="{TAM}" filter="url(#grano)"/>')
    if p.get("fume"):
        partes.append(f'<circle cx="{C}" cy="{C}" r="{C}" fill="url(#fume)"/>')
    return f'<g clip-path="url(#esfera)">{"".join(partes)}</g>'


def pista(p):
    """Minutero exterior."""
    tinta, tipo = p["tinta"], p["pista"]
    partes = []
    if tipo == "ferrocarril":
        for r in (213, 223):
            partes.append(f'<circle cx="{C}" cy="{C}" r="{r}" fill="none" stroke="{tinta}" '
                          f'stroke-width=".8" opacity=".55"/>')
    for i in range(60):
        hora = i % 5 == 0
        if tipo == "perlas":
            if hora:
                continue
            x, y = polar(217, i * 6)
            partes.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.7" fill="url(#metalV)" '
                          f'stroke="{p["metal"][2]}" stroke-width=".4"/>')
            continue
        if tipo == "puntos":
            x, y = polar(218, i * 6)
            partes.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{2 if hora else 1.1}" '
                          f'fill="{tinta}" opacity="{.9 if hora else .6}"/>')
            continue
        if hora and p["indices"] == "aplicado":
            continue
        r_in = 207 if hora else 213
        x1, y1 = polar(r_in, i * 6)
        x2, y2 = polar(223, i * 6)
        ancho = 2 if hora else 1
        partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                      f'stroke="{tinta}" stroke-width="{ancho}" opacity="{.9 if hora else .55}"/>')
    return "\n".join(partes)


def indices(p):
    """Índices de hora: aplicados facetados (metal en relieve) o trazo impreso."""
    tipo = p["indices"]
    if tipo == "ninguno":
        return ""
    partes = []
    for hora in range(1, 13):
        ang = hora * 30
        if tipo == "trazo":
            x1, y1 = polar(198, ang)
            x2, y2 = polar(214, ang)
            partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                          f'stroke="{p["tinta"]}" stroke-width="2.6"/>')
            continue
        base = p.get("largo_indice", 22)
        largo = base + 4 if hora == 12 else min(base, 20) if hora == 3 else base  # El 3 no toca la fecha.
        for d in ((-4.6, 4.6) if hora == 12 else (0,)):  # Doble índice a las 12.
            ext, inte = 2.6, 1.7  # Más ancho afuera que adentro, como cuña.
            y0, y1 = C - 222, C - 222 + largo
            der = f"M{C + d},{y0} L{C + d + ext},{y0} L{C + d + inte},{y1} L{C + d},{y1} Z"
            izq = f"M{C + d},{y0} L{C + d - ext},{y0} L{C + d - inte},{y1} L{C + d},{y1} Z"
            partes.append(
                f'<g transform="rotate({ang} {C} {C})" filter="url(#sombra)">'
                f'<path d="{izq}" fill="url(#metalOscuro)" stroke="{p["metal"][2]}" stroke-width=".4"/>'
                f'<path d="{der}" fill="url(#metalClaro)" stroke="{p["metal"][2]}" stroke-width=".4"/>'
                f'</g>')
    return "\n".join(partes)


def numeros(p):
    n = p["numeros"]
    relleno = "url(#metalV)" if n.get("metal") else n.get("color", p["tinta"])
    borde = f'stroke="{p["metal"][2]}" stroke-width=".4" filter="url(#sombra)"' if n.get("metal") else ""
    estiramiento = n.get("ancho", 1)
    partes = []
    for hora in TODOS:
        x, y = polar(n["radio"], hora * 30)
        partes.append(
            f'<text transform="translate({x:.2f} {y:.2f}) scale({estiramiento} 1)" '
            f'font-family="{n["fuente"]}" font-weight="{n["peso"]}" font-size="{n["tam"]}" '
            f'text-anchor="middle" dominant-baseline="central" fill="{relleno}" {borde}>{hora}</text>')
    return "\n".join(partes)


def capa_fondo(p):
    return "\n".join([f'<circle cx="{C}" cy="{C}" r="{C}" fill="url(#fondo)"/>',
                      textura(p), pista(p), indices(p), numeros(p)])


def capa_datos(p, dia, fecha, h, m, bateria):
    """Datos discretos: día bajo las 12, fecha en ventana a las 3, hora digital y batería sobre las 6."""
    tinta = p["tinta"]
    sufijo = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    nivel = 11 * bateria / 100
    claro = sum(int(p["fondo"][0][i:i + 2], 16) for i in (1, 3, 5)) > 450
    ventana = "#ffffff" if claro else "#000000"
    return f"""
<text x="{C}" y="132" font-family="{p['fuente_dia']}" font-size="14" letter-spacing="3.5" text-anchor="middle"
      fill="{tinta}" opacity=".9">{dia}</text>
<g filter="url(#sombra)">
  <rect x="{C + 138}" y="{C - 11}" width="56" height="22" rx="2.5" fill="{ventana}" fill-opacity="{.75 if claro else .45}"
        stroke="url(#metalV)" stroke-width="1.6"/>
</g>
<text x="{C + 166}" y="{C + 1}" font-family="Avenir Next" font-weight="500" font-size="13" text-anchor="middle"
      dominant-baseline="central" fill="{tinta}">{fecha}</text>
<text x="{C}" y="318" font-family="Avenir Next" font-weight="500" font-size="13" letter-spacing=".5"
      text-anchor="middle" fill="{tinta}" opacity=".8">{h12}:{m:02d} {sufijo}</text>
<g transform="translate({C - 22} 330)" opacity=".75">
  <rect x="0" y="0" width="14" height="7" rx="1.3" fill="none" stroke="{tinta}" stroke-width=".9"/>
  <rect x="14.3" y="2" width="1.4" height="3" fill="{tinta}"/>
  <rect x="1.5" y="1.5" width="{nivel:.1f}" height="4" fill="{tinta}"/>
</g>
<text x="{C + 10}" y="337" font-family="Avenir Next" font-weight="500" font-size="11" text-anchor="middle"
      fill="{tinta}" opacity=".75">{bateria}%</text>"""


def mitades(tipo, largo, ancho, cola):
    """Contorno de la mitad derecha de una manecilla que apunta a las 12 (se refleja para la izquierda)."""
    w = ancho / 2
    if tipo == "delfina":  # Delgada, con cuello fino junto al centro.
        return [(0, -largo), (w, -largo * .3), (w * .35, -2), (0, cola)]
    if tipo == "aguja":  # Muy delgada, apenas afilada; la de los relojes de vestir.
        return [(0, -largo), (w, -largo + 10), (w * .75, cola), (0, cola)]
    if tipo == "baston":  # Bastón facetado con punta corta.
        return [(0, -largo), (w, -largo + 5), (w, cola), (0, cola)]
    if tipo == "alfa":  # Lanceolada, más ancha cerca de la base.
        return [(0, -largo), (w, -largo * .2), (w * .55, 0), (w * .3, cola), (0, cola)]
    raise ValueError(tipo)


def ruta(puntos, espejo=False):
    s = -1 if espejo else 1
    return "M" + " L".join(f"{C + s * x:.2f},{C + y:.2f}" for x, y in puntos) + " Z"


def manecilla(tipo, largo, ancho, cola, angulo, p):
    if tipo == "hoja":
        w = ancho * .62
        der = (f"M{C},{C - largo} Q{C + w * 1.5},{C - largo * .5} {C + w * .3},{C - 4} "
               f"L{C},{C + cola} Z")
        izq = (f"M{C},{C - largo} Q{C - w * 1.5},{C - largo * .5} {C - w * .3},{C - 4} "
               f"L{C},{C + cola} Z")
    else:
        puntos = mitades(tipo, largo, ancho, cola)
        der, izq = ruta(puntos), ruta(puntos, espejo=True)
    oscuro = p["metal"][2]
    partes = [f'<path d="{izq}" fill="url(#metalOscuro)" stroke="{oscuro}" stroke-width=".5"/>',
              f'<path d="{der}" fill="url(#metalClaro)" stroke="{oscuro}" stroke-width=".5"/>']
    if p.get("lume"):
        # Franja luminiscente sobre el eje, como en la referencia.
        partes.append(f'<line x1="{C}" y1="{C - 14}" x2="{C}" y2="{C - largo * .55:.2f}" '
                      f'stroke="{p["lume"]}" stroke-width="{ancho * .18:.2f}" stroke-linecap="round"/>')
    return (f'<g transform="rotate({angulo:.2f} {C} {C})" filter="url(#sombra)">{"".join(partes)}</g>')


def segundero(p, angulo):
    color, tipo = p["segundero"], p["aguja"]
    partes = [f'<rect x="{C - .7}" y="{C - 210}" width="1.4" height="{210 + 38}" fill="{color}"/>']
    if tipo == "paleta":
        partes.append(f'<circle cx="{C}" cy="{C - 172}" r="3.6" fill="{color}"/>')
    elif tipo == "contrapeso":
        partes.append(f'<rect x="{C - 2.6}" y="{C + 18}" width="5.2" height="20" rx="2.6" fill="{color}"/>')
    return (f'<g transform="rotate({angulo:.2f} {C} {C})" filter="url(#sombra)">{"".join(partes)}</g>')


def capa_manecillas(p, h, m, s):
    tipo = p["manecillas"]
    ancho_h, ancho_m = {"delfina": (13, 10), "hoja": (13, 10), "alfa": (12, 9), "aguja": (6, 4.6), "baston": (8, 6)}[tipo]
    return "\n".join([
        manecilla(tipo, 118, ancho_h, 18, (h % 12 + m / 60) * 30, p),
        manecilla(tipo, 200, ancho_m, 22, (m + s / 60) * 6, p),
        segundero(p, s * 6),
        f'<circle cx="{C}" cy="{C}" r="6.5" fill="url(#metalV)" stroke="{p["metal"][2]}" stroke-width=".5"/>',
        f'<circle cx="{C}" cy="{C}" r="2.4" fill="{p["segundero"]}"/>',
    ])


def svg(cuerpo, p):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{TAM}" height="{TAM}" '
            f'viewBox="0 0 {TAM} {TAM}">\n{defs(p)}\n{cuerpo}\n</svg>\n')


def caratula(p):
    t = MUESTRA
    return svg("\n".join([capa_fondo(p),
                          capa_datos(p, t["dia"], t["fecha"], t["h"], t["m"], t["bateria"]),
                          capa_manecillas(p, t["h"], t["m"], t["s"])]), p)


def aod():
    """AOD única: fondo negro, marcas gris plata, dos manecillas, fecha y una mini hora digital.

    Sin segundero ni texturas: sólo se encienden las marcas, las agujas y dos textos.
    """
    gris, plata, sombra = "#7d8086", "#c3c6cb", "#5b5e63"
    partes = [f'<circle cx="{C}" cy="{C}" r="{C}" fill="#000"/>']
    for i in range(60):
        ang = i * 6
        if i % 5:
            x1, y1 = polar(214, ang)
            x2, y2 = polar(220, ang)
            partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                          f'stroke="{gris}" stroke-width="1.4" stroke-linecap="round"/>')
            continue
        hora = i // 5
        largo, ext = (22, 3.2) if hora % 3 == 0 else (15, 2.4)
        for d in ((-4.2, 4.2) if hora == 0 else (0,)):
            partes.append(f'<path transform="rotate({ang} {C} {C})" d="M{C + d - ext},{C - 222} '
                          f'L{C + d + ext},{C - 222} L{C + d + ext * .45},{C - 222 + largo} '
                          f'L{C + d - ext * .45},{C - 222 + largo} Z" fill="{plata}"/>')
    t = MUESTRA
    partes.append(f'<text x="{C}" y="152" font-family="Avenir Next" font-weight="500" font-size="15" '
                  f'letter-spacing="1.5" text-anchor="middle" fill="{gris}">{t["fecha"]}   {t["dia"]}</text>')
    partes.append(f'<text x="{C}" y="322" font-family="Avenir Next" font-weight="500" font-size="15" '
                  f'letter-spacing="1" text-anchor="middle" fill="{gris}">{t["h"]}:{t["m"]:02d}</text>')
    for largo, ancho, ang in ((118, 12, (t["h"] % 12 + t["m"] / 60) * 30), (200, 9, t["m"] * 6)):
        puntos = mitades("delfina", largo, ancho, 16)
        partes.append(f'<g transform="rotate({ang:.2f} {C} {C})">'
                      f'<path d="{ruta(puntos, espejo=True)}" fill="{sombra}"/>'
                      f'<path d="{ruta(puntos)}" fill="{plata}"/></g>')
    partes.append(f'<circle cx="{C}" cy="{C}" r="5" fill="#000" stroke="{plata}" stroke-width="1.6"/>')
    return svg("\n".join(partes), dict(ESTILOS[0]))


def a_png(svg_path, png_path, ancho=TAM, alto=TAM):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", f"--window-size={ancho},{alto}",
                    f"--screenshot={png_path}", svg_path.as_uri()],
                   check=True, capture_output=True)


def hoja(fichas):
    """Hoja de contacto: todas las carátulas dentro de un bisel simulado."""
    celdas = "\n".join(
        f'<figure><div class="bisel"><img src="{archivo}"></div><figcaption>{nombre}</figcaption></figure>'
        for archivo, nombre in fichas)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body {{ margin:0; padding:28px; background:#1b1c1f; font-family:'Avenir Next'; color:#ddd;
       display:grid; grid-template-columns:repeat(3, 300px); gap:26px 34px; }}
figure {{ margin:0; text-align:center; }}
.bisel {{ width:300px; height:300px; border-radius:50%; padding:14px; box-sizing:border-box;
         background:radial-gradient(circle, #555 0 60%, #222 72%, #0c0c0c 100%);
         box-shadow:0 6px 18px rgba(0,0,0,.6); }}
.bisel img {{ width:100%; height:100%; border-radius:50%; display:block; }}
figcaption {{ margin-top:10px; font-size:15px; letter-spacing:.5px; }}
</style></head><body>{celdas}</body></html>"""


def main():
    SALIDA.mkdir(exist_ok=True)
    fichas = []
    for p in ESTILOS:
        ruta_svg = SALIDA / f"{p['clave']}.svg"
        ruta_svg.write_text(caratula(p), encoding="utf-8")
        a_png(ruta_svg, SALIDA / f"{p['clave']}.png")
        fichas.append((ruta_svg.name, p["nombre"]))

    ruta_aod = SALIDA / "00-aod.svg"
    ruta_aod.write_text(aod(), encoding="utf-8")
    a_png(ruta_aod, SALIDA / "00-aod.png")
    fichas.append((ruta_aod.name, "AOD (todas)"))

    ruta_hoja = SALIDA / "hoja.html"
    ruta_hoja.write_text(hoja(fichas), encoding="utf-8")
    a_png(ruta_hoja, SALIDA / "hoja.png", ancho=1078, alto=1100)
    print(f"Listo: {SALIDA}")


if __name__ == "__main__":
    main()
