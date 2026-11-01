"""Summarize a paper-trading run. Usage: python rewards/paper_summary.py OUT.jsonl"""
import json, sys
st = json.load(open(sys.argv[1] + ".state.json"))
rows = [json.loads(l) for l in open(sys.argv[1])]
hrs = (rows[-1]["t"] - rows[0]["t"]) / 3600 if rows else 0
print(f"run length: {hrs:.2f} h, {len(rows)} market-polls")
last = {}
for r in rows: last[r["slug"]] = r
tot = {"touch": [0, 0, 0], "behind": [0, 0, 0]}
for m in st:
    r = last.get(m["slug"])
    if not r: continue
    cap = m["S"] * r["bb"] + m["S"] * (1 - r["ba"])          # capital to post both sides once
    print(f"\n{m['slug'][:70]}  (${m['rate']}/day, S={m['S']}, capital/side-pair ≈ ${cap:.0f})")
    for k in ("touch", "behind"):
        x = r[k]; net = x["reward"] + x["pnl_mtm"]
        tot[k][0] += x["reward"]; tot[k][1] += x["pnl_mtm"]; tot[k][2] += cap
        print(f"  {k:6s}: reward ${x['reward']:.2f}  fills {x['fills']}  inventory {x['pos']:+.0f}  "
              f"inventory P&L ${x['pnl_mtm']:+.2f}  NET ${net:+.2f}  last share {x['share']:.1%}")
for k, (rw, pnl, cap) in tot.items():
    net = rw + pnl
    per_day = net / hrs * 24 if hrs else 0
    print(f"\nTOTAL {k}: reward ${rw:.2f}, inventory P&L ${pnl:+.2f}, net ${net:+.2f} over {hrs:.1f} h "
          f"-> ${per_day:+.2f}/day on ≈${cap:,.0f} capital ({100*per_day/cap if cap else 0:+.2f}%/day)")
