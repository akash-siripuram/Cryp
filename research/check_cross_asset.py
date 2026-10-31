"""Does an older BTC market price improve on ETH's own market price (and vice versa)?

At minute k of window s, take the target asset's last price sample at or before
s+60k (time t). From the other asset, use only samples strictly earlier than t.
Fit logistic regression on the first 60% of windows; report log loss on the next 20%.
"""
import json, numpy as np, pandas as pd, bisect
from sklearn.linear_model import LogisticRegression

cache = {}
for l in open("odds_cache.jsonl"):
    j = json.loads(l); cache[j["slug"]] = j["history"]

def last(pts, t, strict=False):
    ts = [p["t"] for p in pts]
    i = bisect.bisect_left(ts, t) if strict else bisect.bisect_right(ts, t)
    return (pts[i - 1]["t"], pts[i - 1]["p"]) if i else (np.nan, np.nan)

lg = lambda p: np.log(np.clip(p, 1e-3, 1 - 1e-3) / (1 - np.clip(p, 1e-3, 1 - 1e-3)))
ll = lambda p, y: -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

def run(tgt, oth):
    a = pd.read_csv(f"data/{tgt}_5m_120d_odds.csv"); a = a[a.result.isin(["Up", "Down"])]
    starts = a.start_ts.values; y = (a.result == "Up").values.astype(int)
    for k in range(1, 5):
        X = []
        for s in starts:
            pt = cache.get(f"{tgt}-updown-5m-{s}", []); po = cache.get(f"{oth}-updown-5m-{s}", [])
            t, p = last(pt, s + 60 * k)
            _, q = last(po, t, strict=True) if po and t == t else (np.nan, np.nan)
            _, p0 = last(pt, s); _, q0 = last(po, s)
            X.append([lg(p), lg(q), lg(p) - lg(p0), lg(q) - lg(q0)])
        X = np.array(X); ok = ~np.isnan(X).any(1); Xk, yk = X[ok], y[ok]
        n = len(yk); i, j = int(n * .6), int(n * .8)
        own = LogisticRegression().fit(Xk[:i, :1], yk[:i]); both = LogisticRegression().fit(Xk[:i], yk[:i])
        print(f"{tgt} k={k}: own-market {ll(own.predict_proba(Xk[i:j,:1])[:,1], yk[i:j]):.4f}  "
              f"+older {oth} market {ll(both.predict_proba(Xk[i:j])[:,1], yk[i:j]):.4f}  coefs {np.round(both.coef_[0],2)}")

run("eth", "btc"); run("btc", "eth")
