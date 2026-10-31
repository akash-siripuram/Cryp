"""Download the past N days of Polymarket "Bitcoin Up or Down" 5-minute markets.

Uses the public Polymarket Gamma API (no account or key needed). Each market
resolves on Chainlink's BTC/USD price: 'priceToBeat' is the price at window
start and 'finalPrice' is the price at window end.

Usage: python fetch_btc_5m_updown.py [days] [out.csv] [asset]
  asset: btc (default), eth, sol, xrp, ...
"""
import csv, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

API = "https://gamma-api.polymarket.com/events"
BATCH = 20  # API returns at most 20 events per request

def fetch(slugs):
    url = API + "?" + urlencode([("slug", s) for s in slugs])
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** attempt)
    print("failed batch starting", slugs[0], file=sys.stderr)
    return []

def row(ev):
    m = (ev.get("markets") or [{}])[0]
    meta = ev.get("eventMetadata") or {}
    outcomes = json.loads(m.get("outcomes") or "[]")
    prices = [float(p) for p in json.loads(m.get("outcomePrices") or "[]")]
    winner = outcomes[prices.index(1.0)] if 1.0 in prices else ""
    start = int(ev["slug"].rsplit("-", 1)[1])
    return {
        "start_ts": start,
        "start_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start)),
        "slug": ev["slug"],
        "price_to_beat": meta.get("priceToBeat"),
        "final_price": meta.get("finalPrice"),
        "result": winner,
        "status": m.get("umaResolutionStatus"),
        "volume": m.get("volume"),
    }

def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out = sys.argv[2] if len(sys.argv) > 2 else "btc_5m_updown.csv"
    asset = sys.argv[3] if len(sys.argv) > 3 else "btc"
    last = (int(time.time()) // 300 - 1) * 300  # latest window already finished
    starts = range(last - days * 86400 + 300, last + 1, 300)
    slugs = [f"{asset}-updown-5m-{t}" for t in starts]
    batches = [slugs[i:i + BATCH] for i in range(0, len(slugs), BATCH)]
    with ThreadPoolExecutor(8) as ex:
        events = [e for res in ex.map(fetch, batches) for e in res]
    rows = sorted((row(e) for e in events), key=lambda r: r["start_ts"])
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    up = sum(r["result"] == "Up" for r in rows)
    print(f"{len(rows)}/{len(slugs)} windows -> {out}  (Up {up}, Down {sum(r['result']=='Down' for r in rows)})")

if __name__ == "__main__":
    main()
