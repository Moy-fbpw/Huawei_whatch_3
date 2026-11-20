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
# Oro champán (el de Burdeos): el oro de todas las carátulas; el amarillo de fantasía no se usa.
CHAMPAN = ("#fff4dc", "#d6b98a", "#7e6238")
LATON = ("#f3e3b8", "#b99a5c", "#5e4c25")
ACERO_NEGRO = ("#7d858f", "#24282e", "#08090b")
ACERO_AZUL = ("#b8cde4", "#34557f", "#0f2643")

# Hora de muestra para la vista previa (la clásica de los catálogos).
MUESTRA = dict(h=10, m=8, s=36, dia="LUNES", fecha="26 - 10", bateria=60)

TODOS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # El 3 lo ocupa la ventana de fecha.

# Textos de datos, compartidos por la vista previa y las piezas (piezas.py, hwt.py):
# (fuente, peso, tamaño, espaciado, opacidad, centro x, centro y).
# La hora digital es el dato que se lee de reojo: Demi Bold y opacidad completa para que aguante
# el sol con brillo bajo, pero sigue muy por debajo de los números de la esfera.
TEXTOS = {
    "hora": ("Avenir Next", 600, 16, .3, 1, C, 313),
    "fecha": ("Avenir Next", 500, 13, 0, 1, C + 166, C + 1),
    "bateria": ("Avenir Next", 500, 13, 0, .85, C + 12, 336),
}
AMPM = ("Avenir Next", 500, 11, .3, .75)  # am/pm más chico, sobre la misma línea base de los dígitos.
AOD_TEXTOS = {
    "hora": ("Avenir Next", 600, 18, 1, 1, C, 317),
    "fecha": ("Avenir Next", 500, 15, 1.5, 1, C, 147),
}
BASE = .4  # Línea base de Avenir Next medida en Chrome: 0.4 × tamaño debajo del centro del texto.
ICONO_BATERIA = (C - 26, 333)  # Esquina superior izquierda del ícono de batería.

ESTILOS = [
    # Esmoquin: negro con cepillado circular apenas visible, números en relieve y luminiscencia dorada.
    dict(clave="01-negro", nombre="Negro · Esmoquin", fondo=("#121212", "#000000"), textura="circular",
         tinta="#cfd2d6", metal=PLATA, segundero="#d8d8d8", aguja="fina", lume="#d9b04a",
         numeros=dict(fuente="Avenir Next Condensed", peso=500, tam=31, radio=172, metal=True),
         indices="aplicado", pista="lineas", manecillas="delfina", fuente_dia="Avenir Next"),
    # Porcelana: esfera blanca de vestir, índices largos y perlas en oro champán y agujas finas.
    dict(clave="02-blanco-dorado", nombre="Blanco y oro · Porcelana", fondo=("#ffffff", "#ece8df"),
         textura="liso", tinta="#5b4729", metal=CHAMPAN, segundero="#a3824f", aguja="fina",
         numeros=dict(fuente="Didot", peso=700, tam=23, radio=170, color="#8a6c42"),
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
    # Piloto: naranja fumé que oscurece hacia una banda marrón, números grandes crema y hojas con lume.
    # La tinta de los datos es café oscuro: sobre naranja, el blanco no se lee al sol.
    dict(clave="09-naranja", nombre="Naranja · Piloto", fondo=("#ff8243", "#c24a17"), textura="granulado",
         tinta="#2b1206", tinta_pista="#f6e9d4", banda="#4a1c0a", metal=PLATA,
         segundero="#f6e9d4", aguja="flecha", punta="#2f8a55", lume="#f3e6c8",
         numeros=dict(fuente="Avenir Next", peso=600, tam=34, radio=163, color="#fbf1e2", sombra=True),
         indices="ninguno", pista="banda", manecillas="hoja", fuente_dia="Avenir Next"),
    # Oxford: gris oxford con rayos de sol, índices largos facetados, sin números y bastones con lume.
    dict(clave="10-gris-oxford", nombre="Gris oxford · Oxford", fondo=("#6a6e73", "#26292d"), textura="rayos",
         rayos_fuerza=.05, tinta="#eceef0", metal=PLATA, segundero="#eceef0", aguja="fina", lume="#e9ecef",
         numeros=None, indices="aplicado", largo_indice=32, pista="lineas", manecillas="baston",
         fuente_dia="Avenir Next"),
    # Peonía: rosa liso con fumé suave (como Burdeos) y anillo de surcos; textos y minutos en plata con un
    # halo ciruela que los separa del rosa al sol. La fecha conserva la tinta ciruela en su ventana.
    dict(clave="11-rosa", nombre="Rosa · Peonía", fondo=("#ec9cb1", "#b95873"), textura="liso", fume=.3,
         anillo=(176, 206), tinta="#f1f2f5", tinta_fecha="#3e1424", halo="#5c1a2e", metal=PLATA,
         segundero="#f4f4f6",
         aguja="fina", lume="#ffffff", numeros=None, indices="aplicado", largo_indice=26, pista="lineas",
         manecillas="baston", fuente_dia="Optima"),
    # Pizarra: azul pizarra liso y claro, oro champán, romanos XII y VI y minutos numerados en el borde.
    dict(clave="12-azul-pizarra", nombre="Azul pizarra · Pizarra", fondo=("#83a0b0", "#4c6878"),
         textura="liso", tinta="#ffffff", tinta_fecha="#22323c", halo="#22323c", metal=CHAMPAN, segundero="#e3c27e",
         aguja="fina", lume="#f6f2e8", radio_indice=200, largo_indice=22, sin_indice=(12, 3, 6),
         numeros=dict(fuente="Bodoni 72", peso=400, tam=27, radio=160, metal=True, horas=(12, 6),
                      etiquetas={12: "XII", 6: "VI"}),
         indices="aplicado", pista="numerada", manecillas="baston", fuente_dia="Avenir Next"),
]


def polar(radio, grados):
    """Punto a `radio` del centro; 0 grados = las 12, sentido horario."""
    a = math.radians(grados - 90)
    return C + radio * math.cos(a), C + radio * math.sin(a)


def defs(p, sombra=(1.5, 2.5)):
    m1, m2, m3 = p["metal"]
    f1, f2 = p["fondo"]
    fume = p["fume"] if isinstance(p.get("fume"), float) else .7
    return f"""<defs>
  <clipPath id="esfera"><circle cx="{C}" cy="{C}" r="{C}"/></clipPath>
  <radialGradient id="fondo" cx="50%" cy="44%" r="60%">
    <stop offset="0" stop-color="{f1}"/><stop offset="1" stop-color="{f2}"/>
  </radialGradient>
  <radialGradient id="fume" cx="50%" cy="48%" r="50%">
    <stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{fume}"/>
  </radialGradient>
  <filter id="halo" x="-30%" y="-60%" width="160%" height="220%">
    <feDropShadow dx="0" dy="0" stdDeviation="1.1" flood-color="{p.get("halo", "#000")}" flood-opacity=".6"/>
  </filter>
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
    <feDropShadow dx="{sombra[0]}" dy="{sombra[1]}" stdDeviation="1.6" flood-color="#000" flood-opacity=".38"/>
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
    if p.get("anillo"):
        r_in, r_out = p["anillo"]
        partes.append(f'<circle cx="{C}" cy="{C}" r="{(r_in + r_out) / 2}" fill="none" stroke="url(#fondo)" '
                      f'stroke-width="{r_out - r_in}"/>')
        for i, r in enumerate(range(r_in + 2, r_out, 2)):
            color = "#ffffff" if i % 2 else "#000000"
            partes.append(f'<circle cx="{C}" cy="{C}" r="{r}" fill="none" stroke="{color}" '
                          f'stroke-width="1" opacity=".07"/>')
        partes.append(f'<circle cx="{C}" cy="{C}" r="{r_in}" fill="none" stroke="#000" stroke-width="1.2" opacity=".22"/>'
                      f'<circle cx="{C}" cy="{C}" r="{r_in + 1.2}" fill="none" stroke="#fff" stroke-width="1" opacity=".3"/>')
    if p.get("fume"):
        partes.append(f'<circle cx="{C}" cy="{C}" r="{C}" fill="url(#fume)"/>')
    return f'<g clip-path="url(#esfera)">{"".join(partes)}</g>'


def pista(p):
    """Minutero exterior."""
    tinta, tipo = p.get("tinta_pista", p["tinta"]), p["pista"]
    partes = []
    if tipo == "banda":
        partes.append(f'<circle cx="{C}" cy="{C}" r="216" fill="none" stroke="{p["banda"]}" stroke-width="34" '
                      f'clip-path="url(#esfera)"/>'
                      f'<circle cx="{C}" cy="{C}" r="199" fill="none" stroke="{tinta}" stroke-width=".8" opacity=".5"/>')
        for i in range(60):
            hora = i % 5 == 0
            x1, y1 = polar(206 if hora else 213, i * 6)
            x2, y2 = polar(225, i * 6)
            partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{tinta}" '
                          f'stroke-width="{2.6 if hora else 1.1}" opacity="{.95 if hora else .7}"/>')
        return "\n".join(partes)
    if tipo == "numerada":
        for i in range(60):
            hora = i % 5 == 0
            x1, y1 = polar(203, i * 6)
            x2, y2 = polar(210, i * 6)
            partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{tinta}" '
                          f'stroke-width="{1.6 if hora else .9}" opacity="{.85 if hora else .55}"/>')
            if hora:
                x, y = polar(221, i * 6)
                partes.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="Avenir Next" font-weight="500" '
                              f'font-size="9.5" text-anchor="middle" dominant-baseline="central" fill="{tinta}" '
                              f'opacity=".75">{i or 60}</text>')
        return "\n".join(partes)
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
    radio = p.get("radio_indice", 222)
    for hora in range(1, 13):
        ang = hora * 30
        if hora in p.get("sin_indice", ()):
            continue
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
            y0, y1 = C - radio, C - radio + largo
            der = f"M{C + d},{y0} L{C + d + ext},{y0} L{C + d + inte},{y1} L{C + d},{y1} Z"
            izq = f"M{C + d},{y0} L{C + d - ext},{y0} L{C + d - inte},{y1} L{C + d},{y1} Z"
            partes.append(
                f'<g transform="rotate({ang} {C} {C})" filter="url(#sombra)">'
                f'<path d="{izq}" fill="url(#metalOscuro)" stroke="{p["metal"][2]}" stroke-width=".4"/>'
                f'<path d="{der}" fill="url(#metalClaro)" stroke="{p["metal"][2]}" stroke-width=".4"/>'
                f'</g>')
    return "\n".join(partes)


def numeros(p):
    n = p.get("numeros")
    if not n:
        return ""
    relleno = "url(#metalV)" if n.get("metal") else n.get("color", p["tinta"])
    borde = (f'stroke="{p["metal"][2]}" stroke-width=".4" filter="url(#sombra)"' if n.get("metal")
             else 'filter="url(#sombra)"' if n.get("sombra") else "")
    estiramiento = n.get("ancho", 1)
    etiquetas = n.get("etiquetas", {})
    partes = []
    for hora in n.get("horas", TODOS):
        x, y = polar(n["radio"], hora * 30)
        partes.append(
            f'<text transform="translate({x:.2f} {y:.2f}) scale({estiramiento} 1)" '
            f'font-family="{n["fuente"]}" font-weight="{n["peso"]}" font-size="{n["tam"]}" '
            f'text-anchor="middle" dominant-baseline="central" fill="{relleno}" {borde}>{etiquetas.get(hora, hora)}</text>')
    return "\n".join(partes)


def capa_fondo(p):
    return "\n".join([f'<circle cx="{C}" cy="{C}" r="{C}" fill="url(#fondo)"/>',
                      textura(p), pista(p), indices(p), numeros(p)])


def marco_fecha(p):
    """Ventana de fecha a las 3 (parte fija del fondo)."""
    claro = sum(int(p["fondo"][0][i:i + 2], 16) for i in (1, 3, 5)) > 450
    ventana = "#ffffff" if claro else "#000000"
    return f"""<g filter="url(#sombra)">
  <rect x="{C + 138}" y="{C - 11}" width="56" height="22" rx="2.5" fill="{ventana}" fill-opacity="{.75 if claro else .45}"
        stroke="url(#metalV)" stroke-width="1.6"/>
</g>"""


def halo(p):
    """Filtro que rodea los textos claros con un tono oscuro cuando el fondo también es claro."""
    return ' filter="url(#halo)"' if p.get("halo") else ""


def icono_bateria(p, bateria, x=ICONO_BATERIA[0], y=ICONO_BATERIA[1]):
    tinta = p["tinta"]
    nivel = 11 * bateria / 100
    return f"""<g transform="translate({x} {y})" opacity=".75"{halo(p)}>
  <rect x="0" y="0" width="14" height="7" rx="1.3" fill="none" stroke="{tinta}" stroke-width=".9"/>
  <rect x="14.3" y="2" width="1.4" height="3" fill="{tinta}"/>
  <rect x="1.5" y="1.5" width="{nivel:.1f}" height="4" fill="{tinta}"/>
</g>"""


def capa_datos(p, dia, fecha, h, m, bateria):
    """Datos discretos: día bajo las 12, fecha en ventana a las 3, hora digital y batería sobre las 6."""
    tinta = p["tinta"]
    sufijo = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    fa, pa, ta, ea, oa = AMPM
    # El am/pm va en un tspan para compartir la línea base con los dígitos (las piezas hacen lo mismo).
    ampm = (f'<tspan dx="4" font-family="{fa}" font-weight="{pa}" font-size="{ta}" letter-spacing="{ea}" '
            f'fill-opacity="{oa}">{sufijo}</tspan>')
    return f"""
<text x="{C}" y="132" font-family="{p['fuente_dia']}" font-size="14" letter-spacing="3.5" text-anchor="middle"
      fill="{tinta}" opacity=".9"{halo(p)}>{dia}</text>
{marco_fecha(p)}
{dato(TEXTOS["fecha"], fecha, p.get("tinta_fecha", tinta))}
{dato(TEXTOS["hora"], f"{h12}:{m:02d}", tinta, ampm, halo(p))}
{icono_bateria(p, bateria)}
{dato(TEXTOS["bateria"], f"{bateria}%", tinta, filtro=halo(p))}"""


def dato(spec, contenido, color, extra="", filtro=""):
    """Texto de datos centrado en su renglón, escrito sobre la línea base como lo dibuja el reloj."""
    fuente, peso, tam, esp, op, x, y = spec
    return (f'<text x="{x}" y="{y + BASE * tam:.1f}" font-family="{fuente}" font-weight="{peso}" '
            f'font-size="{tam}" letter-spacing="{esp}" text-anchor="middle" fill="{color}" '
            f'opacity="{op}"{filtro}>{contenido}{extra}</text>')


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
    elif tipo == "flecha":
        partes.append(f'<path d="M{C},{C - 214} L{C + 5.5},{C - 196} L{C - 5.5},{C - 196} Z" fill="{p["punta"]}"/>'
                      f'<rect x="{C - 2.6}" y="{C + 18}" width="5.2" height="20" rx="2.6" fill="{color}"/>')
    elif tipo == "contrapeso":
        partes.append(f'<rect x="{C - 2.6}" y="{C + 18}" width="5.2" height="20" rx="2.6" fill="{color}"/>')
    return (f'<g transform="rotate({angulo:.2f} {C} {C})" filter="url(#sombra)">{"".join(partes)}</g>')


ANCHOS = {"delfina": (13, 10), "hoja": (13, 10), "alfa": (12, 9), "aguja": (6, 4.6), "baston": (8, 6)}


def horario(p, angulo):
    return manecilla(p["manecillas"], 118, ANCHOS[p["manecillas"]][0], 18, angulo, p)


def minutero(p, angulo):
    return manecilla(p["manecillas"], 200, ANCHOS[p["manecillas"]][1], 22, angulo, p)


def capa_manecillas(p, h, m, s):
    return "\n".join([
        horario(p, (h % 12 + m / 60) * 30),
        minutero(p, (m + s / 60) * 6),
        segundero(p, s * 6),
        centro(p),
    ])


def centro(p):
    return (f'<circle cx="{C}" cy="{C}" r="6.5" fill="url(#metalV)" stroke="{p["metal"][2]}" stroke-width=".5"/>'
            f'<circle cx="{C}" cy="{C}" r="2.4" fill="{p["segundero"]}"/>')


def svg(cuerpo, p, sombra=(1.5, 2.5)):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{TAM}" height="{TAM}" '
            f'viewBox="0 0 {TAM} {TAM}">\n{defs(p, sombra)}\n{cuerpo}\n</svg>\n')


def caratula(p):
    t = MUESTRA
    return svg("\n".join([capa_fondo(p),
                          capa_datos(p, t["dia"], t["fecha"], t["h"], t["m"], t["bateria"]),
                          capa_manecillas(p, t["h"], t["m"], t["s"])]), p)


AOD_GRIS, AOD_PLATA, AOD_SOMBRA = "#7d8086", "#c3c6cb", "#5b5e63"


def aod_fondo():
    """Marcas del AOD: minutos finos y cuñas en las horas, doble a las 12."""
    partes = [f'<circle cx="{C}" cy="{C}" r="{C}" fill="#000"/>']
    for i in range(60):
        ang = i * 6
        if i % 5:
            x1, y1 = polar(214, ang)
            x2, y2 = polar(220, ang)
            partes.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                          f'stroke="{AOD_GRIS}" stroke-width="1.4" stroke-linecap="round"/>')
            continue
        hora = i // 5
        largo, ext = (22, 3.2) if hora % 3 == 0 else (15, 2.4)
        for d in ((-4.2, 4.2) if hora == 0 else (0,)):
            partes.append(f'<path transform="rotate({ang} {C} {C})" d="M{C + d - ext},{C - 222} '
                          f'L{C + d + ext},{C - 222} L{C + d + ext * .45},{C - 222 + largo} '
                          f'L{C + d - ext * .45},{C - 222 + largo} Z" fill="{AOD_PLATA}"/>')
    return "\n".join(partes)


def aod_manecilla(largo, ancho, angulo):
    puntos = mitades("delfina", largo, ancho, 16)
    return (f'<g transform="rotate({angulo:.2f} {C} {C})">'
            f'<path d="{ruta(puntos, espejo=True)}" fill="{AOD_SOMBRA}"/>'
            f'<path d="{ruta(puntos)}" fill="{AOD_PLATA}"/></g>')


def aod_centro():
    return f'<circle cx="{C}" cy="{C}" r="5" fill="#000" stroke="{AOD_PLATA}" stroke-width="1.6"/>'


def aod():
    """AOD única: fondo negro, marcas gris plata, dos manecillas, fecha y una mini hora digital.

    Sin segundero ni texturas: sólo se encienden las marcas, las agujas y dos textos.
    """
    t = MUESTRA
    partes = [aod_fondo(),
              dato(AOD_TEXTOS["fecha"], f'{t["fecha"]}   {t["dia"]}', AOD_GRIS),
              dato(AOD_TEXTOS["hora"], f'{t["h"]}:{t["m"]:02d}', AOD_GRIS),
              aod_manecilla(118, 12, (t["h"] % 12 + t["m"] / 60) * 30),
              aod_manecilla(200, 9, t["m"] * 6),
              aod_centro()]
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
    filas = -(-len(fichas) // 3)
    a_png(ruta_hoja, SALIDA / "hoja.png", ancho=1078, alto=56 + 366 * filas)
    print(f"Listo: {SALIDA}")


if __name__ == "__main__":
    main()
