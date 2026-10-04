#!/usr/bin/env python3
"""
Generate the SVG assets used by the profile README.

Every asset is *theme-neutral*: it is designed to read correctly on both the
light and the dark GitHub theme, so the README only needs plain <img> tags
(no <picture> / prefers-color-scheme boilerplate).

Fonts (Press Start 2P, VT323) are subset to ASCII and embedded as base64 woff2
so the SVGs render standalone on GitHub with no external font requests.
Both fonts are licensed under the SIL Open Font License 1.1 — see the
OFL-*.txt files next to them in tools/fonts/.

Run:  python tools/generate_assets.py
"""

import base64
import io
import json
import os

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "tools", "fonts")
ASSET_DIR = os.path.join(ROOT, "assets")
PSP_TTF = os.path.join(FONT_DIR, "PressStart2P-Regular.ttf")
VT_TTF = os.path.join(FONT_DIR, "VT323-Regular.ttf")

# theme-neutral palette: every colour must read on white *and* on #0d1117
DARK = "#0D1117"
DARK2 = "#161B22"
WHITE = "#FFFFFF"
ACCENT = "#3B82F6"
ACCENT_SOFT = "#60A5FA"
NEUTRAL = "#6E7681"

STACK_ITEMS = [
    ("php", "PHP"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
    ("laravel", "Laravel"), ("nextdotjs", "Next.js"),
    ("tailwindcss", "Tailwind CSS"), ("mysql", "MySQL"), ("postgresql", "PostgreSQL"),
    ("sqlite", "SQLite"), ("redis", "Redis"),
    ("git", "Git"), ("github", "GitHub"), ("jira", "Jira"), ("trello", "Trello"),
    ("powerbi", "Power BI"),
]


# ------------------------------------------------------------- font utils ---
def font_to_woff2_b64(path, text):
    font = TTFont(path)
    chars = set(text) | {chr(c) for c in range(0x20, 0x7F)}
    options = subset.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["*"]
    sub = subset.Subsetter(options=options)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def text_width(path, s, size):
    font = TTFont(path)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in s if ord(c) in cmap) / upm * size


def font_css(psp_b64, vt_b64, extra=""):
    return (
        "@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64," + psp_b64 + ") format('woff2');}"
        "@font-face{font-family:'VT';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64," + vt_b64 + ") format('woff2');}"
        ".psp{font-family:'PSP',monospace;}.vt{font-family:'VT',monospace;}"
        + extra
    )


# ---------------------------------------------------------------- helpers ---
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(width, height, label, body, css):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s">'
        "<defs><style>%s</style></defs>%s</svg>"
    ) % (width, height, width, height, label, css, body)


def rect(x, y, w, h, fill, stroke=None, sw=0, cls=None):
    s = '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"' % (x, y, w, h, fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
    if cls:
        s += ' class="%s"' % cls
    return s + "/>"


def text(x, y, s, size, fill, cls="psp", anchor="middle"):
    return ('<text x="%g" y="%g" class="%s" font-size="%g" fill="%s" '
            'text-anchor="%s">%s</text>') % (x, y, cls, size, fill, anchor, esc(s))


# ------------------------------------------------------------------- icon ---
def build_icon(psp):
    """Tiny terminal-prompt mark used next to the greeting."""
    b = [rect(4, 4, 36, 36, DARK),
         rect(0, 0, 36, 36, ACCENT),
         text(18, 26, ">", 20, WHITE)]
    return svg(40, 40, "terminal prompt", "".join(b), font_css(psp, psp))


# ----------------------------------------------------------- illustration ---
def build_illustration(psp, vt):
    """Abstract code window, floated to the right of the intro."""
    W, H = 320, 250
    b = [rect(8, 8, 304, 234, DARK)]
    b.append(rect(0, 0, 304, 234, DARK, ACCENT, 3))
    b.append(rect(3, 3, 298, 30, DARK2))
    for i, c in enumerate((ACCENT, NEUTRAL, NEUTRAL)):
        b.append(rect(16 + i * 16, 13, 9, 9, c))
    b.append(text(66, 24, "alfian.ts", 18, NEUTRAL, "vt", "start"))

    lines = [(16, 96, ACCENT), (32, 160, NEUTRAL), (32, 120, ACCENT),
             (48, 80, NEUTRAL), (16, 140, ACCENT), (32, 200, NEUTRAL),
             (16, 84, ACCENT)]
    for i, (ind, w, c) in enumerate(lines):
        b.append(rect(ind, 52 + i * 24, w, 9, c))
    b.append(rect(112, 52 + 6 * 24, 9, 9, ACCENT_SOFT, cls="cur"))
    css = font_css(psp, vt,
                   "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
                   ".cur{animation:blink 1.1s steps(1) infinite;}")
    return svg(W, H, "code window", "".join(b), css)


# ---------------------------------------------------------------- typing ---
def build_typing(psp, vt):
    """Typewriter line: one <text> per character with its own opacity
    keyframes. SMIL, <mask> internals and CSS `width` inside <clipPath> do not
    animate when an SVG is loaded through <img> (how GitHub renders README
    images), so this is the approach that actually works."""
    line = "building & shipping web apps end to end"
    size, prompt, dur = 28, ">", 7
    n = len(line)
    w_prompt = text_width(VT_TTF, prompt, size)
    tx = w_prompt + 12

    xs, x = [], tx
    for ch in line:
        xs.append(x)
        x += text_width(VT_TTF, ch, size)
    line_w = x - tx
    W, H, ty = int(tx + line_w + 24), 46, 33
    cx = tx + line_w + 6

    rules, elems = [], []
    for i, ch in enumerate(line):
        a = 45.0 * (i + 1) / n
        v = 82.0 + 16.0 * (n - i) / n
        rules.append("@keyframes c%d{0%%{opacity:0}%.2f%%{opacity:0}%.2f%%{opacity:1}"
                     "%.2f%%{opacity:1}%.2f%%{opacity:0}100%%{opacity:0}}"
                     % (i, max(a - 0.05, 0.0), a, v, v + 0.05))
        rules.append(".c%d{animation:c%d %ds infinite;}" % (i, i, dur))
        if ch.strip():
            elems.append('<text class="vt c%d" x="%.1f" y="%d" font-size="%d" '
                         'fill="%s">%s</text>' % (i, xs[i], ty, size, ACCENT_SOFT, esc(ch)))

    css = font_css(psp, vt,
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".cursor{animation:blink 1.1s steps(1) infinite;}" + "".join(rules))
    b = [text(0, ty, prompt, size, ACCENT, "vt", "start"),
         "".join(elems),
         rect(cx, ty - 20, 10, 22, ACCENT, cls="cursor")]
    return svg(W, H, "typing", "".join(b), css)


# ------------------------------------------------------------- tech grid ---
def build_stack(icons, psp):
    cols, cell, size, label = 5, 160, 26, 11
    row = 78
    rows = (len(STACK_ITEMS) + cols - 1) // cols
    W, H = cols * cell, rows * row + 6
    b = []
    for i, (slug, name) in enumerate(STACK_ITEMS):
        r, c = divmod(i, cols)
        cx = c * cell + cell / 2
        iy = r * row + 14
        b.append('<g transform="translate(%g,%g) scale(%g)"><path d="%s" fill="%s"/></g>'
                 % (cx - size / 2, iy, size / 24.0, icons[slug], ACCENT))
        b.append(text(cx, iy + size + 16, name, label, NEUTRAL))
    return svg(W, H, "Tech stack", "".join(b), font_css(psp, psp))


# ------------------------------------------------------------------- main ---
def main():
    os.makedirs(ASSET_DIR, exist_ok=True)
    icons = json.load(open(os.path.join(ROOT, "tools", "icons.json"), encoding="utf-8"))

    psp = font_to_woff2_b64(PSP_TTF,
                            "".join(n for _, n in STACK_ITEMS) +
                            ">alfian.tsABCDEFGHIJKLMNOPQRSTUVWXYZ")
    vt = font_to_woff2_b64(VT_TTF,
                           "> alfian.ts building & shipping web apps end to end")

    files = {
        "icon.svg": build_icon(psp),
        "illustration.svg": build_illustration(psp, vt),
        "typing.svg": build_typing(psp, vt),
        "stack.svg": build_stack(icons, psp),
    }
    for fname, content in sorted(files.items()):
        with open(os.path.join(ASSET_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote assets/%-20s %3d KB" % (fname, len(content) // 1024))


if __name__ == "__main__":
    main()
