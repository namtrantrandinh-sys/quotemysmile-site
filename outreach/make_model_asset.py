#!/usr/bin/env python3
"""Key a studio model off her backdrop and emit site assets.

    python3 make_model_asset.py <source.jpg> <out-basename> [--cutout] [--portrait]

Writes photos/<out-basename>.webp (framed on brand mint) and, with --cutout,
photos/<out-basename>-cutout.webp (transparent figure for the wordmark hero).

Thresholds are derived from the plate rather than hard-coded: we sample the
backdrop from the corners, then measure the closest subject pixel so the band
always sits below it. A fixed band is what left an earlier model's pale mint
dress semi-transparent — it was only ~83 from the backdrop in RGB distance.
"""
import argparse
import pathlib
from collections import deque

from PIL import Image, ImageFilter

PHOTOS = pathlib.Path("/Users/nam/quotemysmile-site/photos")


def fill_holes(mask: Image.Image, w: int, h: int, thresh: int = 40) -> Image.Image:
    """Make opaque any transparent region that does not reach the image border.

    Where a model's skin or clothing approaches the backdrop colour, the key
    punches holes INSIDE the silhouette — the smudges that show up across a
    cheek or a forearm. Those holes are enclosed by subject, so flooding the
    transparent areas inward from the border marks everything that is genuinely
    outside her; whatever transparency is left over is a hole, and gets filled.
    """
    a = mask.load()
    outside = bytearray(w * h)
    stack = []
    for x in range(w):
        for y in (0, h - 1):
            if a[x, y] < thresh:
                stack.append((x, y)); outside[y * w + x] = 1
    for y in range(h):
        for x in (0, w - 1):
            if a[x, y] < thresh and not outside[y * w + x]:
                stack.append((x, y)); outside[y * w + x] = 1
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not outside[j] and a[nx, ny] < thresh:
                    outside[j] = 1
                    stack.append((nx, ny))

    px = list(mask.getdata())
    filled = sum(1 for i, v in enumerate(px) if v < thresh and not outside[i])
    out = Image.new("L", (w, h))
    out.putdata([255 if (v < thresh and not outside[i]) else v for i, v in enumerate(px)])
    if filled:
        print(f"filled {filled} px of interior holes")
    return out


def close_mask(mask: Image.Image, radius: int) -> Image.Image:
    """Morphological close — seals narrow channels the flood fill crept through.

    fill_holes only rescues FULLY enclosed holes. When the key breaks through a
    thin bridge (a jawline against a similar-toned backdrop) the damage is
    connected to the outside and survives. Dilating then eroding pinches those
    channels shut first, so the following fill_holes can rescue them.
    """
    size = radius * 2 + 1
    return mask.filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))


def key_figure(path: str, max_side=(1100, 1650), near=None, far=None, close=0, erode=0):
    im = Image.open(path).convert("RGB")
    im.thumbnail(max_side, Image.LANCZOS)
    w, h = im.size
    px = im.load()

    # Sample the backdrop from whichever corners are actually empty. A subject
    # framed to the bottom of the plate makes the lower corners her clothing.
    corners, samples = [(6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7)], []
    for cx, cy in corners:
        patch = [px[cx + dx, cy + dy] for dx in range(-4, 5) for dy in range(-4, 5)]
        avg = tuple(sum(c[i] for c in patch) // len(patch) for i in range(3))
        samples.append(avg)
    # Top corners are the reliable ones; use them as the reference.
    bg = tuple((samples[0][i] + samples[1][i]) // 2 for i in range(3))

    def dist(c):
        return ((c[0] - bg[0]) ** 2 + (c[1] - bg[1]) ** 2 + (c[2] - bg[2]) ** 2) ** 0.5

    # Closest subject pixel: scan the central column band where the figure is.
    inner = [dist(px[x, y])
             for y in range(int(h * 0.25), int(h * 0.75), 6)
             for x in range(int(w * 0.35), int(w * 0.65), 6)]
    subject_min = min([d for d in inner if d > 35] or [120])
    if near is None:
        near = max(22, subject_min * 0.34)
    if far is None:
        far = max(near + 14, subject_min * 0.76)
    # Pass --near/--far when the plate has a soft CAST SHADOW on the seamless:
    # the shadow sits just above the backdrop in RGB distance, so an auto band
    # reads it as subject and leaves a grey blob floating beside the figure.
    print(f"backdrop={bg} closest-subject={subject_min:.0f} band={near:.0f}..{far:.0f}")

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
        if d >= far:
            continue
        alpha[i] = 0 if d <= near else int(255 * (d - near) / (far - near))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))

    mask = Image.new("L", (w, h))
    mask.putdata(alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask = mask.point(lambda v: 0 if v < 46 else min(255, int((v - 46) * 1.55)))

    mask = fill_holes(mask, w, h)
    if close:
        mask = close_mask(mask, close)
        mask = fill_holes(mask, w, h)
    if erode:
        # Pull the silhouette in. On plates where the model's skin sits inside
        # the backdrop's distance range there is no band that both clears the
        # backdrop and spares her face: raise it and the face breaks up, lower
        # it and a pale fringe of leftover seamless survives. So key LOW to keep
        # the face intact, then trim that fringe off the edge here.
        size = erode * 2 + 1
        mask = mask.filter(ImageFilter.MinFilter(size))
        mask = mask.filter(ImageFilter.GaussianBlur(0.6))
    mask = keep_largest_blob(mask, w, h)

    fig = im.convert("RGBA")
    fig.putalpha(mask)
    box = mask.getbbox()
    return fig.crop(box) if box else fig


def keep_largest_blob(mask: Image.Image, w: int, h: int, thresh: int = 40) -> Image.Image:
    """Drop everything except the biggest connected opaque region.

    A soft CAST SHADOW on the seamless sits only just above the backdrop in RGB
    distance, so no global threshold separates it from a lit clothing edge —
    push the band up to kill the shadow and it starts eating the model's
    highlights instead. But the shadow is always a SEPARATE island from the
    figure, so connectivity settles it: keep the largest component, bin the rest.
    """
    a = mask.load()
    labels = [0] * (w * h)
    best_id, best_n, cur = 0, 0, 0
    for sy in range(h):
        for sx in range(w):
            i = sy * w + sx
            if labels[i] or a[sx, sy] < thresh:
                continue
            cur += 1
            n = 0
            stack = [(sx, sy)]
            labels[i] = cur
            while stack:
                x, y = stack.pop()
                n += 1
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not labels[j] and a[nx, ny] >= thresh:
                            labels[j] = cur
                            stack.append((nx, ny))
            if n > best_n:
                best_id, best_n = cur, n

    out = Image.new("L", (w, h))
    px = mask.getdata()
    out.putdata([v if labels[i] == best_id else 0 for i, v in enumerate(px)])
    print(f"kept largest blob: {best_n} px of {w * h}")
    return out


def mint_card(fig, W=1000, H=1250, fill=0.80):
    top, bot = (198, 228, 214), (134, 191, 170)
    card = Image.new("RGB", (W, H))
    cpx = card.load()
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            cpx[x, y] = row
    s = fig.copy()
    s.thumbnail((int(W * fill), int(H * 0.95)), Image.LANCZOS)
    card.paste(s, ((W - s.size[0]) // 2, H - s.size[1]), s)
    return card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("basename")
    ap.add_argument("--cutout", action="store_true")
    ap.add_argument("--fill", type=float, default=0.80)
    ap.add_argument("--near", type=float, help="below this RGB distance = backdrop")
    ap.add_argument("--far", type=float, help="above this RGB distance = subject")
    ap.add_argument("--close", type=int, default=0, help="morphological close radius, seals matte breakthroughs")
    ap.add_argument("--erode", type=int, default=0, help="trim N px off the silhouette, removes leftover backdrop fringe")
    a = ap.parse_args()

    fig = key_figure(a.source, near=a.near, far=a.far, close=a.close, erode=a.erode)
    print("figure:", fig.size)

    card = mint_card(fig, fill=a.fill)
    out = PHOTOS / f"{a.basename}.webp"
    card.save(out, "WEBP", quality=84, method=6)
    print("wrote", out.name, card.size)

    if a.cutout:
        cut = fig.copy()
        cut.thumbnail((900, 1250), Image.LANCZOS)
        outc = PHOTOS / f"{a.basename}-cutout.webp"
        cut.save(outc, "WEBP", quality=84, method=6)
        print("wrote", outc.name, cut.size)


if __name__ == "__main__":
    main()
