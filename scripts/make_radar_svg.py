#!/usr/bin/env python3
"""
Build a radar-scan SVG: a sweep line rotates once around a faint
signal/noise field of hex & binary glyphs. As the sweep passes each
glyph, it blips out. Once the sweep completes its pass, the D0UAZ
wordmark locks in at the center and a thin rule draws under it.

No photo, no face -- signal resolving out of noise instead.

Design pulled from the portfolio's own palette: charcoal background
(#1C1915), off-white text, a single muted green accent -- consistent
with the "signal / noise / pattern" theme running through the site.
"""
import math
import os
import random

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "d0uaz-radar.svg")

SIZE = 370
CX, CY = SIZE / 2, SIZE / 2 - 14
R = 130

BG = "#1C1915"      # matches portfolio meta-theme-color
FG = "#EDEAE3"      # off-white text
DIM = "#6f6a5e"      # muted ring/grid lines
ACCENT = "#8fae8a"   # quiet muted green, not neon -- restrained like the site

SWEEP_DUR = 2.6      # seconds for one full rotation
GLYPHS = list("01D0UAZ#$%01ABCDEF01")

random.seed(7)


def polar(cx, cy, r, deg):
    rad = math.radians(deg - 90)  # -90 so 0deg points up
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def main():
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}" font-family="\'Cascadia Code\', \'Fira Code\', Consolas, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')

    # concentric rings
    for frac in (0.35, 0.62, 0.85, 1.0):
        parts.append(
            f'<circle cx="{CX}" cy="{CY}" r="{R*frac:.1f}" fill="none" '
            f'stroke="{DIM}" stroke-width="0.7" opacity="0.35"/>'
        )
    # crosshair
    parts.append(f'<line x1="{CX-R}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{DIM}" stroke-width="0.6" opacity="0.3"/>')
    parts.append(f'<line x1="{CX}" y1="{CY-R}" x2="{CX}" y2="{CY+R}" stroke="{DIM}" stroke-width="0.6" opacity="0.3"/>')

    # scattered noise glyphs around the disc, each blips out as the sweep passes its angle
    n_glyphs = 46
    for i in range(n_glyphs):
        ang = random.uniform(0, 360)
        rad_frac = random.uniform(0.25, 0.97)
        x, y = polar(CX, CY, R * rad_frac, ang)
        ch = random.choice(GLYPHS)
        size = random.choice([8, 9, 10])
        delay = (ang / 360.0) * SWEEP_DUR
        opacity_start = random.uniform(0.35, 0.75)
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{DIM}" font-size="{size}" '
            f'text-anchor="middle" opacity="{opacity_start:.2f}">{ch}'
            f'<animate attributeName="opacity" from="{opacity_start:.2f}" to="0" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
            f'</text>'
        )

    # sweep wedge: a radial gradient triangle that rotates once, then fades out
    grad_id = "sweepGrad"
    parts.append(
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0.55"/>'
        f'</linearGradient></defs>'
    )
    # wedge as a path: center -> arc point A -> arc point B -> close, spanning ~28deg
    span = 28
    ax, ay = polar(CX, CY, R, -span/2)
    bx, by = polar(CX, CY, R, span/2)
    wedge = (
        f'<path d="M {CX:.1f} {CY:.1f} L {ax:.1f} {ay:.1f} '
        f'A {R} {R} 0 0 1 {bx:.1f} {by:.1f} Z" fill="url(#{grad_id})">'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'from="0 {CX:.1f} {CY:.1f}" to="360 {CX:.1f} {CY:.1f}" '
        f'begin="0s" dur="{SWEEP_DUR}s" fill="freeze" repeatCount="1"/>'
        f'<animate attributeName="opacity" from="1" to="0" '
        f'begin="{SWEEP_DUR}s" dur="0.6s" fill="freeze"/>'
        f'</path>'
    )
    parts.append(wedge)

    # leading edge line of the sweep, slightly brighter
    edge = (
        f'<line x1="{CX:.1f}" y1="{CY:.1f}" x2="{CX:.1f}" y2="{CY-R:.1f}" '
        f'stroke="{ACCENT}" stroke-width="1.2" opacity="0.9">'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'from="0 {CX:.1f} {CY:.1f}" to="360 {CX:.1f} {CY:.1f}" '
        f'begin="0s" dur="{SWEEP_DUR}s" fill="freeze" repeatCount="1"/>'
        f'<animate attributeName="opacity" from="0.9" to="0" '
        f'begin="{SWEEP_DUR}s" dur="0.6s" fill="freeze"/>'
        f'</line>'
    )
    parts.append(edge)

    # wordmark locks in after the sweep completes
    word = "D0UAZ"
    letter_spacing = 26
    total_w = letter_spacing * (len(word) - 1)
    start_x = CX - total_w / 2
    word_y = CY + 8

    for i, ch in enumerate(word):
        x = start_x + i * letter_spacing
        delay = SWEEP_DUR + 0.15 + i * 0.09
        parts.append(
            f'<text x="{x:.1f}" y="{word_y:.1f}" fill="{FG}" font-size="30" font-weight="700" '
            f'text-anchor="middle" opacity="0">{ch}'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.2f}s" dur="0.2s" fill="freeze"/>'
            f'</text>'
        )

    # thin rule draws under the wordmark once all letters are in
    rule_delay = SWEEP_DUR + 0.15 + len(word) * 0.09 + 0.1
    rule_w = total_w + 40
    parts.append(
        f'<line x1="{CX-rule_w/2:.1f}" y1="{word_y+14:.1f}" x2="{CX-rule_w/2:.1f}" y2="{word_y+14:.1f}" '
        f'stroke="{ACCENT}" stroke-width="1.4">'
        f'<animate attributeName="x2" from="{CX-rule_w/2:.1f}" to="{CX+rule_w/2:.1f}" '
        f'begin="{rule_delay:.2f}s" dur="0.5s" fill="freeze"/>'
        f'</line>'
    )

    # small subtitle beneath, on-brand with the portfolio's language
    sub_delay = rule_delay + 0.5
    parts.append(
        f'<text x="{CX:.1f}" y="{word_y+34:.1f}" fill="{DIM}" font-size="10.5" '
        f'text-anchor="middle" letter-spacing="2" opacity="0">SIGNAL // RESOLVED'
        f'<animate attributeName="opacity" from="0" to="0.85" '
        f'begin="{sub_delay:.2f}s" dur="0.6s" fill="freeze"/>'
        f'</text>'
    )

    parts.append('</svg>')

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))

    print(f"[make_radar_svg] wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
