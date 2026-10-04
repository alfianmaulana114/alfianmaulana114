#!/usr/bin/env python3
"""
Generate SVG assets for the GitHub profile README.

Design language (restrained neobrutalism):
  - monochrome base (black / white) with a single blue accent
  - thin solid borders, no scattered decoration
  - pixel display font for headings, terminal font for meta text
  - fonts are subset to ASCII and embedded as base64 woff2 so the SVGs
    render standalone on GitHub (no external font requests)
  - every asset ships in a light and a dark variant, selected in the
    README through <picture media="(prefers-color-scheme: dark)">

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

THEMES = {
    "light": dict(card="#FFFFFF", border="#111111", text="#111111",
                  muted="#57606A", line="#D0D7DE", shadow="#111111", accent="#2563EB"),
    "dark":  dict(card="#0D1117", border="#E6EDF3", text="#F0F6FC",
                  muted="#8B949E", line="#30363D", shadow="#30363D", accent="#3B82F6"),
}

STACK = [
    ("LANGUAGES", [("php", "PHP"), ("javascript", "JavaScript"), ("typescript", "TypeScript")]),
    ("FRAMEWORKS", [("laravel", "Laravel"), ("nextdotjs", "Next.js"), ("tailwindcss", "Tailwind CSS")]),
    ("DATABASES", [("mysql", "MySQL"), ("postgresql", "PostgreSQL"), ("sqlite", "SQLite"), ("redis", "Redis")]),
    ("TOOLS", [("git", "Git"), ("github", "GitHub"), ("jira", "Jira"), ("trello", "Trello"), ("powerbi", "Power BI")]),
]


# ------------------------------------------------------------- font embed ---
def font_to_woff2_b64(filename, text):
    font = TTFont(os.path.join(FONT_DIR, filename))
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


def font_face_css(psp_b64, vt_b64):
    return (
        "@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        "@font-face{font-family:'VT';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        ".psp{font-family:'PSP',monospace;}.vt{font-family:'VT',monospace;}"
    ) % (psp_b64, vt_b64)


# ---------------------------------------------------------------- helpers ---
def svg(width, height, label, body, css):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s">'
        "<defs><style>%s</style></defs>%s</svg>"
    ) % (width, height, width, height, label, css, body)


def rect(x, y, w, h, fill, stroke=None, sw=0):
    s = '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"' % (x, y, w, h, fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
    return s + "/>"


def text(x, y, s, size, fill, cls="psp", anchor="middle"):
    return ('<text x="%g" y="%g" class="%s" font-size="%g" fill="%s" '
            'text-anchor="%s">%s</text>') % (x, y, cls, size, fill, anchor, s)


# ----------------------------------------------------------------- header ---
def build_header(t):
    W, H = 1000, 200
    b = [
        rect(10, 10, 980, 176, t["shadow"]),
        rect(0, 0, 980, 176, t["card"], t["border"], 4),
        rect(2, 2, 976, 32, t["border"]),
        text(18, 24, "alfian@github:~$ whoami", 20, t["card"], "vt", "start"),
        text(490, 100, "ALFIAN EKA MAULANA", 36, t["text"]),
        text(490, 134, "Fullstack Developer  \u00b7  Jakarta, Indonesia", 28, t["muted"], "vt"),
        text(490, 163, "github.com/alfianmaulana114  \u00b7  alfianmaulana.me", 20, t["muted"], "vt"),
    ]
    return svg(W, H, "Alfian Eka Maulana - Fullstack Developer", "".join(b),
               font_face_css(t["_psp"], t["_vt"]))


# ---------------------------------------------------------------- section ---
def build_section(label, t, width=280):
    W, H = width, 52
    b = [
        rect(6, 6, width, 40, t["shadow"]),
        rect(0, 0, width, 40, t["card"], t["border"], 4),
        rect(14, 12, 16, 16, t["accent"], t["border"], 2),
        text(46, 27, label, 16, t["text"], "psp", "start"),
    ]
    css = ("@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
           "src:url(data:font/woff2;base64,%s) format('woff2');}"
           ".psp{font-family:'PSP',monospace;}") % t["_psp"]
    return svg(W, H, label, "".join(b), css)


# ---------------------------------------------------------------- divider ---
def build_divider(t):
    W, H = 1000, 14
    b = [rect(x, 3, 8, 8, t["line"]) for x in range(0, W, 16)]
    return svg(W, H, "divider", "".join(b), "")


# ------------------------------------------------------------ tech stack ---
def build_stack(icons, t):
    cell, row, size = 170, 104, 30
    W = max(len(items) for _, items in STACK) * cell
    H = row * len(STACK)
    b = []
    for r, (cat, items) in enumerate(STACK):
        y = r * row
        b.append(text(0, y + 18, cat, 16, t["accent"], "psp", "start"))
        for i, (slug, name) in enumerate(items):
            cx = i * cell + cell / 2
            s = size / 24.0
            b.append('<g transform="translate(%g,%g) scale(%g)">'
                     '<path d="%s" fill="%s"/></g>'
                     % (cx - size / 2, y + 36, s, icons[slug], t["text"]))
            b.append(text(cx, y + 84, name, 12, t["text"]))
    css = ("@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
           "src:url(data:font/woff2;base64,%s) format('woff2');}"
           ".psp{font-family:'PSP',monospace;}") % t["_psp"]
    return svg(W, H, "Tech stack", "".join(b), css)


# ------------------------------------------------------------------- main ---
def main():
    os.makedirs(ASSET_DIR, exist_ok=True)
    icons = json.load(open(os.path.join(ROOT, "tools", "icons.json"), encoding="utf-8"))

    all_text = "".join(n for _, items in STACK for _, n in items) + \
               "ALFIAN EK MAULNA" + "LANGUAGESFRAMEWORKSDATABASESTOOLS" + \
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    psp = font_to_woff2_b64("PressStart2P-Regular.ttf", all_text)
    vt = font_to_woff2_b64("VT323-Regular.ttf",
                           "alfian@github:~$ whoami Fullstack Developer Jakarta Indonesia "
                           "github.com/alfianmaulana114  \u00b7  alfianmaulana.me")

    sections = [("about", "ABOUT_ME"), ("stack", "TECH_STACK"), ("experience", "EXPERIENCE"),
                ("projects", "PROJECTS"), ("achievements", "ACHIEVEMENTS"), ("contact", "CONTACT")]

    files = {}
    for name, t in THEMES.items():
        t = dict(t, _psp=psp, _vt=vt)
        files["header-%s.svg" % name] = build_header(t)
        files["divider-%s.svg" % name] = build_divider(t)
        files["stack-%s.svg" % name] = build_stack(icons, t)
        for key, label in sections:
            files["section-%s-%s.svg" % (key, name)] = build_section(label, t)

    for fname, content in sorted(files.items()):
        with open(os.path.join(ASSET_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote assets/%-28s %3d KB" % (fname, len(content) // 1024))


if __name__ == "__main__":
    main()
