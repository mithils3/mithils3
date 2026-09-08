#!/usr/bin/env python3
"""Snapshot local Claude Code token usage to data/claude-tokens.json.

Reads ~/.claude/projects/**/*.jsonl, the transcripts Claude Code writes for
every session on this machine, subagent and workflow transcripts included.
Assistant turns carry a usage block; the same turn can appear in more than one
transcript after a resume, so turns are deduped on (message id, request id).
Days are bucketed in local time.

This one is machine-local, so it runs by hand, not in the workflow. The JSON it
writes is committed and the renderer reads that.
"""
import json, os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = Path(os.environ.get("CLAUDE_PROJECTS", Path.home() / ".claude" / "projects"))
KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def main():
    daily = defaultdict(lambda: dict.fromkeys(KEYS, 0))
    turns_by_day = defaultdict(int)
    seen, uuids, sessions, projects, tools, bad = set(), set(), set(), set(), 0, 0

    for f in sorted(LOGS.rglob("*.jsonl")):
        rel = f.relative_to(LOGS).parts
        with f.open(errors="replace") as fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage")
                if rec.get("type") != "assistant" or not usage:
                    continue
                # one API response is written out as one line per content block,
                # each line repeating the same usage, so tokens dedupe on the
                # response and tool calls count per line
                if rec.get("uuid") not in uuids:
                    uuids.add(rec.get("uuid"))
                    tools += sum(1 for c in msg.get("content") or []
                                 if isinstance(c, dict) and c.get("type") == "tool_use")
                key = (msg.get("id"), rec.get("requestId"))
                if key in seen:
                    continue
                seen.add(key)
                day = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")).astimezone().date()
                bucket = daily[day]
                for k in KEYS:
                    bucket[k] += usage.get(k) or 0
                turns_by_day[day] += 1
                sessions.add(rec.get("sessionId") or rel[1].removesuffix(".jsonl"))
                projects.add(rel[0])

    if not daily:
        raise SystemExit(f"no transcripts under {LOGS}")

    start, end = min(daily), max(daily)
    rows, cum = [], 0
    for i in range((end - start).days + 1):
        d = start + timedelta(days=i)
        day = daily.get(d)
        total = sum(day.values()) if day else 0
        cum += total
        rows.append({"date": d.isoformat(), "tokens": total, "cum": cum,
                     "turns": turns_by_day.get(d, 0)})

    out = {
        "as_of": date.today().isoformat(),
        "window": [start.isoformat(), end.isoformat()],
        "sessions": len(sessions),
        "projects": len(projects),
        "turns": len(seen),
        "tool_calls": tools,
        "tokens": cum,
        "totals": {k: sum(v[k] for v in daily.values()) for k in KEYS},
        "peak": max(rows, key=lambda r: r["tokens"]),
        "daily": rows,
    }
    p = ROOT / "data" / "claude-tokens.json"
    p.write_text(json.dumps(out, indent=1))
    print(p, f'{out["tokens"]:,} tokens,', f'{len(sessions):,} sessions,',
          f"{len(rows)} days,", f"{bad} unparsed lines")


if __name__ == "__main__":
    main()
