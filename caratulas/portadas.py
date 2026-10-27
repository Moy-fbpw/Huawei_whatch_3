"""Genera las imágenes que pide Theme Studio al exportar (res, cover, icon, aod).

Se dibujan desde el SVG de cada carátula al tamaño pedido, para que no salgan
borrosas al agrandar la vista previa de 466x466.

Uso: .venv/bin/python portadas.py
"""

import io
import tempfile
from pathlib import Path

from PIL import Image

import generar as g

# Nombre: (formato, lado en px). Theme Studio pide cada una de menos de 200 KB.
PORTADAS = {"res": ("PNG", 250), "cover": ("JPEG", 960), "icon": ("JPEG", 390), "aod": ("JPEG", 960)}
LIMITE = 200 * 1024


def dibujar(svg_texto, lado, tmp):
    """Convierte el SVG a PNG de `lado` x `lado` con fondo transparente fuera de la esfera."""
    escalado = svg_texto.replace(f'width="{g.TAM}" height="{g.TAM}"', f'width="{lado}" height="{lado}"', 1)
    ruta = Path(tmp) / f"p{lado}.svg"
    ruta.write_text(escalado, encoding="utf-8")
    g.a_png(ruta, ruta.with_suffix(".png"), lado, lado)
    return Image.open(ruta.with_suffix(".png")).convert("RGBA")


def guardar(im, formato, destino):
    if formato == "PNG":
        im.save(destino, optimize=True)
    else:
        # JPG no tiene transparencia: lo de fuera de la esfera va en negro, como la pantalla apagada.
        plano = Image.new("RGB", im.size, "black")
        plano.paste(im, mask=im.getchannel("A"))
        for calidad in range(92, 40, -4):
            datos = io.BytesIO()
            plano.save(datos, "JPEG", quality=calidad, optimize=True)
            if datos.tell() <= LIMITE:
                break
        destino.write_bytes(datos.getvalue())
    peso = destino.stat().st_size
    assert peso <= LIMITE, f"{destino} pesa {peso} bytes"
    return peso


def main():
    aod = g.aod()
    with tempfile.TemporaryDirectory() as tmp:
        for p in g.ESTILOS:
            carpeta = g.RAIZ / "piezas" / p["clave"] / "portadas"
            carpeta.mkdir(parents=True, exist_ok=True)
            for nombre, (formato, lado) in PORTADAS.items():
                im = dibujar(aod if nombre == "aod" else g.caratula(p), lado, tmp)
                destino = carpeta / f"{nombre}.{'png' if formato == 'PNG' else 'jpg'}"
                print(f"{destino.relative_to(g.RAIZ)}: {lado}x{lado}, {guardar(im, formato, destino) // 1024} KB")


if __name__ == "__main__":
    main()
