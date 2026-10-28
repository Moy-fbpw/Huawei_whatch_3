# Carátulas Huawei Watch 3

Ocho carátulas analógicas (466×466) y un AOD común. `hwt.py` arma los `.hwt` instalables
directo desde las piezas; Theme Studio ya no hace falta.

## Scripts

| Script | Qué hace | Cómo se corre |
|---|---|---|
| `generar.py` | Dibuja las carátulas en SVG y la hoja de vista previa (`vista-previa/hoja.png`) | `python3 generar.py` |
| `piezas.py` | Exporta las piezas sueltas a `piezas/<carátula>/` con su `guia.json` | `.venv/bin/python piezas.py` |
| `portadas.py` | Genera las imágenes que pide Theme Studio al exportar (res, cover, icon, aod) | `.venv/bin/python portadas.py` |
| `hwt.py` | Arma el `.hwt` instalable de cada carátula en `hwt/reloj/<título>.hwt` | `.venv/bin/python hwt.py [claves]` |
| `empaquetar.py` | Convierte un `.hwt` exportado con Theme Studio en uno instalable (`hwt/reloj/`) | `python3 empaquetar.py hwt/<carátula>.hwt` |

Requisitos: macOS con Google Chrome (convierte SVG a PNG) y Pillow para recortar:

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Orden: `generar.py` → `piezas.py` → `portadas.py` → `hwt.py`. `piezas.py` (unos 4 min) vuelve a crear
las subcarpetas de cada carátula y conserva `portadas/`.

## Piezas por carátula

| Archivo | Uso en Theme Studio |
|---|---|
| `fondo.png` | Fondo de 466×466 (esfera, índices, números y marco de fecha) |
| `manecillas/hora.png`, `minuto.png`, `segundo.png` | Manecillas apuntando a las 12. Posición 233,233; ángulo 0–360; punto de giro en `guia.json` → `giro` |
| `manecillas/centro.png` | Tapa central, encima de las manecillas |
| `hora/0-9.png`, `dos-puntos.png`, `am.png`, `pm.png` | Hora digital chica (12 h) |
| `fecha/0-9.png`, `guion.png` | Fecha `dd - MM` dentro de la ventana de las 3 |
| `bateria/0-9.png`, `porcentaje.png`, `icono-000…100.png` | Porcentaje y el ícono por nivel (cada 10 %) |
| `dias/1-lunes.png … 7-domingo.png` | Día de la semana en español |
| `vista-previa.png` | Imagen de referencia de cómo debe quedar |

`guia.json` trae, por pieza, su posición (`x`, `y`) y tamaño en la esfera, el centro de cada texto
(`ubicaciones`) y el punto de giro de cada manecilla (`giro`).

Los dígitos de un mismo grupo tienen el mismo tamaño, para que no bailen al cambiar la hora.

## AOD (`piezas/00-aod/`)

Fondo con marcas, manecillas de hora y minuto, tapa central, hora digital (`hora/`), fecha (`fecha/`) y día (`dias/`).
Medido sobre la vista previa: 2.4 % de pixeles no negros. Huawei pide como máximo 10–20 %.

## Orden de capas

Fondo → datos (fecha, día, batería, hora digital) → manecillas → tapa central.

## Cómo arma `hwt.py` la carátula

El Watch 3 (HarmonyOS 3.0) lee `watch_face_config.xml` y las imágenes de `res/` dentro del paquete
`com.huawei.watchface`. Si el paquete trae el `watchface.bin` que agrega Theme Studio 11, el reloj
confirma la instalación y luego la descarta sin avisar; por eso `hwt.py` no lo incluye.

Las capas y sus `value_type` son las que Theme Studio armó para Burdeos Fume. Las posiciones salen de
`guia.json`; con los tamaños anteriores coincidieron con las de Theme Studio en las 28 capas, salvo la
tapa central (1 px más centrada aquí) y el borde del fondo, que Theme Studio suaviza.
La semana lleva 8 imágenes porque el reloj cuenta de 1 (lunes) a 7 y la posición 0 no se usa.

## Instalar en el reloj

1. `.venv/bin/python hwt.py` (o `empaquetar.py` si la carátula se exportó con Theme Studio).
2. Copiar `hwt/reloj/<título>.hwt` al celular y abrirlo con Gadgetbridge (*Instalador de FW/App*).

Gadgetbridge debe estar emparejado con el ID de cuenta Huawei puesto **antes** de emparejar
(ajustes del reloj → *Cuenta de Huawei*); si no, el reloj detecta otra cuenta y ofrece restablecerse.
