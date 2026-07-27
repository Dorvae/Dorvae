#!/usr/bin/env python3
"""
Build a neofetch-style info card SVG: title bar + colored key/value rows
that fade + slide in on a short stagger, like text printing next to the
ASCII portrait.

Set STATIC=1 to emit a frozen (already-visible) frame, useful for local
Quick Look / image previews where animation won't play.
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

WIDTH, HEIGHT = 490, 340
BG = "#0d1117"
BAR = "#161b22"
FG = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#39d353"
KEY_COLOR = "#69f0a0"

USER = "douae"
HOST = "github"

ROWS = [
    ("now", "Cybersecurity Eng. student @ ENSAO -- open to Stage PFA 2026"),
    ("prev", "Security observation stage -- SRM Orientale (AD, GPO, SOC practices)"),
    ("stack", "Python . Linux . Splunk . Wazuh . Wireshark . Metasploit . TensorFlow"),
    ("focus", "Detection engineering . Blue Team . Applied ML for security"),
    ("cert", "TryHackMe -- SOC Level 1 (Analyst Path)"),
    ("highlight", "ML-based IDS w/ SHAP explainability (RF/SVM + LSTM/CNN)"),
    ("highlight", "SSH brute-force detection pipeline -- Hydra to Splunk SPL dashboard"),
    ("club", "Red Phoenix Cybersecurity Club -- Treasurer & active member"),
]

LINE_H = 26
TITLE_H = 34
PAD_X = 20
START_Y = TITLE_H + 30


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main():
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="\'Cascadia Code\', \'Fira Code\', '
        f'Consolas, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>')

    # title bar
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{TITLE_H}" fill="{BAR}" rx="10"/>')
    parts.append(f'<rect x="0" y="{TITLE_H-10}" width="{WIDTH}" height="10" fill="{BAR}"/>')
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{18 + i*18}" cy="{TITLE_H/2}" r="6" fill="{dot}"/>')
    parts.append(
        f'<text x="{WIDTH/2}" y="{TITLE_H/2 + 4}" fill="{DIM}" font-size="12" '
        f'text-anchor="middle">{USER}@{HOST}: neofetch</text>'
    )

    # ascii-ish header line: user@host + underline
    header = f"{USER}@{HOST}"
    parts.append(f'<text x="{PAD_X}" y="{START_Y}" fill="{ACCENT}" font-size="15" font-weight="bold">{header}</text>')
    parts.append(f'<line x1="{PAD_X}" y1="{START_Y+8}" x2="{WIDTH-PAD_X}" y2="{START_Y+8}" stroke="{DIM}" stroke-width="1" opacity="0.4"/>')

    y = START_Y + 34
    delay = 0.15
    for key, val in ROWS:
        key_txt = esc(key)
        val_txt = esc(val)
        line = (
            f'<g{"" if STATIC else " opacity=\"0\""}>'
            f'<text x="{PAD_X}" y="{y}" font-size="13">'
            f'<tspan fill="{KEY_COLOR}" font-weight="bold">{key_txt}</tspan>'
            f'<tspan fill="{DIM}">  </tspan>'
            f'<tspan fill="{FG}">{val_txt}</tspan>'
            f'</text>'
        )
        if not STATIC:
            line += (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
            )
        line += '</g>'
        parts.append(line)
        y += LINE_H
        delay += 0.22

    # color swatches row (the classic neofetch bottom bar)
    swatch_y = y + 8
    palette = ["#0d1117", "#ff5f56", "#39d353", "#ffbd2e", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]
    sw = 24
    for i, c in enumerate(palette):
        x = PAD_X + i * sw
        block = f'<rect x="{x}" y="{swatch_y}" width="{sw-2}" height="14" fill="{c}"{"" if STATIC else " opacity=\"0\""}>'
        if not STATIC:
            block += f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
        block += '</rect>'
        parts.append(block)

    parts.append('</svg>')

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))

    print(f"[make_info_card] wrote {OUT_PATH} (STATIC={STATIC})")


if __name__ == "__main__":
    main()
