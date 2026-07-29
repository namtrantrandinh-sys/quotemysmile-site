#!/usr/bin/env python3
"""Whiten teeth inside an elliptical region of an RGBA cut-out.

    python3 whiten_teeth.py in.png out.png X0 Y0 X1 Y1 [strength] [sat_max] [val_min]

X0 Y0 X1 Y1 bound an ELLIPSE, not a rectangle. A dental arch is curved, so a
rectangle wide enough to reach the outer teeth also grabs lip at its corners —
which is what produced the white blocks either side of the mouth. The ellipse
covers the full arch and tapers away exactly where the lips are, and the effect
is feathered towards its edge so there is no visible boundary.

Selection inside that region, in HSV:
  - hue in the yellow/amber band    (lips and gums sit in the reds, ~235-255)
  - saturation below a ceiling      (lips are far more saturated)
  - value above a floor             (excludes the shadow inside the mouth)

Enamel is desaturated rather than simply brightened. Brightening alone blows the
highlights and looks pasted on; pulling the yellow out while lifting value a
little is what reads as clean teeth.
"""
import sys

from PIL import Image

HUE_LO, HUE_HI = 8, 48
SAT_MAX = 0.60
VAL_MIN = 0.26


def main():
    src, dst = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
    strength = float(sys.argv[7]) if len(sys.argv) > 7 else 0.80
    sat_max = float(sys.argv[8]) if len(sys.argv) > 8 else SAT_MAX
    val_min = float(sys.argv[9]) if len(sys.argv) > 9 else VAL_MIN

    im = Image.open(src).convert("RGBA")
    hsv = im.convert("RGB").convert("HSV")
    hp = hsv.load()

    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = max(1.0, (x1 - x0) / 2.0), max(1.0, (y1 - y0) / 2.0)
    smax, vmin = int(sat_max * 255), int(val_min * 255)

    touched = 0
    for y in range(max(0, y0), min(im.size[1], y1)):
        for x in range(max(0, x0), min(im.size[0], x1)):
            # Elliptical distance: 0 at the centre, 1 at the boundary.
            d = (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2) ** 0.5
            if d >= 1.0:
                continue
            h, s, v = hp[x, y]
            if not (HUE_LO <= h <= HUE_HI and s <= smax and v >= vmin):
                continue
            # Feather over the outer 30% of the ellipse, and again as saturation
            # approaches the ceiling, so neither edge of the selection shows.
            shape = min(1.0, (1.0 - d) / 0.30)
            band = min(1.0, (smax - s) / 40.0)
            k = strength * shape * band
            if k <= 0:
                continue
            hp[x, y] = (h, int(s * (1 - k)), min(255, int(v * (1 + 0.10 * k))))
            touched += 1

    out = hsv.convert("RGB")
    out.putalpha(im.getchannel("A"))
    out.save(dst)
    print(f"whitened {touched} px")


if __name__ == "__main__":
    main()
