"""Draw simple, original jewellery illustrations for the demo catalogue.

They are placeholders so the whole pipeline can run without any copyrighted photos.
For meaningful search quality, replace them with real photos of your own products
(keep the same file names, or update image_filename in the database).

Usage:  python scripts/generate_demo_images.py [--force]
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from demo_catalogue import CATALOGUE  # noqa: E402

S = 1024  # drawn at 2x, then downsampled to 512 for smooth edges
BG = (238, 240, 238)
METALS = {  # main, dark, light
    "Gold": ((212, 175, 55), (150, 110, 25), (250, 228, 140)),
    "Silver": ((190, 194, 202), (110, 115, 125), (240, 243, 248)),
    "Diamond": ((205, 210, 220), (120, 128, 140), (245, 250, 255)),  # white-gold look
}
STONES = {
    "Ruby": (190, 25, 55), "Emerald": (25, 140, 85), "Sapphire": (35, 75, 175),
    "Diamond": (232, 248, 255), "Pearl": (246, 242, 232),
}


def gem(d, cx, cy, r, color):
    dark = tuple(int(c * 0.6) for c in color)
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in range(0, 360, 45)]
    d.polygon(pts, fill=color, outline=dark)
    d.line([pts[0], pts[4]], fill=dark, width=max(2, r // 14))
    d.line([pts[2], pts[6]], fill=dark, width=max(2, r // 14))
    d.ellipse([cx - r * 0.45, cy - r * 0.55, cx - r * 0.1, cy - r * 0.2], fill=(255, 255, 255))


def ring_pts(cx, cy, rx, ry, n, start=0.0, end=360.0):
    step = (end - start) / n
    return [(cx + rx * math.cos(math.radians(start + i * step)),
             cy + ry * math.sin(math.radians(start + i * step))) for i in range(n + 1)]


def chain(d, pts, m, width=12):
    main, dark, light = m
    for (x, y) in pts:
        d.ellipse([x - width, y - width, x + width, y + width], outline=dark, fill=main, width=3)


def draw_ring(d, m, stone, v):
    main, dark, light = m
    d.ellipse([262, 430, 762, 930], outline=dark, width=78)
    d.ellipse([268, 436, 756, 924], outline=main, width=64)
    d.arc([280, 450, 744, 910], 200, 270, fill=light, width=12)
    sc = STONES.get(stone) or main
    style = v % 4
    if style == 1:  # halo
        for x, y in ring_pts(512, 400, 120, 120, 10)[:-1]:
            gem(d, x, y, 24, STONES["Diamond"])
    if style == 2:  # three-stone
        gem(d, 400, 420, 55, STONES["Diamond"]); gem(d, 624, 420, 55, STONES["Diamond"])
    if style == 3:  # plain band with engraved dots
        for x, y in ring_pts(512, 680, 250, 250, 24, 0, 360)[:-1]:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=dark)
        return
    d.rectangle([462, 440, 562, 500], fill=main, outline=dark)
    gem(d, 512, 395, 85 if style != 2 else 100, sc)


def draw_necklace(d, m, stone, v):
    main, dark, light = m
    style = v % 4
    for strand in range(2 if style == 2 else 1):
        off = strand * 85
        pts = [(150 + 724 * t / 40, 140 + off + 500 * (1 - (2 * t / 40 - 1) ** 2)) for t in range(41)]
        if style == 1:
            for i, (x, y) in enumerate(pts):
                d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=main, outline=dark, width=3)
        else:
            chain(d, pts, m, 9)
        if style in (1, 3):
            for i, (x, y) in enumerate(pts):
                if i % 5 == 2:
                    gem(d, x, y + 6, 20, STONES.get(stone) or main)
    cy = 640 + (85 if style == 2 else 0)
    d.ellipse([422, cy - 20, 602, cy + 160], fill=main, outline=dark, width=6)
    gem(d, 512, cy + 70, 56, STONES.get(stone) or light)


def draw_earrings(d, m, stone, v):
    main, dark, light = m
    sc = STONES.get(stone) or light
    style = v % 3
    for x in (330, 694):
        d.ellipse([x - 22, 110, x + 22, 154], fill=main, outline=dark, width=4)
        if style == 1:  # hoop
            d.ellipse([x - 120, 180, x + 120, 640], outline=dark, width=46)
            d.ellipse([x - 114, 186, x + 114, 634], outline=main, width=34)
            continue
        d.line([x, 150, x, 270], fill=dark, width=10)
        if style == 2:  # chandelier
            d.rectangle([x - 100, 260, x + 100, 300], fill=main, outline=dark, width=4)
            for dx in (-70, 0, 70):
                d.line([x + dx, 300, x + dx, 440], fill=dark, width=6)
                gem(d, x + dx, 470, 38, sc)
        else:  # drop
            d.ellipse([x - 78, 270, x + 78, 600], fill=main, outline=dark, width=6)
            gem(d, x, 400, 56, sc)
            gem(d, x, 540, 28, sc)


def draw_bracelet(d, m, stone, v):
    main, dark, light = m
    style = v % 4
    pts = ring_pts(512, 540, 340, 200, 44)[:-1]
    for i, (x, y) in enumerate(pts):
        if style == 2:  # tennis: continuous gems
            gem(d, x, y, 30, STONES["Diamond"])
        elif style == 1 and i % 6 == 0:  # charms
            d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=STONES.get(stone) or light, outline=dark, width=5)
        elif style == 3 and i % 4 == 0:
            gem(d, x, y, 30, STONES.get(stone) or light)
        else:
            d.ellipse([x - 24, y - 16, x + 24, y + 16], outline=dark, fill=main, width=5)
    d.ellipse([140, 520, 230, 580], fill=main, outline=dark, width=6)


def draw_bangle(d, m, stone, v):
    main, dark, light = m
    style = v % 4
    d.ellipse([120, 280, 904, 800], outline=dark, width=96)
    d.ellipse([128, 288, 896, 792], outline=main, width=80)
    d.arc([150, 310, 870, 770], 190, 260, fill=light, width=14)
    pts = ring_pts(512, 540, 392, 252, 16)[:-1]
    for x, y in pts:
        if style == 2:
            gem(d, x, y, 24, STONES.get(stone) or light)
        elif style == 3:
            gem(d, x, y, 24, STONES["Diamond"])
        elif style == 1:
            d.line([x - 14, y - 22, x + 14, y + 22], fill=dark, width=6)
        else:
            d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=dark)


def draw_pendant(d, m, stone, v):
    main, dark, light = m
    sc = STONES.get(stone) or light
    style = v % 4
    for x0 in (230, 794):
        d.line([x0, 90, 512, 440], fill=dark, width=14)
        d.line([x0, 90, 512, 440], fill=main, width=8)
    d.ellipse([484, 420, 540, 476], outline=dark, width=10)
    if style == 1:  # heart
        d.ellipse([352, 480, 522, 650], fill=main, outline=dark, width=6)
        d.ellipse([502, 480, 672, 650], fill=main, outline=dark, width=6)
        d.polygon([(356, 600), (668, 600), (512, 860)], fill=main, outline=dark)
        gem(d, 512, 610, 64, sc)
    elif style == 2:  # medallion
        d.ellipse([337, 480, 687, 830], fill=main, outline=dark, width=8)
        d.ellipse([377, 520, 647, 790], outline=dark, width=6)
        gem(d, 512, 655, 70, sc)
    elif style == 3:  # solitaire
        d.ellipse([452, 480, 572, 600], outline=dark, width=8, fill=main)
        gem(d, 512, 650, 90, STONES["Diamond"])
    else:  # teardrop
        d.polygon([(512, 470), (400, 700), (624, 700)], fill=main, outline=dark)
        d.ellipse([400, 600, 624, 824], fill=main, outline=dark, width=6)
        gem(d, 512, 700, 62, sc)


DRAWERS = {
    "Necklace": draw_necklace, "Ring": draw_ring, "Earrings": draw_earrings,
    "Bracelet": draw_bracelet, "Bangle": draw_bangle, "Pendant": draw_pendant,
}


def render(product: dict) -> Image.Image:
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    DRAWERS[product["category"]](d, METALS[product["material"]], product["stone_type"], product["variant"])
    return img.resize((512, 512), Image.Resampling.LANCZOS)


def main() -> None:
    force = "--force" in sys.argv
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    for product in CATALOGUE:
        target = settings.images_dir / product["image_filename"]
        if target.exists() and not force:
            continue
        render(product).save(target, "JPEG", quality=92)
        made += 1
    print(f"Demo images written: {made} (folder: {settings.images_dir})")


if __name__ == "__main__":
    main()
