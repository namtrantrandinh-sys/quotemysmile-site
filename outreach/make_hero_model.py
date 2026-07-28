#!/usr/bin/env python3
"""Key the hero model off her studio backdrop and emit the two site assets.

Source: Pexels (Pexels License — free for commercial use, no attribution
required). See photos/CREDITS.md.

Outputs:
  photos/model-cutout.webp   transparent figure, for the wordmark hero
  photos/model-portrait.webp figure composited on brand mint, 4:5 framed heroes

The backdrop is an even seamless, so a colour-distance key gets a clean matte.
We flood-fill inward from the border so any backdrop-coloured pixel INSIDE the
subject is never punched out, then feather the edge.
"""
from collections import deque

from PIL import Image, ImageFilter

SRC = "/private/tmp/claude-501/-Users-nam/f14aa032-9b5a-4249-b3a2-21de0fd08006/scratchpad/cand1.jpg"
OUT_CUT = "/Users/nam/quotemysmile-site/photos/model-cutout.webp"
OUT_PORT = "/Users/nam/quotemysmile-site/photos/model-portrait.webp"

# Distance thresholds against the sampled backdrop.
# Measured on this plate: backdrop pixels sit within ~25, while the LIGHTEST
# subject pixels (her pale mint dress) are ~83 away. A wide band swallowed the
# dress and left her torso semi-transparent, so the band sits well below 83.
NEAR, FAR = 30, 64

im = Image.open(SRC).convert("RGB")
im.thumbnail((1100, 1650), Image.LANCZOS)
w, h = im.size
px = im.load()

# Sample all four corners — the subject is inset from every edge in this plate.
patch = []
for cx, cy in ((6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7)):
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            patch.append(px[cx + dx, cy + dy])
bg = tuple(sum(c[i] for c in patch) // len(patch) for i in range(3))
print("sampled backdrop:", bg)


def dist(c):
    return ((c[0] - bg[0]) ** 2 + (c[1] - bg[1]) ** 2 + (c[2] - bg[2]) ** 2) ** 0.5


alpha = [255] * (w * h)
seen = bytearray(w * h)
q = deque()
for x in range(w):
    for y in (0, h - 1):
        q.append((x, y))
for y in range(h):
    for x in (0, w - 1):
        q.append((x, y))

while q:
    x, y = q.popleft()
    i = y * w + x
    if seen[i]:
        continue
    seen[i] = 1
    d = dist(px[x, y])
    if d >= FAR:
        continue  # reached the subject
    alpha[i] = 0 if d <= NEAR else int(255 * (d - NEAR) / (FAR - NEAR))
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
            q.append((nx, ny))

mask = Image.new("L", (w, h))
mask.putdata(alpha)
mask = mask.filter(ImageFilter.GaussianBlur(1.0))
mask = mask.point(lambda v: 0 if v < 46 else min(255, int((v - 46) * 1.55)))

fig = im.convert("RGBA")
fig.putalpha(mask)
bbox = mask.getbbox()
if bbox:
    fig = fig.crop(bbox)
print("figure:", fig.size)

cut = fig.copy()
cut.thumbnail((900, 1250), Image.LANCZOS)
cut.save(OUT_CUT, "WEBP", quality=84, method=6)
print("wrote", OUT_CUT, cut.size)

# Framed 4:5 portrait on the brand mint field.
W, H = 1000, 1250
top, bot = (198, 228, 214), (134, 191, 170)
card = Image.new("RGB", (W, H))
cpx = card.load()
for y in range(H):
    t = y / (H - 1)
    row = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    for x in range(W):
        cpx[x, y] = row
s = fig.copy()
s.thumbnail((int(W * 0.80), int(H * 0.95)), Image.LANCZOS)
card.paste(s, ((W - s.size[0]) // 2, H - s.size[1]), s)
card.save(OUT_PORT, "WEBP", quality=84, method=6)
print("wrote", OUT_PORT, card.size)
