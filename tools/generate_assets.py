#!/usr/bin/env python3
"""
Generate neobrutalist + pixel SVG assets for the GitHub profile README.

Design language:
  - thick black borders, hard (un-blurred) offset shadows
  - bright saturated colors on cream paper
  - pixel fonts (Press Start 2P for headings, VT323 for terminal text)
  - fonts are subset to ASCII and embedded as base64 woff2 so the SVGs
    render standalone on GitHub (no external font requests).

Run:  python tools/generate_assets.py
"""

import base64
import io
import os

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "tools", "fonts")
ASSET_DIR = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- palette ---
INK = "#111111"
PAPER = "#FFF8E7"
YELLOW = "#FFD23F"
CYAN = "#3DDCFF"
PINK = "#FF5CA8"
LIME = "#A8FF3E"
PURPLE = "#B58CFF"
ORANGE = "#FF8A3D"
PALETTE = [INK, YELLOW, CYAN, PINK, LIME, PURPLE, ORANGE]


def font_to_woff2_b64(filename: str, text: str) -> str:
    """Subset a TTF to the given text + printable ASCII, return base64 woff2."""
    font = TTFont(os.path.join(FONT_DIR, filename))
    chars = set(text) | {chr(c) for c in range(0x20, 0x7F)}
    options = subset.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["*"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(chars)))
    subsetter.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def font_face_css(psp_b64: str, vt_b64: str) -> str:
    return (
        "@font-face{font-family:'PSP';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        "@font-face{font-family:'VT';font-style:normal;font-weight:400;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        ".psp{font-family:'PSP',monospace;}"
        ".vt{font-family:'VT',monospace;}"
    ) % (psp_b64, vt_b64)


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


def text(x, y, s, size, fill, cls="psp", anchor="middle", spacing=None):
    t = '<text x="%g" y="%g" class="%s" font-size="%g" fill="%s" text-anchor="%s"' % (
        x, y, cls, size, fill, anchor,
    )
    if spacing:
        t += ' letter-spacing="%g"' % spacing
    return t + ">%s</text>" % s


# ----------------------------------------------------------------- header ---
def build_header(psp_b64, vt_b64):
    W, H = 1000, 300
    b = []
    b.append(rect(28, 28, 944, 256, INK))                       # hard shadow
    b.append(rect(16, 16, 944, 256, PAPER, INK, 6))             # card
    b.append(rect(16, 16, 944, 54, CYAN, INK, 6))               # title bar
    for i, c in enumerate((PINK, YELLOW, LIME)):                # window dots
        b.append(rect(40 + i * 22, 37, 13, 13, c, INK, 2))
    b.append(text(122, 55, "alfian@github:~$ whoami", 27, INK, "vt", "start"))
    for r in range(2):                                          # title-bar texture
        for c in range(5):
            b.append(rect(842 + c * 22, 32 + r * 16, 10, 10, INK))

    # name on a yellow chip
    b.append(rect(154, 104, 692, 54, YELLOW, INK, 4))
    b.append(text(500, 143, "ALFIAN EKA MAULANA", 36, INK))
    # role chip
    b.append(rect(340, 182, 320, 38, PINK, INK, 4))
    b.append(text(500, 209, "FULLSTACK DEVELOPER", 15, INK))
    # footer line
    b.append(text(500, 252, "// build. ship. learn. repeat.", 25, INK, "vt"))

    # pixel decorations
    b.append(rect(896, 96, 18, 18, LIME, INK, 3))
    b.append(rect(872, 120, 18, 18, PURPLE, INK, 3))
    b.append(rect(58, 226, 18, 18, ORANGE, INK, 3))
    b.append(rect(82, 202, 18, 18, CYAN, INK, 3))
    return svg(W, H, "Alfian Eka Maulana - Fullstack Developer",
               "".join(b), font_face_css(psp_b64, vt_b64))


# --------------------------------------------------------------- sections ---
def build_section(label, color, psp_b64):
    W, H = 480, 64
    b = []
    b.append(rect(8, 8, 464, 48, INK))
    b.append(rect(0, 0, 464, 48, color, INK, 5))
    b.append(text(24, 33, ">", 18, INK, "psp", "start"))
    b.append(text(56, 33, label, 18, INK, "psp", "start"))
    for i in range(3):                                          # little menu icon
        b.append(rect(414 + i * 16, 19, 12, 12, INK))
    css = "@font-face{font-family:'PSP';font-style:normal;font-weight:400;" \
          "src:url(data:font/woff2;base64,%s) format('woff2');}.psp{font-family:'PSP',monospace;}" % psp_b64
    return svg(W, H, label, "".join(b), css)


def build_divider():
    W, H = 1000, 24
    b = []
    x, i = 0, 0
    while x + 16 <= W:
        b.append(rect(x, 4, 16, 16, PALETTE[i % len(PALETTE)]))
        x += 24
        i += 1
    return svg(W, H, "divider", "".join(b), "")


def main():
    os.makedirs(ASSET_DIR, exist_ok=True)
    psp_b64 = font_to_woff2_b64("PressStart2P-Regular.ttf", "ALFIANEKMAUL")
    vt_b64 = font_to_woff2_b64("VT323-Regular.ttf", "alfian@github:~$ whoami")

    files = {"header.svg": build_header(psp_b64, vt_b64), "divider.svg": build_divider()}
    sections = [
        ("section-about.svg", "ABOUT_ME", CYAN),
        ("section-stack.svg", "TECH_STACK", LIME),
        ("section-experience.svg", "EXPERIENCE", YELLOW),
        ("section-projects.svg", "PROJECTS", PINK),
        ("section-achievements.svg", "ACHIEVEMENTS", ORANGE),
        ("section-contact.svg", "CONTACT", PURPLE),
    ]
    for fname, label, color in sections:
        files[fname] = build_section(label, color, psp_b64)

    for fname, content in files.items():
        with open(os.path.join(ASSET_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote assets/%s (%d KB)" % (fname, len(content) // 1024))


if __name__ == "__main__":
    main()
