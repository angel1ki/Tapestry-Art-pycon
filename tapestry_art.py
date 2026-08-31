import argparse
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

PHOTO = "IMG_1716.jpg"

#Framing, as fractions of the original photogragh (left, top, right and bottom)
CROP = (0.20, 0.45, 0.78, 0.99)

STITCHES_WIDE = 190
COLOURS = 34
CELL = 18
BOLD_EVERY = 10

def build_chart(photo_path, stitches_wide, colours, crop=(0.0, 0.0, 1.0, 1.0)):
    """Compile a photograph into a grid of stitches.

    BOX resampling averages every source pixel falling inside a cell, which is
    what makes this work on a photograph: fine detail is integrated away rather
    than point-sampled, so the chart is a faithful reduction and not a
    subsample of whatever pixels happened to land on the grid lines.
    """
    image = Image.open(photo_path)
    image = ImageOps.exif_transpose(image).convert("RGB")

    W, H = image.size
    left, top, right, bottom = crop
    image = image.crop((round(W * left), round(H * top),
                        round(W * right), round(H * bottom)))

    w, h = image.size
    stitches_high = max(1, round(stitches_wide * h / w))
    small = image.resize((stitches_wide, stitches_high), Image.Resampling.BOX)

    reduced = small.quantize(colors=colours,
                             method=Image.Quantize.MEDIANCUT,
                             dither=Image.Dither.NONE).convert("RGB")

    raw = reduced.tobytes()
    cells = [tuple(raw[i:i +3]) for i in range(0, len(raw), 3)]

    #Using numbers so that  the number 1 is the colour with the most stitches
    counts = Counter(cells)
    order = [rgb for rgb, _ in counts.most_common()]
    symbol = {rgb: str(i + 1) for i, rgb in enumerate(order)}

    grid = [cells[r * stitches_wide:(r + 1) * stitches_wide]
            for r in range(stitches_high)]
    legend = [(symbol[rgb], rgb, counts[rgb]) for rgb in order]
    return grid, legend, symbol


def render_artwork(grid):
    """One solid block per stitch"""
    h, w = len(grid), len(grid[0])
    img = Image.new("RGB", (w * CELL, h * CELL))
    draw = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        for c, rgb in enumerate(row):
            draw.rectangle([c * CELL, r * CELL, (c + 1) * CELL, (r + 1) * CELL],
                            fill=rgb)

    return img


def load_font(size):
    for name in ("DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_chart(grid, symbol):
    """The working chart: gridlines, plus each cell's colour number"""
    img = render_artwork(grid)
    draw = ImageDraw.Draw(img)
    h, w = len(grid), len(grid[0])
    font = load_font(int(CELL * 0.55))

    for c in range(w + 1):
        x = c * CELL
        draw.line([x, 0, x, h * CELL], fill=(60, 60, 60),
                  width=2 if c % BOLD_EVERY == 0 else 1)

    for r in range(h + 1):
        y = r * CELL
        draw.line([0, y, w * CELL, y], fill=(60, 60, 60),
                  width=2 if r % BOLD_EVERY == 0 else 1)


    box = {} #metrics cache for each symbol, so we don't have to recalculate it every time
    for r, row in enumerate(grid):
        for c, rgb in enumerate(row):
            s = symbol[rgb]
            if s not in box:
                b = draw.textbbox((0, 0), s, font=font)
                box[s] = (b[2] - b[0], b[3] - b[1], b[0], b[1])
            tw, th, bx, by = box[s]
            #Changing the ink of the yarn based on the brightness
            luma = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            draw.text((c * CELL + (CELL - tw) / 2 - bx,
                       r * CELL + (CELL - th) / 2 - by),
                       s, fill=(0, 0, 0) if luma > 150 else (255, 255, 255),
                       font=font)
    return img

def main():
    here = Path(__file__).parent if "__file__" in globals() else Path.cwd()
    ap = argparse.ArgumentParser(
        description="Compile a photograph into a tapestry chart. "
                    "With no arguments, reproduces with exhibited artwork.")
    ap.add_argument("photo", nargs="?",
                    help=f"any photograph (default: {PHOTO}, the exhibited piece)")
    ap.add_argument("--stitches", type=int, default=STITCHES_WIDE,
                    help=f"chart width in stitches (default{STITCHES_WIDE})")
    ap.add_argument("--colours", "--colors", dest="colours", type=int, default=COLOURS,
                     help=f"number of yarn colours (default {COLOURS})")
    ap.add_argument("--crop", type=float, nargs=4, metavar=("L", "T", "R", "B"),
                    help="crop as fractions of the photograph, e.g. 0.2 0.45 0.78 0.99")
    args=ap.parse_args()

    if args.photo:
        #Someone else's photograph: use the whole frame unless they crop it
        #themselves. The exhibited crop belongs to the sunset alone.
        photo, name = Path(args.photo), Path(args.photo).stem
        crop = tuple(args.crop) if args.crop else (0.0, 0.0, 1.0, 1.0)
    else:
        photo, name = here / PHOTO, "sunset"
        crop = tuple(args.crop) if args.crop else CROP

    if not photo.exists():
        raise SystemExit(f"photograph not found: {photo}\n"
                          f"place {PHOTO} beside this script, or pass a path")

    grid, legend, symbol = build_chart(photo, args.stitches, args.colours, crop)

    render_artwork(grid).save(here / f"{name}_artwork.png")
    render_chart(grid, symbol).save(here / f"{name}_chart.png")

    lines = [f"{'No.':>4} {'HEX':<9} Stitches", "-" * 28]
    lines += [f"{s:>4} #{r:02X}{g:02X}{b:02X} {n:>8}" for s, (r, g, b), n in legend]
    total = sum(n for _, _, n in legend)
    lines += ["-"*28, f"{total} stitches, {len(legend)} colours"]
    (here / f"{name}_legend.txt").write_text("\n".join(lines), encoding="utf-8")

    print(f"{len(grid[0])} x {len(grid)} stitches, {total} total, {len(legend)} colours")
    print(f"wrote {name}_artwork.png, {name}_chart.png, {name}_legend.txt")

if __name__ == "__main__":
    main()
