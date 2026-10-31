"""Download 1-minute spot candles from Coinbase's free public API.

Usage: python fetch_spot_1m.py PRODUCT DAYS OUT.csv   (e.g. BTC-USD 120 data/btc_spot_1m.csv)
Columns: ts (minute open, unix s), open, high, low, close, volume.
"""
import csv, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

API = "https://api.exchange.coinbase.com/products/{}/candles?granularity=60&start={}&end={}"

def chunk(args):
    prod, s = args
    url = API.format(prod, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(s)),
                     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(s + 299 * 60)))
    for attempt in range(6):
        try:
            # curl, because Coinbase's Cloudflare rule rejects urllib.
            out = subprocess.run(["curl", "-sSf", "-m", "20", url], capture_output=True,
                                 check=True, text=True).stdout
            return json.loads(out)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    print("failed chunk", s, file=sys.stderr)
    return []

def main():
    prod, days, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    end = int(time.time()) // 60 * 60
    starts = range(end - days * 86400, end, 300 * 60)
    rows = {}
    with ThreadPoolExecutor(4) as ex:   # Coinbase public limit is ~10 req/s
        for res in ex.map(chunk, [(prod, s) for s in starts]):
            for t, lo, hi, op, cl, v in res:
                rows[t] = (t, op, hi, lo, cl, v)
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ts", "open", "high", "low", "close", "volume"])
        w.writerows(rows[t] for t in sorted(rows))
    print(f"{prod}: {len(rows)} minutes -> {out} (expected ~{days * 1440})")

if __name__ == "__main__":
    main()
