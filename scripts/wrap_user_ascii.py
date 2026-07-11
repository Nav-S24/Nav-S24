"""
Wrap a user-supplied ASCII-art PNG (already generated elsewhere, e.g.
folge.me/tools/image-to-ascii) in the same terminal-window chrome as
make_ascii_svg.py, and reveal it with a top-to-bottom banded wipe so it still
"types itself in" like the generated version -- just using their image
instead of re-deriving characters from a photo.

The PNG is embedded as a base64 data URI so the SVG is a single portable
file (GitHub renders embedded raster data inside <image> fine).

    python scripts/wrap_user_ascii.py <input.png> [output.svg]
"""
import base64
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "user-ascii-art.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "avi-ascii.svg")

WHOAMI_NAME = "Navya Saxena"
HOST_LABEL = "nav-s24"

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = 700  # display width of the art area; height derives from source aspect

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"

BANDS = 44          # number of horizontal reveal strips
BAND_DUR = 0.11
STAGGER = 0.11

im = Image.open(SRC).convert("RGBA")
src_w, src_h = im.size
ART_H = round(ART_W * src_h / src_w)

CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

with open(SRC, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
data_uri = f"data:image/png;base64,{b64}"

art_top = TITLEBAR_H + PAD * 0.35
art_x = PAD

parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)
parts.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
             f'</linearGradient>'
             f'<image id="art" href="{data_uri}" x="{art_x}" y="{art_top}" '
             f'width="{ART_W}" height="{ART_H}" preserveAspectRatio="none"/>'
             f'</defs>')

parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')

parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">{HOST_LABEL}@github: ~$ ./portrait.sh</text>')

# background plate under the art so the white PNG background matches the
# white ascii "blank space" look, framed like a terminal pane
parts.append(f'<rect x="{art_x}" y="{art_top:.1f}" width="{ART_W}" height="{ART_H}" fill="#ffffff"/>')

STATIC = bool(os.environ.get("STATIC"))
band_h = ART_H / BANDS

if STATIC:
    parts.append(f'<use href="#art"/>')
else:
    for b in range(BANDS):
        y0 = art_top + b * band_h
        delay = b * STAGGER
        parts.append(
            f'<clipPath id="b{b}"><rect x="{art_x}" y="{y0:.2f}" height="{band_h:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
            f'dur="{BAND_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#b{b})"><use href="#art"/></g>')
        parts.append(
            f'<rect y="{y0+1:.2f}" width="10" height="{max(band_h-2,2):.2f}" fill="{INK}" opacity="0">'
            f'<animate attributeName="x" from="{art_x}" to="{art_x+ART_W}" begin="{delay:.3f}s" '
            f'dur="{BAND_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+BAND_DUR:.3f}s"/></rect>'
        )

# frame around the art area to match the window chrome
parts.append(f'<rect x="{art_x}" y="{art_top:.1f}" width="{ART_W}" height="{ART_H}" '
             f'fill="none" stroke="{FRAME}" stroke-opacity="0.6"/>')

status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
             f'{HOST_LABEL}@github:~$ whoami <tspan fill="{INK}">{WHOAMI_NAME}</tspan></text>')
cursor_x = PAD + (len(HOST_LABEL) + 9 + len(WHOAMI_NAME)) * 7.2
parts.append(f'<rect x="{cursor_x:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
