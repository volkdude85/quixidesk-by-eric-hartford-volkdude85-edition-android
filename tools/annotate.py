#!/usr/bin/env python3
"""Draw callouts on device screenshots: a darkened frame, a bright cut-out on the thing to touch,
and a numbered badge. High contrast on purpose — the reader is being asked to find a row among
thirty, and a thin red rectangle at phone resolution is invisible on paper.

Every figure is composed from the raw grab, so it can be regenerated after any recapture.

    python3 tools/annotate.py in.png out.png '[{"box":[x1,y1,x2,y2],"badge":"1","kind":"touch"}]'
"""
import json
import sys
from PIL import Image, ImageDraw, ImageFont

ACCENT = (255, 206, 0)        # yellow: readable on both light and dark settings themes
ACCENT_2 = (0, 229, 255)      # cyan for the second element on a screen
INK = (16, 16, 18)
WHITE = (255, 255, 255)

FONT_CANDIDATES = [
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return mask


def annotate(src, dst, ops, dim_alpha=150):
    base = Image.open(src).convert("RGB")
    width, height = base.size

    # 1. dim everything, so the cut-out is the brightest thing on the page
    veil = Image.new("RGB", base.size, INK)
    dimmed = Image.blend(base, veil, dim_alpha / 255.0)

    for op in ops:
        x1, y1, x2, y2 = [int(v) for v in op["box"]]
        pad = int(op.get("pad", 12))
        box = (max(0, x1 - pad), max(0, y1 - pad), min(width, x2 + pad), min(height, y2 + pad))
        w, h = box[2] - box[0], box[3] - box[1]
        radius = int(op.get("radius", 18))

        # 2. paste the original back inside the cut-out, with a rounded edge
        patch = base.crop(box)
        mask = rounded_mask((w, h), radius)
        dimmed.paste(patch, box, mask)

        accent = ACCENT_2 if op.get("accent") == "cyan" else ACCENT
        draw = ImageDraw.Draw(dimmed)
        for inset, colour, thickness in ((0, WHITE, 10), (2, accent, 6)):
            draw.rounded_rectangle(
                [box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset],
                radius,
                outline=colour,
                width=thickness,
            )

        badge = str(op.get("badge") or "").strip()
        if badge:
            r = int(op.get("badge_radius", 46))
            bx = box[0] + int(op.get("badge_dx", -r // 2))
            by = box[1] + int(op.get("badge_dy", -r // 2))
            bx = max(r, min(width - r, bx))
            by = max(r, min(height - r, by))
            draw.ellipse([bx - r, by - r, bx + r, by + r], fill=accent, outline=WHITE, width=6)
            f = font(int(r * 1.25))
            tw = draw.textbbox((0, 0), badge, font=f)
            draw.text(
                (bx - (tw[2] - tw[0]) / 2, by - (tw[3] - tw[1]) / 2 - (tw[1] - tw[0]) / 2 - 6),
                badge,
                font=f,
                fill=INK,
            )

    dimmed.save(dst)
    print(f"{dst}: {width}x{height} with {len(ops)} callout(s)")


if __name__ == "__main__":
    src, dst, ops_json = sys.argv[1], sys.argv[2], sys.argv[3]
    annotate(src, dst, json.loads(ops_json))
