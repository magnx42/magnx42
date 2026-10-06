"""Fetch the last-year contribution calendar into data/contributions.json.

Uses the GraphQL API when GITHUB_TOKEN is set (stable schema, what the workflow
does); otherwise falls back to the public HTML fragment (no auth, but tied to
GitHub's markup).
"""
import json
import os
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "magnx42")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def via_graphql(token: str) -> list[dict]:
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USER}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        {"date": d["date"], "count": d["contributionCount"]}
        for w in weeks
        for d in w["contributionDays"]
    ]


def via_html() -> list[dict]:
    from bs4 import BeautifulSoup

    r = requests.get(f"https://github.com/users/{USER}/contributions", timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.select("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        m = re.match(r"(\d[\d,]*) contribution", tips.get(td.get("id"), ""))
        days.append({"date": td["data-date"], "count": int(m.group(1).replace(",", "")) if m else 0})
    if not days:
        raise RuntimeError("no day cells found, GitHub markup changed?")
    return sorted(days, key=lambda d: d["date"])


def stats(days: list[dict]) -> dict:
    counts = [d["count"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # le jour courant peut encore être à 0 sans casser la série
    current = 0
    for c in reversed(counts[:-1] if counts and counts[-1] == 0 else counts):
        if not c:
            break
        current += 1
    best = max(days, key=lambda d: d["count"]) if days else None
    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]
    return {
        "total": sum(counts),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "active_days": sum(1 for c in counts if c),
        "monthly": dict(monthly),
    }


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    days = via_graphql(token) if token else via_html()
    out = {"user": USER, "generated": date.today().isoformat(), "days": days, "stats": stats(days)}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "contributions.json").write_text(json.dumps(out, indent=1))
    s = out["stats"]
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current_streak']}/{s['longest_streak']}")


if __name__ == "__main__":
    main()
