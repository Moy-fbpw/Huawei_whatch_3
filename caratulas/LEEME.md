# Carátulas Huawei Watch 3

Ocho carátulas analógicas (466×466) y un AOD común, listas para armarse en Huawei Theme Studio.

## Scripts

| Script | Qué hace | Cómo se corre |
|---|---|---|
| `generar.py` | Dibuja las carátulas en SVG y la hoja de vista previa (`vista-previa/hoja.png`) | `python3 generar.py` |
| `piezas.py` | Exporta las piezas sueltas a `piezas/<carátula>/` con su `guia.json` | `.venv/bin/python piezas.py` |
| `portadas.py` | Genera las imágenes que pide Theme Studio al exportar (res, cover, icon, aod) | `.venv/bin/python portadas.py` |
| `empaquetar.py` | Convierte el `.hwt` de Theme Studio en uno instalable en el reloj (`hwt/reloj/`) | `python3 empaquetar.py hwt/<carátula>.hwt` |

Requisitos: macOS con Google Chrome (convierte SVG a PNG) y Pillow para recortar:

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

`piezas.py` borra y vuelve a crear `piezas/` completa.

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

## Instalar en el reloj

1. Exportar el `.hwt` en Theme Studio a `hwt/`.
2. `python3 empaquetar.py hwt/<carátula>.hwt`: quita el `watchface.bin` que agrega Theme Studio 11.
   El Watch 3 (HarmonyOS 3.0) acepta la carátula con él, pero la descarta sin avisar.
3. Copiar `hwt/reloj/<carátula>.hwt` al celular y abrirlo con Gadgetbridge (*Instalador de FW/App*).

Gadgetbridge debe estar emparejado con el ID de cuenta Huawei puesto **antes** de emparejar
(ajustes del reloj → *Cuenta de Huawei*); si no, el reloj detecta otra cuenta y ofrece restablecerse.
