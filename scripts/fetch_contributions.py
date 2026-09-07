#!/usr/bin/env python3
"""Snapshot the GitHub contribution calendar to data/contributions.json."""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

USER = "mithils3"
ROOT = Path(__file__).resolve().parent.parent

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}
"""


def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def main():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token()}", "Content-Type": "application/json"},
    )
    body = json.load(urllib.request.urlopen(req))
    if "errors" in body:
        sys.exit(f"graphql: {body['errors']}")
    coll = body["data"]["user"]["contributionsCollection"]
    cal = coll["contributionCalendar"]
    weeks = cal["weeks"][-53:]
    out = {
        "total": cal["totalContributions"],
        "commits": coll["totalCommitContributions"],
        "weeks": [[d for d in w["contributionDays"]] for w in weeks],
    }
    p = ROOT / "data" / "contributions.json"
    p.write_text(json.dumps(out))
    print(p, out["total"], "contributions,", len(weeks), "weeks")


if __name__ == "__main__":
    main()
