"""FIXED evaluation harness for the autoresearch loop. DO NOT MODIFY.

Simulates betting a bankroll on Polymarket BTC 5-min Up/Down markets.

Rules:
- Data is split chronologically: train (first 60%), val (next 20%), test (last 20%).
- strategy.fit(train_df) is called once; strategy.decide(df) returns, for every
  row, a side (+1 Up, -1 Down, 0 skip) and a stake as a fraction of bankroll.
- A row's decision may use only that row's pre-open fields (start_ts, start_utc,
  price_to_beat, p_up_open) and anything from earlier rows. The harness checks
  this by re-running decide() on truncated, scrambled copies.
- You buy at the market price at window open (p_up_open for Up, 1 - p_up_open
  for Down) plus SLIPPAGE, and pay FEE on the stake. A winning share pays $1.
- Stake per bet is capped at MAX_FRACTION of bankroll.

Score = mean daily log-growth of bankroll on VAL, shown as % per day.
Test is only evaluated with --final; never use it to choose between ideas.
"""
import sys, importlib
import numpy as np
import pandas as pd

DATA = "../btc_5m_updown_30d_odds.csv"
SLIPPAGE = 0.01      # dollars per share above the quoted price
FEE = 0.01           # fraction of stake (approximate taker fee)
MAX_FRACTION = 0.10
PRE_OPEN = ["start_ts", "start_utc", "slug", "price_to_beat", "p_up_open"]
GOAL = 3.0           # % per day

def load():
    d = pd.read_csv(DATA).sort_values("start_ts").reset_index(drop=True)
    d = d[d["result"].isin(["Up", "Down"]) & d["p_up_open"].between(0.02, 0.98)]
    d = d.reset_index(drop=True)
    n = len(d); a, b = int(n * .6), int(n * .8)
    return d.iloc[:a].reset_index(drop=True), d.iloc[a:b].reset_index(drop=True), d.iloc[b:].reset_index(drop=True)

def check_causal(strategy, df, trials=5, seed=0):
    side, frac = strategy.decide(df.copy())
    rng = np.random.default_rng(seed)
    for k in rng.integers(len(df) // 4, len(df) - 1, trials):
        cut = df.iloc[:k + 1].copy()
        post = [c for c in cut.columns if c not in PRE_OPEN]
        cut.loc[k, post] = df.loc[(k + 7) % len(df), post].values   # scramble row k's outcome
        s2, f2 = strategy.decide(cut)
        if s2[k] != side[k] or not np.isclose(f2[k], frac[k]):
            raise SystemExit(f"LOOK-AHEAD DETECTED at row {k}: decision changed when future/outcome data changed")

def simulate(df, side, frac):
    side = np.asarray(side); frac = np.clip(np.asarray(frac, float), 0, MAX_FRACTION)
    up = (df["result"] == "Up").values
    price = np.where(side > 0, df["p_up_open"], 1 - df["p_up_open"]) + SLIPPAGE
    win = np.where(side > 0, up, ~up)
    ret = np.where(side == 0, 0.0, frac * (np.where(win, 1 / price - 1, -1.0) - FEE))
    logg = np.log1p(ret)
    day = pd.to_datetime(df["start_ts"], unit="s").dt.floor("D")
    daily = pd.Series(logg).groupby(day.values).sum()
    bets = side != 0
    return {
        "pct_per_day": (np.exp(daily.mean()) - 1) * 100,
        "total_return_pct": (np.exp(logg.sum()) - 1) * 100,
        "max_drawdown_pct": (1 - np.exp(np.cumsum(logg) - np.maximum.accumulate(np.cumsum(logg)))).max() * 100,
        "bets": int(bets.sum()),
        "hit_rate": float(win[bets].mean()) if bets.any() else 0.0,
        "days": int(len(daily)),
    }

def main():
    final = "--final" in sys.argv
    train, val, test = load()
    strategy = importlib.import_module("strategy")
    strategy.fit(train.copy())
    check_causal(strategy, val)
    out = {"val": val}
    if final: out["test"] = test
    for name, df in out.items():
        r = simulate(df, *strategy.decide(df.copy()))
        print(f"--- {name} ---")
        for k, v in r.items():
            print(f"{name}_{k}: {v:.4f}" if isinstance(v, float) else f"{name}_{k}: {v}")
    print(f"goal_pct_per_day: {GOAL}")

if __name__ == "__main__":
    main()
