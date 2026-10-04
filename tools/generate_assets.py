#!/usr/bin/env python3
"""
Generate SVG assets for the GitHub profile README.

Design language (restrained neobrutalism):
  - monochrome base (black / white) with a single blue accent
  - thin solid borders, no scattered decoration
  - pixel display font for headings, terminal font for meta text
  - fonts subset to ASCII and embedded as base64 woff2 so the SVGs render
    standalone on GitHub (no external font requests)
  - every asset ships light + dark, selected via
    <picture><source media="(prefers-color-scheme: dark)">

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

THEMES = {
    "light": dict(card="#FFFFFF", border="#111111", text="#111111",
                  muted="#57606A", line="#D0D7DE", shadow="#111111", accent="#2563EB"),
    "dark":  dict(card="#0D1117", border="#E6EDF3", text="#F0F6FC",
                  muted="#8B949E", line="#30363D", shadow="#30363D", accent="#3B82F6"),
}

# flat, ordered list -> rendered as a uniform 5 x 3 grid
STACK_ITEMS = [
    ("php", "PHP"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
    ("laravel", "Laravel"), ("nextdotjs", "Next.js"),
    ("tailwindcss", "Tailwind CSS"), ("mysql", "MySQL"), ("postgresql", "PostgreSQL"),
    ("sqlite", "SQLite"), ("redis", "Redis"),
    ("git", "Git"), ("github", "GitHub"), ("jira", "Jira"), ("trello", "Trello"),
    ("powerbi", "Power BI"),
]

SECTIONS = [("about", "ABOUT_ME"), ("stack", "TECH_STACK"),
            ("stats", "GITHUB_STATS"), ("contact", "CONTACT")]


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
    """Advance width of a string in px, measured from the real font metrics."""
    font = TTFont(path)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    total = sum(hmtx[cmap[ord(c)]][0] for c in s if ord(c) in cmap)
    return total / upm * size


def font_face_css(psp_b64, vt_b64, extra=""):
    # built by concatenation (not %-formatting) so CSS can contain raw '%'
    return (
        "@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64," + psp_b64 + ") format('woff2');}"
        "@font-face{font-family:'VT';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64," + vt_b64 + ") format('woff2');}"
        ".psp{font-family:'PSP',monospace;}.vt{font-family:'VT',monospace;}"
        + extra
    )


def psp_css(psp_b64):
    return ("@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
            "src:url(data:font/woff2;base64," + psp_b64 + ") format('woff2');}"
            ".psp{font-family:'PSP',monospace;}")


# ---------------------------------------------------------------- helpers ---
def svg(width, height, label, body, css, extra_defs=""):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s">'
        "<defs><style>%s</style>%s</defs>%s</svg>"
    ) % (width, height, width, height, label, css, extra_defs, body)


def rect(x, y, w, h, fill, stroke=None, sw=0, cls=None):
    s = '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"' % (x, y, w, h, fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
    if cls:
        s += ' class="%s"' % cls
    return s + "/>"


def esc(s):
    """Escape XML special characters in text nodes."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size, fill, cls="psp", anchor="middle"):
    return ('<text x="%g" y="%g" class="%s" font-size="%g" fill="%s" '
            'text-anchor="%s">%s</text>') % (x, y, cls, size, fill, anchor, esc(s))


# ----------------------------------------------------------------- header ---
def build_header(t):
    """Live-terminal header: transparent background, no card/border/shadow, so
    it reads as page text rather than a banner graphic. A prompt line with a
    blinking cursor plus a staggered fade-in on the name and role."""
    prompt = "alfian@github:~$ whoami"
    name = "Alfian Eka Maulana"
    role = "Fullstack Developer  \u00b7  Jakarta, Indonesia"
    p_size, n_size, r_size = 24, 36, 26
    w = max(text_width(VT_TTF, prompt, p_size),
            text_width(PSP_TTF, name, n_size),
            text_width(VT_TTF, role, r_size))
    W, H = int(w + 34), 142
    px = text_width(VT_TTF, prompt, p_size) + 8
    extra = ("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
             ".cursor{animation:blink 1.1s steps(1) infinite;}"
             "@keyframes fade{from{opacity:0}to{opacity:1}}"
             ".f2{animation:fade .7s ease .25s both;}"
             ".f3{animation:fade .7s ease .55s both;}")
    b = [
        text(0, 28, prompt, p_size, t["muted"], "vt", "start"),
        rect(px, 11, 10, 18, t["accent"], cls="cursor"),
        '<text class="psp f2" x="0" y="90" font-size="%d" fill="%s" '
        'text-anchor="start">%s</text>' % (n_size, t["text"], esc(name)),
        '<text class="vt f3" x="0" y="126" font-size="%d" fill="%s" '
        'text-anchor="start">%s</text>' % (r_size, t["muted"], esc(role)),
    ]
    return svg(W, H, "Alfian Eka Maulana - Fullstack Developer", "".join(b),
               font_face_css(t["_psp"], t["_vt"], extra))


# ------------------------------------------------------ animated typing ---
def build_typing(t):
    """Typewriter line, one <text> per character with its own opacity
    keyframes. Deliberately avoids SMIL, <mask> and CSS `width` inside
    <clipPath>: none of those animate when the SVG is loaded through <img>
    (which is exactly how GitHub renders README images)."""
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

    rules, elems = [], []
    for i, ch in enumerate(line):
        a = 45.0 * (i + 1) / n                      # appears
        v = 82.0 + 16.0 * (n - i) / n               # disappears (reverse order)
        rules.append("@keyframes c%d{0%%{opacity:0}%.2f%%{opacity:0}%.2f%%{opacity:1}"
                     "%.2f%%{opacity:1}%.2f%%{opacity:0}100%%{opacity:0}}"
                     % (i, max(a - 0.05, 0.0), a, v, v + 0.05))
        rules.append(".c%d{animation:c%d %ds infinite;}" % (i, i, dur))
        if ch.strip():
            elems.append('<text class="vt c%d" x="%.1f" y="%d" font-size="%d" '
                         'fill="%s">%s</text>' % (i, xs[i], ty, size, t["muted"], esc(ch)))

    # the cursor rides along with the text instead of sitting at the far end
    rules.append("@keyframes cur{0%%{transform:translateX(0);"
                 "animation-timing-function:steps(%d,end)}"
                 "45%%{transform:translateX(%.1fpx);animation-timing-function:linear}"
                 "82%%{transform:translateX(%.1fpx);animation-timing-function:steps(%d,end)}"
                 "100%%{transform:translateX(0)}}" % (n, line_w, line_w, n))
    rules.append(".cursor{animation:cur %ds infinite,blink 1.1s steps(1) infinite;}" % dur)

    css = font_face_css(t["_psp"], t["_vt"],
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}" + "".join(rules))
    b = [
        text(0, ty, prompt, size, t["accent"], "vt", "start"),
        "".join(elems),
        rect(tx, ty - 20, 10, 22, t["accent"], cls="cursor"),
    ]
    return svg(W, H, "typing", "".join(b), css)


# ---------------------------------------------------------------- section ---
def build_section(label, t, width=280):
    b = [
        rect(6, 6, width, 40, t["shadow"]),
        rect(0, 0, width, 40, t["card"], t["border"], 4),
        rect(14, 12, 16, 16, t["accent"], t["border"], 2),
        text(46, 27, label, 16, t["text"], "psp", "start"),
    ]
    return svg(width, 52, label, "".join(b), psp_css(t["_psp"]))


# ---------------------------------------------------------------- divider ---
def build_divider(t):
    W = 1000
    return svg(W, 14, "divider", "".join(rect(x, 3, 8, 8, t["line"]) for x in range(0, W, 16)), "")


# ------------------------------------------------------------- tech grid ---
def build_stack(icons, t):
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
                 % (cx - size / 2, iy, size / 24.0, icons[slug], t["text"]))
        b.append(text(cx, iy + size + 16, name, label, t["text"]))
    return svg(W, H, "Tech stack", "".join(b), psp_css(t["_psp"]))


# ------------------------------------------------------------------- main ---
def main():
    os.makedirs(ASSET_DIR, exist_ok=True)
    icons = json.load(open(os.path.join(ROOT, "tools", "icons.json"), encoding="utf-8"))

    psp = font_to_woff2_b64(PSP_TTF,
                            "".join(n for _, n in STACK_ITEMS) +
                            "ALFIANEKMAULNABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    vt = font_to_woff2_b64(VT_TTF,
                           "alfian@github:~$ whoami Fullstack Developer Jakarta Indonesia "
                           "github.com/alfianmaulana114  \u00b7  alfianmaulana.me "
                           "> building & shipping web apps end to end")

    files = {}
    for name, t in THEMES.items():
        t = dict(t, _psp=psp, _vt=vt)
        files["header-%s.svg" % name] = build_header(t)
        files["typing-%s.svg" % name] = build_typing(t)
        files["divider-%s.svg" % name] = build_divider(t)
        files["stack-%s.svg" % name] = build_stack(icons, t)
        for key, label in SECTIONS:
            files["section-%s-%s.svg" % (key, name)] = build_section(label, t)

    for fname, content in sorted(files.items()):
        with open(os.path.join(ASSET_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote assets/%-28s %3d KB" % (fname, len(content) // 1024))


if __name__ == "__main__":
    main()
