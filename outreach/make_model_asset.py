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


def fill_holes(mask: Image.Image, w: int, h: int, thresh: int = 40,
               src: Image.Image = None, bg=None) -> Image.Image:
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

    # Not every enclosed hole is damage. Background genuinely shows through gaps
    # the subject encloses — between a hand and a cheek, or an arm and the waist.
    # Filling those paints a patch of backdrop back onto the figure. So when the
    # source is available, keep a hole transparent if what lies under it still
    # looks like the backdrop; fill it only if it looks like subject.
    keep_transparent = set()
    if src is not None and bg is not None:
        spx = src.load()
        holes = {}
        for i, v in enumerate(px):
            if v < thresh and not outside[i]:
                holes.setdefault(_hole_id(i, w, px, outside, thresh), []).append(i)
        for hid, idxs in holes.items():
            sample = idxs[:: max(1, len(idxs) // 40)]
            dists = []
            for i in sample:
                c = spx[i % w, i // w]
                dists.append(((c[0] - bg[0]) ** 2 + (c[1] - bg[1]) ** 2 + (c[2] - bg[2]) ** 2) ** 0.5)
            if dists and sorted(dists)[len(dists) // 2] < 60:
                keep_transparent.update(idxs)

    filled = sum(1 for i, v in enumerate(px)
                 if v < thresh and not outside[i] and i not in keep_transparent)
    out = Image.new("L", (w, h))
    out.putdata([255 if (v < thresh and not outside[i] and i not in keep_transparent) else v
                 for i, v in enumerate(px)])
    if filled:
        print(f"filled {filled} px of interior holes"
              + (f", left {len(keep_transparent)} px of see-through gaps" if keep_transparent else ""))
    return out


def soften_and_despill(fig: Image.Image, bg, feather=1.4, despill=True) -> Image.Image:
    """Give the matte a soft edge and strip the backdrop's colour from it.

    Two things make a cut-out look like bad photoshop, and both live at the
    hair line:

    1. A BINARY alpha. Real hair edges are partly transparent; a hard 0/255
       mask gives a stencilled outline no amount of tidying fixes. Feathering
       the alpha restores the transition.
    2. COLOUR CONTAMINATION. A pixel on the edge of the hair is a blend of hair
       and backdrop, so against a black plate it carries a dark rim, and against
       a coloured one a coloured rim. Dropped onto mint that rim reads as dirt.
       Un-mixing solves it: the observed pixel is a*F + (1-a)*BG, so the true
       foreground is F = (observed - (1-a)*BG) / a.
    """
    fig = fig.convert("RGBA")
    a = fig.getchannel("A").filter(ImageFilter.GaussianBlur(feather))
    fig.putalpha(a)

    if not despill or bg is None:
        return fig

    px = fig.load()
    w, h = fig.size
    fixed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, al = px[x, y]
            if 8 < al < 248:  # only the transition band carries the rim
                f = al / 255.0
                nr = int(max(0, min(255, (r - (1 - f) * bg[0]) / f)))
                ng = int(max(0, min(255, (g - (1 - f) * bg[1]) / f)))
                nb = int(max(0, min(255, (b - (1 - f) * bg[2]) / f)))
                px[x, y] = (nr, ng, nb, al)
                fixed += 1
    print(f"despilled {fixed} edge px")
    return fig


def _hole_id(start, w, px, outside, thresh):
    """Cheap grouping key for an enclosed hole — its connected-region seed.

    Full labelling would be exact but this runs per pixel on a large mask; the
    row-run seed is enough to group a hole's pixels together for the colour test.
    """
    y, x = start // w, start % w
    while x > 0 and px[y * w + (x - 1)] < thresh and not outside[y * w + (x - 1)]:
        x -= 1
    return y * w + x


def close_mask(mask: Image.Image, radius: int) -> Image.Image:
    """Morphological close — seals narrow channels the flood fill crept through.

    fill_holes only rescues FULLY enclosed holes. When the key breaks through a
    thin bridge (a jawline against a similar-toned backdrop) the damage is
    connected to the outside and survives. Dilating then eroding pinches those
    channels shut first, so the following fill_holes can rescue them.
    """
    size = radius * 2 + 1
    return mask.filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))


def key_chroma(path: str, max_side=(1100, 1650), hue_tol=26, sat_min=0.34,
               val_min=0.55, close=0, erode=0, strip_tol=55):
    """Key a VIVID coloured backdrop on hue + saturation instead of RGB distance.

    A saturated seamless (orange, teal, yellow) is almost always lit unevenly —
    bright behind the subject, falling off at the edges. Euclidean distance from
    one sampled colour cannot cover that gradient: set the band wide enough to
    catch the dark corners and it eats skin, narrow enough to spare skin and the
    bright centre survives as a coloured halo.

    Hue and saturation are both stable across that falloff. The backdrop stays
    the same hue and stays vivid; skin, hair and neutral clothing are far less
    saturated whatever their brightness. So: background = same hue AND vivid.
    """
    im = Image.open(path).convert("RGB")
    im.thumbnail(max_side, Image.LANCZOS)
    w, h = im.size
    hsv = im.convert("HSV")
    hp = hsv.load()

    corner = [hp[x, y] for x in range(2, 16) for y in range(2, 16)]
    bg_h = sum(c[0] for c in corner) // len(corner)
    print(f"chroma key: backdrop hue={bg_h} (0-255 scale), tol={hue_tol}, sat_min={sat_min}")

    smin, vmin = int(sat_min * 255), int(val_min * 255)
    alpha = []
    for y in range(h):
        for x in range(w):
            hh, ss, vv = hp[x, y]
            dh = min(abs(hh - bg_h), 255 - abs(hh - bg_h))
            # Brightness matters as well as hue: warm brown HAIR shares an orange
            # backdrop's hue and is saturated enough to pass a hue+sat test, so
            # it gets eaten. The seamless is lit bright and the hair is dark, so
            # requiring brightness too keeps the hair.
            alpha.append(0 if (dh <= hue_tol and ss >= smin and vv >= vmin) else 255)

    mask = Image.new("L", (w, h))
    mask.putdata(alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask = mask.point(lambda v: 0 if v < 128 else 255)
    bg_rgb = im.convert("RGB").resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    cor = im.convert("RGB").load()
    bg_rgb = cor[4, 4]
    mask = fill_holes(mask, w, h, src=im.convert("RGB"), bg=bg_rgb)
    if close:
        mask = close_mask(mask, close)
        mask = fill_holes(mask, w, h, src=im.convert("RGB"), bg=bg_rgb)
    if erode:
        mask = mask.filter(ImageFilter.MinFilter(erode * 2 + 1))
        mask = mask.filter(ImageFilter.GaussianBlur(0.6))
    mask = keep_largest_blob(mask, w, h)

    # Final sweep: any pixel still opaque whose colour is essentially the
    # backdrop is leftover seamless, not subject. This catches SHADOWED backdrop
    # in enclosed gaps — between a hand and a cheek, say — which is too dim and
    # desaturated to trip the hue/sat/value test, yet is plainly background.
    # Safe because a real subject sits far from a vivid backdrop in RGB: this
    # model's skin is ~166 away from her amber seamless, so strip_tol has room.
    rgbp = im.load()
    mp = mask.load()
    stripped = 0
    for y in range(h):
        for x in range(w):
            if mp[x, y] > 40:
                c = rgbp[x, y]
                if ((c[0] - bg_rgb[0]) ** 2 + (c[1] - bg_rgb[1]) ** 2
                        + (c[2] - bg_rgb[2]) ** 2) ** 0.5 < strip_tol:
                    mp[x, y] = 0
                    stripped += 1
    if stripped:
        print(f"stripped {stripped} px of residual backdrop")

    fig = im.convert("RGBA")
    fig.putalpha(mask)
    fig = soften_and_despill(fig, bg_rgb)
    box = fig.getchannel("A").getbbox()
    return fig.crop(box) if box else fig


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
    mask = mask.point(lambda v: 0 if v < 30 else min(255, int((v - 30) * 1.30)))

    mask = fill_holes(mask, w, h, src=im, bg=bg)
    if close:
        mask = close_mask(mask, close)
        mask = fill_holes(mask, w, h, src=im, bg=bg)
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
    fig = soften_and_despill(fig, bg)
    box = fig.getchannel("A").getbbox()
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
    ap.add_argument("--chroma", action="store_true", help="key a VIVID coloured backdrop on hue+sat+value instead of RGB distance")
    ap.add_argument("--hue-tol", type=int, default=24)
    ap.add_argument("--sat-min", type=float, default=0.34)
    ap.add_argument("--val-min", type=float, default=0.62)
    a = ap.parse_args()

    if a.chroma:
        fig = key_chroma(a.source, hue_tol=a.hue_tol, sat_min=a.sat_min,
                         val_min=a.val_min, close=a.close, erode=a.erode)
    else:
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
