"""Compare today's reward-scan snapshot with earlier days.
Usage: python rewards/daily_report.py  -> writes rewards/DAILY.md"""
import csv, collections, glob, json
snaps = sorted(glob.glob("rewards/snapshots/*.json"))
hist = collections.defaultdict(dict)
for r in csv.DictReader(open("rewards/pool_history.csv")):
    hist[r["slug"]][r["day"]] = r
days = sorted({d for v in hist.values() for d in v})
today = days[-1]
lines = [f"# Liquidity-rewards daily scan ({today})", "",
         "| Day | Markets with rewards | Total daily pool |", "|---|---|---|"]
for p in snaps[-14:]:
    s = json.load(open(p)); lines.append(f"| {s['day']} | {s['n_markets']:,} | ${s['total_daily_pool']:,.0f} |")
lines += ["", "## Today's best candidates (quiet filters: ends > 10 days out, spread ≤ 3¢, mid 0.15–0.85, ≥ $300 quoted)", "",
          "| Market | Pool $/day | Quoted near mid | $/day per $1k | Days seen in top 100 | Pool change vs first seen |", "|---|---|---|---|---|---|"]
import datetime as dt
cutoff = (dt.date.fromisoformat(today) + dt.timedelta(days=10)).isoformat()
cands = []
for slug, by in hist.items():
    r = by.get(today)
    if not r: continue
    if not r["end"] or r["end"] <= cutoff: continue
    try:
        if not (0.15 <= float(r["mid"]) <= 0.85 and float(r["spread_c"]) <= 3 and float(r["usd_near_mid"]) >= 300): continue
    except ValueError:
        continue
    first = by[min(by)]
    chg = float(r["daily_usd"]) / max(float(first["daily_usd"]), 1e-9) - 1
    cands.append((float(r["per_1k"]), slug, r, len(by), chg))
for per, slug, r, n, chg in sorted(cands, reverse=True)[:15]:
    lines.append(f"| {slug[:70]} | ${float(r['daily_usd']):.0f} | ${float(r['usd_near_mid']):,.0f} | {per:.1f} | {n} | {chg:+.0%} |")
open("rewards/DAILY.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines[:20]))
