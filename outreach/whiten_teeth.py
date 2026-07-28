#!/usr/bin/env python3
"""Whiten teeth inside a given box of an RGBA cut-out.

    python3 whiten_teeth.py in.png out.png X0 Y0 X1 Y1 [strength]

Works in HSV and only touches pixels that actually look like enamel, so lips
and gums are left alone:

  - hue in the yellow/amber band    (lips and gums sit in the reds, ~245-255)
  - saturation below a ceiling      (lips are far more saturated)
  - value above a floor             (excludes the shadow inside the mouth)

Enamel is then desaturated rather than simply brightened. Brightening alone
blows out the highlights and gives that fake pasted-on look; pulling the yellow
out while lifting value slightly is what reads as clean teeth.
"""
import sys

from PIL import Image

HUE_LO, HUE_HI = 8, 48      # yellow/amber band, 0-255 scale
SAT_MAX = 0.46              # above this it is lip or gum, not enamel
VAL_MIN = 0.42              # below this it is the shadow inside the mouth


def main():
    src, dst = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
    strength = float(sys.argv[7]) if len(sys.argv) > 7 else 0.72
    # Teeth toward the corners of a smile sit in shadow: darker and more
    # saturated than the front ones. Tight gates whiten the middle and leave the
    # outer teeth yellow, which looks worse than not whitening at all. Lips and
    # gums are already excluded by HUE, so these two can be opened up safely.
    sat_max = float(sys.argv[8]) if len(sys.argv) > 8 else SAT_MAX
    val_min = float(sys.argv[9]) if len(sys.argv) > 9 else VAL_MIN

    im = Image.open(src).convert("RGBA")
    rgb = im.convert("RGB")
    hsv = rgb.convert("HSV")
    hp, op = hsv.load(), im.load()

    smax, vmin = int(sat_max * 255), int(val_min * 255)
    touched = 0
    for y in range(max(0, y0), min(im.size[1], y1)):
        for x in range(max(0, x0), min(im.size[0], x1)):
            h, s, v = hp[x, y]
            if HUE_LO <= h <= HUE_HI and s <= smax and v >= vmin:
                # Desaturate towards neutral, then lift value a little. Feather
                # the effect near the saturation ceiling so the edge of the
                # selection does not show as a hard line across a tooth.
                edge = min(1.0, (smax - s) / 40.0)
                k = strength * edge
                ns = int(s * (1 - k))
                nv = min(255, int(v * (1 + 0.10 * k)))
                hp[x, y] = (h, ns, nv)
                touched += 1

    out = hsv.convert("RGB")
    out.putalpha(im.getchannel("A"))
    out.save(dst)
    print(f"whitened {touched} px")


if __name__ == "__main__":
    main()
