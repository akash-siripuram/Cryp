"""Scan Polymarket markets with active liquidity rewards and rank them by reward per
dollar of competing qualifying liquidity (rough "yield" for a new maker).

Usage: python rewards/scan.py [TOP_N_BOOKS=150]
Public read-only endpoints; no keys, no orders.
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

def get(url):
    try:
        return json.loads(subprocess.run(["curl", "-sSf", "-m", "20", url], capture_output=True,
                                         text=True, check=True).stdout)
    except Exception:
        return None

def all_reward_markets():
    out, cur = [], ""
    while True:
        d = get("https://clob.polymarket.com/rewards/markets/current" + (f"?next_cursor={cur}" if cur else ""))
        if not d: break
        out += d.get("data", [])
        cur = d.get("next_cursor")
        if not cur or cur == "LTE=": break
    return out

def score(dist, v):                      # Polymarket's per-share score, distance in cents
    return ((v - dist) / v) ** 2 if dist < v else 0.0

def competition(m):
    """Sum of scored size near the mid (both sides of the Yes token's book)."""
    info = get(f"https://clob.polymarket.com/markets/{m['condition_id']}")
    if not info or not info.get("active") or info.get("closed"): return None
    tok = info["tokens"][0]
    book = get(f"https://clob.polymarket.com/book?token_id={tok['token_id']}")
    if not book or not book.get("bids") or not book.get("asks"): return None
    bids = [(float(x["price"]), float(x["size"])) for x in book["bids"]]
    asks = [(float(x["price"]), float(x["size"])) for x in book["asks"]]
    bb, ba = max(p for p, _ in bids), min(p for p, _ in asks)
    mid, v, mn = (bb + ba) / 2, m["rewards_max_spread"], m["rewards_min_size"]
    q = lambda side: sum(s * score(abs(p - mid) * 100, v) for p, s in side if s >= mn)
    qb, qa = q(bids), q(asks)
    usd_near = sum(p * s for p, s in bids if abs(p - mid) * 100 < v) + sum((1 - p) * s for p, s in asks if abs(p - mid) * 100 < v)
    return {"question": info.get("question", "")[:70], "mid": round(mid, 3), "spread_c": round((ba - bb) * 100, 1),
            "q_comp": round(min(qb, qa) + 1e-9, 1), "usd_near_mid": round(usd_near), "end": info.get("end_date_iso"),
            "slug": info.get("market_slug")}

if __name__ == "__main__":
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    ms = all_reward_markets()
    rate = lambda m: m.get("total_daily_rate") or 0
    print(f"{len(ms)} markets with reward configs; total daily pool ${sum(rate(m) for m in ms):,.0f}")
    dist = sorted((rate(m) for m in ms), reverse=True)
    print("largest daily pools ($):", [round(x) for x in dist[:15]])
    cand = sorted(ms, key=rate, reverse=True)[:top]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(competition, cand))
    rows = []
    for m, r in zip(cand, res):
        if r and 0.1 <= r["mid"] <= 0.9:
            r["daily_$"] = rate(m); r["max_spread_c"] = m["rewards_max_spread"]; r["min_size"] = m["rewards_min_size"]
            r["$/day per $1k competing"] = round(1000 * rate(m) / max(r["usd_near_mid"], 1), 2)
            rows.append(r)
    rows.sort(key=lambda r: r["$/day per $1k competing"], reverse=True)
    json.dump(rows, open("rewards/scan_results.json", "w"), indent=1)
    for r in rows[:25]:
        print(f"${r['daily_$']:>6}/day | ${r['usd_near_mid']:>8,} near mid | {r['$/day per $1k competing']:>7}/1k | "
              f"mid {r['mid']:.2f} spr {r['spread_c']}c v={r['max_spread_c']} min={r['min_size']} | {r['end'] or ''} | {r['question']}")
