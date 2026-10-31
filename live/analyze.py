"""Analyze live recordings: real spreads, and whether Polymarket lags Coinbase by seconds.

Usage: python live/analyze.py live/btc_book.jsonl
"""
import json, sys, numpy as np, pandas as pd

rows = []
for line in open(sys.argv[1]):
    r = json.loads(line)
    up, dn, cb = r.get("Up"), r.get("Down"), r.get("cb")
    if not (up and up["bid"] and up["ask"] and cb and r["window"]): continue
    rows.append({"t": r["t"], "w": r["window"], "bid": up["bid"][0], "ask": up["ask"][0],
                 "ask_size": up["ask"][1], "spot": (float(cb["bid"]) + float(cb["ask"])) / 2})
d = pd.DataFrame(rows).sort_values("t").reset_index(drop=True)
d["mid"] = (d.bid + d.ask) / 2; d["spread"] = d.ask - d.bid
d["sec"] = d.t - d.w
print(f"{len(d)} samples over {d.w.nunique()} windows")
print("Up-token spread (cents):", (d.spread * 100).round(1).value_counts(normalize=True).head(5).round(3).to_dict())
print("median top-of-book ask size (shares):", d.ask_size.median())

# Fair probability from spot: open = first spot in window (proxy for Chainlink price to beat).
d["open"] = d.groupby("w").spot.transform("first")
d = d[d.groupby("w").sec.transform("min") < 10]          # windows recorded from the start
ret = np.log(d.spot).diff().where(d.w.eq(d.w.shift()))
sig5s = ret.std()
rem = np.maximum(300 - d.sec, 5) / 5
from scipy.stats import norm
d["fair"] = norm.cdf(np.log(d.spot / d["open"]) / (sig5s * np.sqrt(rem)))

# Lead/lag: does the change in fair prob over the last step predict the next change in mid?
g = d.groupby("w")
d["d_fair"] = g.fair.diff(); d["d_mid_next"] = g.mid.shift(-1) - d.mid; d["d_mid"] = g.mid.diff()
ok = d[["d_fair", "d_mid_next", "d_mid"]].notna().all(axis=1) & d.sec.between(20, 280)
x = d[ok]
print(f"corr(spot move now, Polymarket move NEXT 5s) = {x.d_fair.corr(x.d_mid_next):.3f}  (n={len(x)})")
print(f"corr(spot move now, Polymarket move SAME 5s) = {x.d_fair.corr(x.d_mid):.3f}")
# Latency-arb test: after a spot jump, buy at the ask now and sell at the bid H steps later.
# Note: Coinbase is fetched just before the books (~0.3-1 s apart), so this is optimistic.
for H in (1, 2, 4):
    d["bid_later"] = g.bid.shift(-H); d["ask_later"] = g.ask.shift(-H)
    for th in (0.02, 0.05, 0.10):
        upj, dnj = ok & (d.d_fair > th), ok & (d.d_fair < -th)
        fee = lambda p: 0.07 * p * (1 - p)          # Polymarket crypto taker fee per share, each leg
        pnl = pd.concat([(d.bid_later - d.ask - fee(d.ask) - fee(d.bid_later))[upj],
                         (d.bid - d.ask_later - fee(d.bid) - fee(d.ask_later))[dnj]]).dropna()
        if len(pnl):
            print(f"hold {5*H:2d}s, spot-jump >{th:.2f}: trades {len(pnl):4d}, avg P&L per share after spread+fees {pnl.mean()*100:+.2f}c")

# Hold to settlement: buy after a spot jump, keep until the window resolves (one fee only).
import subprocess
def result(w):
    try:
        out = subprocess.run(["curl", "-sSf", "-m", "10", f"https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{int(w)}"],
                             capture_output=True, text=True, check=True).stdout
        m = json.loads(out)[0]["markets"][0]
        pr = json.loads(m["outcomePrices"]); oc = json.loads(m["outcomes"])
        return 1.0 if oc[pr.index("1")] == "Up" else 0.0
    except Exception:
        return np.nan
res = {w: result(w) for w in d.w.unique()}
d["up_won"] = d.w.map(res)
fee = lambda p: 0.07 * p * (1 - p)
for th in (0.02, 0.05, 0.10):
    for lo, hi in ((20, 150), (150, 280)):
        sel = ok & d.sec.between(lo, hi) & d.up_won.notna()
        first_up = d[sel & (d.d_fair > th)].groupby("w").head(1)      # one trade per window and direction
        first_dn = d[sel & (d.d_fair < -th)].groupby("w").head(1)
        pnl = pd.concat([first_up.up_won - first_up.ask - fee(first_up.ask),
                         (1 - first_dn.up_won) - (1 - first_dn.bid) - fee(1 - first_dn.bid)])
        if len(pnl):
            print(f"hold to settlement, jump >{th:.2f}, entry {lo}-{hi}s: trades {len(pnl):3d}, "
                  f"avg P&L/share {pnl.mean()*100:+.2f}c, win {np.mean(pnl > 0):.2f}")
