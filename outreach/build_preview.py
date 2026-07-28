#!/usr/bin/env python3
"""Build a fully self-contained preview of a landing page.

Claude Artifacts run under a strict CSP that blocks every external host, so a
page that links style.css, Google Fonts and /photos/*.jpg renders as unstyled
text. This inlines all three into one file the founder can actually open.

Usage:  python3 build_preview.py for-dentists.html  waitlist.html
Output: outreach/preview-<name>.html
"""
import base64
import mimetypes
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outreach"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
FONT_CSS_URL = ("https://fonts.googleapis.com/css2?"
                "family=Cormorant+Garamond:wght@400;500;600&family=Allura"
                "&family=Inter:wght@200;300;400;500;600&display=swap")

_font_cache: dict[str, str] = {}


def curl(url: str) -> bytes:
    return subprocess.run(
        ["curl", "-sS", "-A", UA, "--max-time", "30", url],
        check=True, capture_output=True,
    ).stdout


def data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def build_font_css() -> str:
    """Fetch the Google Fonts CSS and inline each latin woff2 as a data URI.

    Only the `latin` subset is kept — the full set would add megabytes for
    glyphs an Australian marketing page never renders.
    """
    css = curl(FONT_CSS_URL).decode("utf-8")
    blocks, keep = [], False
    for line in css.splitlines():
        if line.strip().startswith("/*"):
            keep = line.strip() in ("/* latin */", "/* latin-ext */")
        if keep:
            blocks.append(line)
    css = "\n".join(blocks)

    def repl(m: re.Match) -> str:
        url = m.group(1)
        if url not in _font_cache:
            _font_cache[url] = base64.b64encode(curl(url)).decode()
        return f"url(data:font/woff2;base64,{_font_cache[url]})"

    return re.sub(r"url\((https://fonts\.gstatic\.com[^)]+)\)", repl, css)


def inline(page: str, font_css: str) -> str:
    src = (ROOT / page).read_text("utf-8")

    # Drop the external font <link> tags and preconnects.
    src = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", src)
    src = re.sub(r'\s*<link\s+rel="stylesheet"\s+href="https://fonts\.googleapis[^>]*>',
                 "", src, flags=re.S)

    # Replace the local stylesheet link with the real CSS + fonts.
    site_css = (ROOT / "style.css").read_text("utf-8")
    combined = f"<style>\n{font_css}\n{site_css}\n</style>"
    # lambda replacement: CSS contains backslashes re.sub would read as escapes
    src = re.sub(r'<link rel="stylesheet" href="\./style\.css[^>]*>',
                 lambda _: combined, src)

    # Inline every local image reference as a data URI.
    def img_repl(m: re.Match) -> str:
        attr, path = m.group(1), m.group(2)
        f = ROOT / path.lstrip("/")
        if not f.is_file():
            return m.group(0)
        return f'{attr}="{data_uri(f)}"'

    # NOTE: keep this extension list in sync with what /photos actually holds.
    # webp was missing once and the hero model silently vanished from every
    # published preview — the path 404s under the artifact CSP and the <img>
    # onerror handler then hides the slot, so it fails invisibly.
    src = re.sub(r'(src|href)="(/[\w./-]+\.(?:png|jpe?g|svg|webp|avif|gif))"',
                 img_repl, src)
    # smile.png is referenced from CSS (the wordmark underline).
    smile = ROOT / "smile.png"
    if smile.is_file():
        src = src.replace('url("/smile.png?v=v3")', f'url("{data_uri(smile)}")')

    # The site's JS lives in a separate file; inline it so forms still demo.
    js = ROOT / "waitlist.js"
    if js.is_file():
        block = "<script>\n" + js.read_text("utf-8") + "\n</script>"
        src = re.sub(r'<script defer src="/waitlist\.js[^>]*></script>',
                     lambda _: block, src)
    return src


def main() -> None:
    pages = sys.argv[1:] or ["for-dentists.html", "waitlist.html"]
    print("fetching fonts…")
    font_css = build_font_css()
    for page in pages:
        out = OUT_DIR / f"preview-{page}"
        out.write_text(inline(page, font_css), "utf-8")
        print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
