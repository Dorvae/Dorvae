#!/usr/bin/env python3
"""
Render data/contributions.json as an animated SVG contribution heatmap:
a 53-week x 7-day grid of rounded boxes that slide in diagonally (once,
no looping), a Less->More legend, and a stats footer line.

Pure stdlib string templating -> no drawing library needed.
"""
import json
import os
from datetime import datetime, timedelta

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# level:    none        1           2         3          4          5 (neon top end)

BOX = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 34
FOOTER_H = 26
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # 0=Sun .. 6=Sat


def build_grid(days):
    """Bucket the flat day list into GitHub's week-columns (Sun-start)."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return [], None

    last_date = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    # walk back to the most recent Saturday, then 52 weeks further back to a Sunday
    end = last_date
    start = end - timedelta(weeks=53)
    while start.weekday() != 6:  # 6 == Sunday in Python's Mon=0 scheme? Mon=0..Sun=6
        start += timedelta(days=1)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        iso = cur.strftime("%Y-%m-%d")
        rec = by_date.get(iso, {"count": 0, "level": 0})
        week.append({"date": iso, "count": rec.get("count", 0), "level": rec.get("level") or 0})
        if cur.weekday() == 5:  # Saturday -> close out the week column
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        weeks.append(week)

    return weeks, (start, end)


def month_labels(weeks):
    labels = []
    seen = set()
    for wi, week in enumerate(weeks):
        for day in week:
            d = datetime.strptime(day["date"], "%Y-%m-%d").date()
            if d.day <= 7:
                key = (d.year, d.month)
                if key not in seen:
                    seen.add(key)
                    labels.append((wi, d.strftime("%b")))
                break
    return labels


def main():
    with open(DATA_PATH) as f:
        payload = json.load(f)

    days = payload.get("days", [])
    stats = payload.get("stats", {})
    username = payload.get("username", "")

    weeks, span = build_grid(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * (BOX + GAP) + 90  # extra room for legend
    height = TOP_PAD + 7 * (BOX + GAP) + FOOTER_H + 10

    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif">''')
    svg_parts.append(f'''<rect width="100%" height="100%" fill="#0d1117" rx="8"/>''')

    # month labels
    for wi, label in month_labels(weeks):
        x = LEFT_PAD + wi * (BOX + GAP)
        svg_parts.append(f'<text x="{x}" y="16" fill="#8b949e" font-size="10">{label}</text>')

    # weekday labels
    for wd, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + wd * (BOX + GAP) + BOX - 2
        svg_parts.append(f'<text x="2" y="{y}" fill="#8b949e" font-size="9">{label}</text>')

    # day boxes, staggered diagonal reveal
    delay_step = 0.006
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (BOX + GAP)
            y = TOP_PAD + di * (BOX + GAP)
            level = max(0, min(5, day["level"]))
            color = PALETTE[level]
            delay = (wi + di) * delay_step
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2.5" fill="{color}" '
                f'opacity="0" transform="translate(-6,-6)">'
                f'<title>{day["count"]} contributions on {day["date"]}</title>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-6,-6" to="0,0" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>'
                f'</rect>'
            )

    # legend: Less [boxes] More
    legend_x = LEFT_PAD + n_weeks * (BOX + GAP) + 4
    legend_y = TOP_PAD
    svg_parts.append(f'<text x="{legend_x}" y="{legend_y+BOX-2}" fill="#8b949e" font-size="9">Less</text>')
    for i, color in enumerate(PALETTE):
        lx = legend_x + 26 + i * (BOX + 2)
        svg_parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX-2}" height="{BOX-2}" rx="2" fill="{color}"/>')
    svg_parts.append(f'<text x="{legend_x + 26 + len(PALETTE)*(BOX+2) + 4}" y="{legend_y+BOX-2}" fill="#8b949e" font-size="9">More</text>')

    # footer stats line
    total = stats.get("total_last_year", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_y = height - 8
    footer_text = f"{total} contributions in the last year  ·  current streak {streak}d  ·  longest streak {longest}d"
    svg_parts.append(f'<text x="{LEFT_PAD}" y="{footer_y}" fill="#c9d1d9" font-size="11">{footer_text}</text>')

    svg_parts.append('</svg>')

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(svg_parts))

    print(f"[render_heatmap_svg] wrote {OUT_PATH} ({n_weeks} weeks)")


if __name__ == "__main__":
    main()
