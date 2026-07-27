#!/usr/bin/env python3
"""
Fetch a user's public GitHub contribution calendar (no token / no GraphQL API).

GitHub serves this as a plain HTML fragment at:
    https://github.com/users/<username>/contributions

We parse the day cells with BeautifulSoup and write out:
    data/contributions.json

containing the raw per-day counts plus a few derived stats (current streak,
longest streak, best single day, monthly totals) that the renderer and the
info card can both use.
"""
import json
import os
import sys
from datetime import datetime, date
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "Dorvae")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_calendar_html(username: str) -> str:
    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as either a <td class="ContributionCalendar-day">
    # or (newer markup) a <table><tr><td> with tool-tips holding the count.
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        # fallback for the newer web-component markup
        cells = soup.select("[data-date]")

    for cell in cells:
        d = cell.get("data-date")
        level = cell.get("data-level")
        if d is None:
            continue
        count = 0
        # Try to pull the numeric count out of tooltip text if present
        tip_id = cell.get("id")
        tooltip = None
        if tip_id:
            tooltip = soup.find(attrs={"for": tip_id})
        text = tooltip.get_text(strip=True) if tooltip else cell.get("aria-label", "")
        for token in text.replace(",", "").split():
            if token.isdigit():
                count = int(token)
                break
        days.append({
            "date": d,
            "count": count,
            "level": int(level) if level is not None else None,
        })

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    # current streak (walking back from most recent day)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    best_day = max(days, key=lambda x: x["count"], default={"date": None, "count": 0})

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


def main():
    try:
        html = fetch_calendar_html(USERNAME)
        days = parse_days(html)
        if not days:
            raise ValueError("No contribution cells parsed — GitHub markup may have changed.")
    except Exception as e:
        print(f"[fetch_contributions] WARNING: {e}", file=sys.stderr)
        # Don't crash the daily workflow over a scrape hiccup — keep last good data if present.
        if os.path.exists(OUT_PATH):
            print("[fetch_contributions] Keeping previous data/contributions.json", file=sys.stderr)
            return
        days = []

    payload = {
        "username": USERNAME,
        "days": days,
        "stats": derive_stats(days) if days else {},
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[fetch_contributions] wrote {len(days)} days to {OUT_PATH}")


if __name__ == "__main__":
    main()
