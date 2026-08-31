# Tapestry Art

A photograph compiled into a chart for hand-stitched tapestry.

![The sunset, reduced to 190 stitches across and 34 yarn colours](sunset_artwork.png)

The script reduces a photograph to a grid of stitches and a fixed palette of
yarn colours, then writes three things: the finished piece as it will look
stitched, a numbered working chart, and a legend giving the stitch count for
every colour.

## Running it

Needs Python 3.8+ and Pillow 9.1 or newer:

```bash
pip install -r requirements.txt
python3 tapestry_art.py
```

That reproduces the exhibited piece from `IMG_1716.jpg` — 190 x 133 stitches,
25,270 in total, 34 colours, in about five seconds.

Any other photograph can be charted the same way:

```bash
python3 tapestry_art.py your_photo.jpg
python3 tapestry_art.py your_photo.jpg --stitches 120 --colours 20
python3 tapestry_art.py your_photo.jpg --crop 0.1 0.2 0.9 0.8
```

JPEG or PNG. Output lands beside the script, named after the input photograph:

| File | What it is |
|---|---|
| `sunset_artwork.png` | the finished piece, one solid block per stitch (3420 x 2394 px) |
| `sunset_chart.png` | the working chart: a gridline at every stitch, heavier every 10, a colour number in every cell |
| `sunset_legend.txt` | colour number, hex value and stitch count for each yarn |

## How the reduction works

Box resampling averages every pixel falling inside a stitch rather than
sampling one of them, so fine detail is integrated away instead of dropped —
the chart is a faithful reduction, not a subsample of whichever pixels happened
to land on the grid lines.

Dithering is switched off deliberately. It would scatter lone off-colour
stitches through the sky, which is invisible on a screen and unstitchable in
yarn. The palette itself comes from the photograph, by median cut.

The crop exists for the same reason: the photograph is mostly empty sky, and at
190 stitches the sun is only a few cells across. Uncropped, it averages away
into the surrounding glow. Cropping in is what lets it survive the reduction as
a distinct disc.

Colours are numbered by frequency, so colour 1 is the one you stitch most and
the legend doubles as a shopping list.
