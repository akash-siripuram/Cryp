"""Add Polymarket's market price of "Up" around each window's open to the dataset.

Downloads the Up token's 1-minute price history from 10 min before to the end of
each 5-min window (public CLOB API, no key). Saves the raw histories to
odds_cache.jsonl (resumable) and writes p_up_open (last price at or before
window start) and p_up_1m .. p_up_4m (price N minutes into the window).

Usage: python fetch_updown_odds.py [in.csv] [out.csv]
"""
import csv, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

GAMMA = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/prices-history"
CACHE = "odds_cache.jsonl"

def get(url, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.load(r)
        except Exception:
            time.sleep(1 + attempt)
    return None

def up_tokens(slugs):
    out = {}
    for e in get(GAMMA + "?" + urlencode([("slug", s) for s in slugs])) or []:
        m = e["markets"][0]
        outcomes, toks = json.loads(m["outcomes"]), json.loads(m["clobTokenIds"])
        out[e["slug"]] = toks[outcomes.index("Up")]
    return out

def history(slug, tok, start):
    h = get(CLOB + "?" + urlencode({"market": tok, "startTs": start - 600,
                                    "endTs": start + 300, "fidelity": 1}))
    return slug, None if h is None else h.get("history", [])

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "btc_5m_updown_30d.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "btc_5m_updown_30d_odds.csv"
    rows = list(csv.DictReader(open(src)))
    cache = {}
    if os.path.exists(CACHE):
        for line in open(CACHE):
            d = json.loads(line); cache[d["slug"]] = d["history"]
    todo = [r for r in rows if r["slug"] not in cache]
    print(f"{len(cache)} cached, {len(todo)} to fetch", flush=True)
    if todo:
        slugs = [r["slug"] for r in todo]
        toks = {}
        with ThreadPoolExecutor(8) as ex:
            for d in ex.map(up_tokens, [slugs[i:i + 20] for i in range(0, len(slugs), 20)]):
                toks.update(d)
        with ThreadPoolExecutor(16) as ex, open(CACHE, "a") as f:
            futs = [ex.submit(history, r["slug"], toks[r["slug"]], int(r["start_ts"]))
                    for r in todo if r["slug"] in toks]
            for i, fu in enumerate(as_completed(futs), 1):
                slug, h = fu.result()
                if h is not None:
                    cache[slug] = h
                    f.write(json.dumps({"slug": slug, "history": h}) + "\n")
                if i % 500 == 0:
                    print(f"{i}/{len(futs)}", flush=True); f.flush()
    for r in rows:
        pts, s = cache.get(r["slug"], []), int(r["start_ts"])
        at = lambda t: next((p["p"] for p in reversed(pts) if p["t"] <= t), None)
        r["p_up_open"] = at(s)
        for k in range(1, 5):
            r[f"p_up_{k}m"] = at(s + 60 * k)
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    got = sum(r["p_up_open"] is not None for r in rows)
    print(f"odds for {got}/{len(rows)} windows -> {dst}")

if __name__ == "__main__":
    main()
