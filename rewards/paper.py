"""Paper-trade Polymarket liquidity rewards. Read-only: no orders are ever sent.

For each market, two virtual quoting variants rest S shares on both sides of the
Yes token's book:
  touch  - bid at best bid, ask at best ask
  behind - one tick further from the mid on each side
Every poll we estimate our reward with Polymarket's scoring rule
  score = ((v - s)/v)^2 per share, Q_min = max(min(Qb,Qa), max(Qb,Qa)/3) (mid in .10-.90,
  else min), share = ours / (ours + everyone else's)
and accrue daily_rate * share * dt / 86400. Fills: our bid fills if the best ask
drops to or below our price or a trade prints at or below it (asks mirror this).
Fills build inventory (capped at 3*S per side), valued at the price we could exit at
(bid for longs, ask for shorts).

Usage: python rewards/paper.py HOURS OUT.jsonl SLUG [SLUG ...]
"""
import json, subprocess, sys, time

POLL, S_MIN = 15, 100

def get(url):
    try:
        return json.loads(subprocess.run(["curl", "-sSf", "-m", "15", url], capture_output=True,
                                         text=True, check=True).stdout)
    except Exception:
        return None

def score(dist_c, v):
    return ((v - dist_c) / v) ** 2 if dist_c < v else 0.0

def qmin(qb, qa, mid):
    return max(min(qb, qa), max(qb, qa) / 3) if 0.10 <= mid <= 0.90 else min(qb, qa)

def setup(slug):
    g = get(f"https://gamma-api.polymarket.com/markets?slug={slug}")
    if not g: raise SystemExit(f"no market {slug}")
    m = g[0]; cid = m["conditionId"]
    info = get(f"https://clob.polymarket.com/markets/{cid}")
    rw = get(f"https://clob.polymarket.com/rewards/markets/{cid}")
    rate = 0
    try:
        rate = sum(c.get("rate_per_day") or 0 for c in rw["data"][0]["rewards_config"])
    except Exception:
        pass
    tok = info["tokens"][0]["token_id"]
    v, mn = info["rewards"]["max_spread"], info["rewards"]["min_size"]
    tick = float(info.get("minimum_tick_size") or 0.01)
    S = max(S_MIN, mn)
    return {"slug": slug, "tok": tok, "v": v, "min": mn, "tick": tick, "S": S, "rate": rate,
            "last_seen": None,
            "var": {k: {"bid": None, "ask": None, "pos": 0.0, "cash": 0.0, "reward": 0.0,
                        "fills": 0, "fill_log": []} for k in ("touch", "behind")}}

def step(mk, dt, out):
    book = get(f"https://clob.polymarket.com/book?token_id={mk['tok']}")
    if not book or not book.get("bids") or not book.get("asks"): return
    bids = [(float(x["price"]), float(x["size"])) for x in book["bids"]]
    asks = [(float(x["price"]), float(x["size"])) for x in book["asks"]]
    bb, ba = max(p for p, _ in bids), min(p for p, _ in asks)
    mid = (bb + ba) / 2
    lt = get(f"https://clob.polymarket.com/last-trade-price?token_id={mk['tok']}")
    px = float(lt["price"]) if lt and lt.get("price") else None
    # only count a print as a new trade when the last-trade price changed since the last poll
    last = px if (px is not None and mk["last_seen"] is not None and px != mk["last_seen"]) else None
    mk["last_seen"] = px
    v, mn, S, t = mk["v"], mk["min"], mk["S"], mk["tick"]
    comp_b = sum(s * score(abs(mid - p) * 100, v) for p, s in bids if s >= mn)
    comp_a = sum(s * score(abs(p - mid) * 100, v) for p, s in asks if s >= mn)
    comp = qmin(comp_b, comp_a, mid)
    rec = {"t": round(time.time()), "slug": mk["slug"], "mid": mid, "bb": bb, "ba": ba, "last": last}
    for name, st in mk["var"].items():
        # 1) fills against the quotes we had resting since the last poll
        if st["bid"] is not None and (ba <= st["bid"] or (last is not None and last <= st["bid"])) and st["pos"] < 3 * S:
            st["pos"] += S; st["cash"] -= S * st["bid"]; st["fills"] += 1
            st["fill_log"].append({"t": rec["t"], "side": "buy", "px": st["bid"], "mid": mid})
        if st["ask"] is not None and (bb >= st["ask"] or (last is not None and last >= st["ask"])) and st["pos"] > -3 * S:
            st["pos"] -= S; st["cash"] += S * st["ask"]; st["fills"] += 1
            st["fill_log"].append({"t": rec["t"], "side": "sell", "px": st["ask"], "mid": mid})
        # 2) requote
        off = 0 if name == "touch" else t
        st["bid"] = round(bb - off, 4) if st["pos"] < 3 * S else None
        st["ask"] = round(ba + off, 4) if st["pos"] > -3 * S else None
        # 3) reward share for this interval
        qb = S * score((mid - st["bid"]) * 100, v) if st["bid"] is not None else 0
        qa = S * score((st["ask"] - mid) * 100, v) if st["ask"] is not None else 0
        ours = qmin(qb, qa, mid)
        share = ours / (ours + comp) if ours > 0 else 0.0
        st["reward"] += mk["rate"] * share * dt / 86400
        rec[name] = {"share": round(share, 4), "reward": round(st["reward"], 4), "pos": st["pos"],
                     "pnl_mtm": round(st["cash"] + st["pos"] * (bb if st["pos"] > 0 else ba), 4), "fills": st["fills"]}
    out.write(json.dumps(rec) + "\n"); out.flush()

def main():
    hours, path, slugs = float(sys.argv[1]), sys.argv[2], sys.argv[3:]
    mks = [setup(s) for s in slugs]
    for m in mks: print(f"{m['slug'][:60]}: ${m['rate']}/day v={m['v']} min={m['min']} S={m['S']}", flush=True)
    end, last = time.time() + hours * 3600, time.time()
    with open(path, "a") as out:
        while time.time() < end:
            t0 = time.time(); dt = t0 - last; last = t0
            for m in mks: step(m, dt if dt < 120 else POLL, out)
            json.dump([{k: v for k, v in m.items() if k != "tok"} for m in mks], open(path + ".state.json", "w"))
            time.sleep(max(0, POLL - (time.time() - t0)))

if __name__ == "__main__":
    main()
