"""Live recorder: every ~5 s, log the current BTC 5-min Up/Down order book top
(both tokens) and Coinbase BTC-USD bid/ask, for measuring real spreads and
sub-minute lead/lag. Read-only, public endpoints, no trading.

Usage: python live/recorder.py HOURS OUT.jsonl
"""
import json, subprocess, sys, time

def get(url):
    try:
        out = subprocess.run(["curl", "-sSf", "-m", "8", url], capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except Exception:
        return None

def top(book):
    if not book: return None
    bids = sorted(((float(x["price"]), float(x["size"])) for x in book.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in book.get("asks", []))
    return {"bid": bids[0] if bids else None, "ask": asks[0] if asks else None,
            "bid_depth": sum(s for p, s in bids[:5]), "ask_depth": sum(s for p, s in asks[:5])}

def main():
    hours, out = float(sys.argv[1]), sys.argv[2]
    end, toks, cur = time.time() + hours * 3600, None, None
    with open(out, "a") as f:
        while time.time() < end:
            s = int(time.time()) // 300 * 300
            if s != cur:
                ev = get(f"https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{s}")
                if ev:
                    m = ev[0]["markets"][0]
                    toks = dict(zip(json.loads(m["outcomes"]), json.loads(m["clobTokenIds"])))
                    cur = s
            t0 = time.time()
            rec = {"t": round(t0, 2), "window": cur,
                   "cb": get("https://api.exchange.coinbase.com/products/BTC-USD/ticker")}
            if toks:
                for side, tok in toks.items():
                    rec[side] = top(get(f"https://clob.polymarket.com/book?token_id={tok}"))
            f.write(json.dumps(rec) + "\n"); f.flush()
            time.sleep(max(0, 5 - (time.time() - t0)))

if __name__ == "__main__":
    main()
