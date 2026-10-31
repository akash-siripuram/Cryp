"""Add Polymarket's market price of "Up" around each window's open to the dataset.

For each 5-min market, records the last traded/mid price of the Up token at or
before the window start (p_up_open) and ~1 minute in (p_up_1m). Public CLOB API.

Usage: python fetch_updown_odds.py [in.csv] [out.csv]
"""
import csv, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

GAMMA = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/prices-history"

def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** attempt)
    return None

def up_tokens(slugs):
    evs = get(GAMMA + "?" + urlencode([("slug", s) for s in slugs])) or []
    out = {}
    for e in evs:
        m = e["markets"][0]
        outcomes, toks = json.loads(m["outcomes"]), json.loads(m["clobTokenIds"])
        out[e["slug"]] = toks[outcomes.index("Up")]
    return out

def odds(args):
    slug, tok, start = args
    h = get(CLOB + "?" + urlencode({"market": tok, "startTs": start - 600,
                                    "endTs": start + 90, "fidelity": 1}))
    pts = (h or {}).get("history", [])
    at = lambda t: next((p["p"] for p in reversed(pts) if p["t"] <= t), None)
    return slug, at(start), at(start + 60)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "btc_5m_updown_30d.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "btc_5m_updown_30d_odds.csv"
    rows = list(csv.DictReader(open(src)))
    slugs = [r["slug"] for r in rows]
    with ThreadPoolExecutor(8) as ex:
        toks = {}
        for d in ex.map(up_tokens, [slugs[i:i + 20] for i in range(0, len(slugs), 20)]):
            toks.update(d)
    jobs = [(r["slug"], toks[r["slug"]], int(r["start_ts"])) for r in rows if r["slug"] in toks]
    with ThreadPoolExecutor(16) as ex:
        res = {s: (a, b) for s, a, b in ex.map(odds, jobs)}
    for r in rows:
        r["p_up_open"], r["p_up_1m"] = res.get(r["slug"], (None, None))
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    got = sum(r["p_up_open"] is not None for r in rows)
    print(f"odds for {got}/{len(rows)} windows -> {dst}")

if __name__ == "__main__":
    main()
