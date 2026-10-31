"""Train models to predict BTC 5-min Up/Down from information known at window start.

Split is chronological (no shuffling): first 70% train, next 15% validation,
last 15% test. Features only use previous windows, so there is no look-ahead.

Usage: python train_updown_model.py [btc_5m_updown_30d.csv]
"""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def build_features(df):
    df = df.sort_values("start_ts").reset_index(drop=True)
    df = df[df["result"].isin(["Up", "Down"])].copy()
    df["y"] = (df["result"] == "Up").astype(int)
    # Return of each window in basis points (known only once the window ends).
    df["ret"] = (df["final_price"] / df["price_to_beat"] - 1) * 1e4
    df["ret"] = df["ret"].fillna(0)
    f = pd.DataFrame(index=df.index)
    for k in range(1, 13):                       # last hour of window returns
        f[f"ret_lag{k}"] = df["ret"].shift(k)
    for w in (3, 6, 12, 36, 144):                # momentum / volatility / up-rate
        past = df["ret"].shift(1)
        f[f"ret_sum{w}"] = past.rolling(w).sum()
        f[f"vol{w}"] = past.rolling(w).std()
        f[f"uprate{w}"] = df["y"].shift(1).rolling(w).mean()
    # Current streak length of same-direction results (signed).
    sign = np.where(df["y"] == 1, 1, -1)
    streak, s = [], 0
    for v in sign:
        streak.append(s)
        s = s + v if (s == 0 or np.sign(s) == v) else v
    f["streak"] = streak
    t = pd.to_datetime(df["start_ts"], unit="s")
    hour = t.dt.hour + t.dt.minute / 60
    f["hour_sin"], f["hour_cos"] = np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)
    f["dow"] = t.dt.dayofweek
    f["log_volume_lag1"] = np.log1p(df["volume"].shift(1).fillna(0))
    keep = f.notna().all(axis=1)
    return f[keep], df.loc[keep, "y"], df.loc[keep, "start_utc"]

def evaluate(name, p, y):
    return {"model": name, "accuracy": accuracy_score(y, p > 0.5),
            "auc": roc_auc_score(y, p), "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))}

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "btc_5m_updown_30d.csv"
    X, y, when = build_features(pd.read_csv(path))
    n = len(X); a, b = int(n * .70), int(n * .85)
    splits = {"train": slice(0, a), "val": slice(a, b), "test": slice(b, n)}
    for k, s in splits.items():
        print(f"{k:5s}: {when.iloc[s].iloc[0]} -> {when.iloc[s].iloc[-1]}  n={len(y.iloc[s])}  up%={y.iloc[s].mean():.3f}")
    Xtr, ytr = X.iloc[splits["train"]], y.iloc[splits["train"]]

    models = {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)),
        "random_forest": RandomForestClassifier(400, min_samples_leaf=50, n_jobs=-1, random_state=0),
        "grad_boost": HistGradientBoostingClassifier(max_depth=3, learning_rate=0.03, max_iter=300,
                                                     l2_regularization=1.0, random_state=0),
    }
    rows = {"val": [], "test": []}
    base = ytr.mean()
    for split in rows:
        ys = y.iloc[splits[split]]
        rows[split].append(evaluate("baseline (train up-rate)", np.full(len(ys), base), ys))
    for name, m in models.items():
        m.fit(Xtr, ytr)
        for split in rows:
            s = splits[split]
            rows[split].append(evaluate(name, m.predict_proba(X.iloc[s])[:, 1], y.iloc[s]))
    for split, r in rows.items():
        print(f"\n== {split} ==")
        print(pd.DataFrame(r).to_string(index=False, float_format="%.4f"))
    # Is the best test accuracy distinguishable from a coin flip?
    nt = len(y.iloc[splits["test"]])
    print(f"\n95% range for a coin flip on {nt} test windows: 0.5 ± {1.96 * 0.5 / np.sqrt(nt):.4f}")
    lr = models["logistic"][-1]
    coefs = pd.Series(lr.coef_[0], index=X.columns).sort_values(key=abs, ascending=False)
    print("\nTop logistic coefficients (standardized):\n" + coefs.head(8).to_string(float_format="%.4f"))

if __name__ == "__main__":
    main()
