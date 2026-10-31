"""Does any model beat the market's own probability? (log loss on val, before costs)

For entry minute k, features use only what's known at k: market prices up to
minute k, previous windows' results/returns, time of day, recent volatility.
"""
import numpy as np, pandas as pd, backtest as B
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

def lg(p):
    p = np.clip(p, 1e-3, 1 - 1e-3); return np.log(p / (1 - p))

def feats(d, k):
    f = pd.DataFrame(index=d.index)
    for j in range(k + 1):
        f[f"lg{j}"] = lg(d[B.MINUTE_COLS[j]].values)
    if k: f["dlast"] = f[f"lg{k}"] - f[f"lg{k-1}"]
    ret = np.log(d["final_price"] / d["price_to_beat"]) * 1e4
    up = (d["result"] == "Up").astype(float)
    for w in (1, 3, 12, 48):
        f[f"ret{w}"] = ret.shift(1).rolling(w).sum()
        f[f"up{w}"] = up.shift(1).rolling(w).mean()
    f["vol12"] = ret.shift(1).rolling(12).std()
    f["vol144"] = ret.shift(1).rolling(144).std()
    h = (d["start_ts"] % 86400) / 3600
    f["hs"], f["hc"] = np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)
    return f

def ll(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

if __name__ == "__main__":
    d = pd.concat(B.load(), ignore_index=True)
    n = len(d); a, b = int(n * .6), int(n * .8)
    y = (d["result"] == "Up").values.astype(int)
    for k in range(5):
        F = feats(d, k).fillna(0).values
        mk = d[B.MINUTE_COLS[k]].values
        gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.03, max_iter=300,
                                            l2_regularization=1.0, random_state=0).fit(F[:a], y[:a])
        lr = LogisticRegression(C=0.1, max_iter=2000).fit(F[:a], y[:a])
        print(f"k={k} val logloss  market {ll(mk[a:b], y[a:b]):.4f}  logistic {ll(lr.predict_proba(F[a:b])[:,1], y[a:b]):.4f}"
              f"  gboost {ll(gb.predict_proba(F[a:b])[:,1], y[a:b]):.4f}")
