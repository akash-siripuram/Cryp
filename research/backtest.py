"""FIXED evaluation harness for the autoresearch loop. DO NOT MODIFY.

Simulates betting a bankroll on Polymarket BTC 5-min Up/Down markets.

Rules:
- Data is split chronologically: train (first 60%), val (next 20%), test (last 20%).
- strategy.fit(train_df) is called once; strategy.decide(df) returns, for every
  row, a side (+1 Up, -1 Down, 0 skip), a stake as a fraction of bankroll, and
  optionally an entry minute k in 0..4 (default 0 = at window open).
- A row's decision may use only that row's fields known at entry (start_ts,
  start_utc, slug, price_to_beat, p_up_open, and p_up_1m..p_up_km) plus anything
  from earlier rows. The harness checks this by re-running decide() on
  truncated copies whose not-yet-known fields are scrambled.
- You buy at the market price at entry (p_up_km for Up, 1 - p_up_km for Down)
  plus SLIPPAGE, and pay FEE on the stake. A winning share pays $1.
- Stake per bet is capped at MAX_FRACTION of bankroll.

Score = mean daily log-growth of bankroll on VAL, shown as % per day.
Test is only evaluated with --final; never use it to choose between ideas.
"""
import sys, importlib
import numpy as np
import pandas as pd

DATA = "../data/btc_5m_120d_odds.csv"
SLIPPAGE = 0.01      # dollars per share above the quoted price
FEE = 0.01           # fraction of stake (approximate taker fee)
MAX_FRACTION = 0.10
PRE_OPEN = ["start_ts", "start_utc", "slug", "price_to_beat", "p_up_open"]
MINUTE_COLS = ["p_up_open", "p_up_1m", "p_up_2m", "p_up_3m", "p_up_4m"]

def unpack(out, n):
    side, frac = np.asarray(out[0]), np.asarray(out[1], float)
    k = np.asarray(out[2], int) if len(out) > 2 else np.zeros(n, int)
    return side, frac, np.clip(k, 0, 4)
GOAL = 3.0           # % per day

def load():
    d = pd.read_csv(DATA).sort_values("start_ts").reset_index(drop=True)
    d = d[d["result"].isin(["Up", "Down"]) & d["p_up_open"].between(0.02, 0.98)]
    for a, b in zip(MINUTE_COLS, MINUTE_COLS[1:]):
        d[b] = d[b].fillna(d[a])
    d = d.reset_index(drop=True)
    n = len(d); a, b = int(n * .6), int(n * .8)
    return d.iloc[:a].reset_index(drop=True), d.iloc[a:b].reset_index(drop=True), d.iloc[b:].reset_index(drop=True)

def check_causal(strategy, df, trials=5, seed=0):
    side, frac, ent = unpack(strategy.decide(df.copy()), len(df))
    rng = np.random.default_rng(seed)
    rows = list(rng.integers(len(df) // 4, len(df) - 1, trials))
    rows += list(np.flatnonzero(side != 0)[-trials:])          # also check rows that bet
    for k in rows:
        cut = df.iloc[:k + 1].copy()
        known = PRE_OPEN + MINUTE_COLS[1:ent[k] + 1]
        post = [c for c in cut.columns if c not in known]
        cut.loc[k, post] = df.loc[(k + 7) % len(df), post].values   # scramble row k's unknowns
        s2, f2, e2 = unpack(strategy.decide(cut), len(cut))
        if s2[k] != side[k] or not np.isclose(f2[k], frac[k]) or e2[k] != ent[k]:
            raise SystemExit(f"LOOK-AHEAD DETECTED at row {k}: decision changed when future/outcome data changed")

def simulate(df, out):
    side, frac, ent = unpack(out, len(df))
    frac = np.clip(frac, 0, MAX_FRACTION)
    up = (df["result"] == "Up").values
    p_up = df[MINUTE_COLS].values[np.arange(len(df)), ent]
    price = np.minimum(np.where(side > 0, p_up, 1 - p_up) + SLIPPAGE, 0.999)
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
        r = simulate(df, strategy.decide(df.copy()))
        print(f"--- {name} ---")
        for k, v in r.items():
            print(f"{name}_{k}: {v:.4f}" if isinstance(v, float) else f"{name}_{k}: {v}")
    print(f"goal_pct_per_day: {GOAL}")

if __name__ == "__main__":
    main()
