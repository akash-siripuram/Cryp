"""CLI: download data, backtest, chronological split, walk-forward.

  python run_backtest.py --start 2021-01 --end 2026-09
  python run_backtest.py --synthetic          # offline smoke test (no edge expected)
  python run_backtest.py --paper              # live paper trading loop
"""
import argparse
import json
from dataclasses import replace

import numpy as np
import pandas as pd

from quant.backtest import run_backtest
from quant.config import Config
from quant.data import load_funding, load_klines, synthetic_klines
from quant.metrics import acceptance, summarize
from quant.strategy import build_signals
from quant.walkforward import walk_forward


def show(title, m):
    print(f"\n=== {title} ===")
    print(json.dumps(m, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--paper", action="store_true")
    ap.add_argument("--risk", type=float, default=0.005)
    ap.add_argument("--no-walkforward", action="store_true")
    a = ap.parse_args()
    cfg = Config(risk_per_trade=a.risk)

    if a.paper:
        from quant.paper import run
        return run(cfg)

    if a.synthetic:
        df, funding = synthetic_klines(), None
    else:
        df = load_klines(cfg.symbol, cfg.exec_tf, a.start, a.end)
        funding = load_funding(cfg.symbol, a.start, a.end)
    print(f"Bars: {len(df)}  {df.index[0]} -> {df.index[-1]}")

    # Chronological split: 60% train / 20% validation / 20% test (default params, no fitting)
    n = len(df)
    cuts = {"train": (0, int(n * .6)), "validation": (int(n * .6), int(n * .8)), "test": (int(n * .8), n)}
    sig = build_signals(df, cfg)
    for name, (i0, i1) in cuts.items():
        s = sig.copy()
        s.iloc[:i0, s.columns.get_loc("signal")] = 0
        tr, eq = run_backtest(s.iloc[:i1], cfg, funding)
        eq = eq.iloc[i0:]
        tr = tr[tr["entry_time"] >= df.index[i0]] if not tr.empty else tr
        m = summarize(tr, eq / eq.iloc[0] * cfg.initial_equity)
        show(f"{name} (default params)", m)

    tr, eq = run_backtest(sig, cfg, funding)
    full = summarize(tr, eq)
    show("FULL PERIOD", full)
    show("Acceptance checks (full period)", acceptance(full))
    tr.to_csv("trades.csv", index=False)

    # Cost sensitivity: does the edge survive doubled costs?
    c2 = replace(cfg, taker_fee=cfg.taker_fee * 2, maker_fee=cfg.maker_fee * 2, slippage_bps=cfg.slippage_bps * 2)
    tr2, eq2 = run_backtest(build_signals(df, c2), c2, funding)
    m2 = summarize(tr2, eq2)
    show("2x costs", {k: m2.get(k) for k in ("trades", "profit_factor", "expectancy_R", "total_return", "max_drawdown")})

    if not a.no_walkforward:
        oos, picks = walk_forward(df, cfg, funding)
        print("\n=== Walk-forward parameter picks ===")
        print(picks.to_string(index=False))
        if not oos.empty:
            # compound OOS R-multiples at the configured risk
            eq_oos = cfg.initial_equity * np.cumprod(1 + cfg.risk_per_trade * oos["r_multiple"].values)
            eq_s = pd.Series(np.r_[cfg.initial_equity, eq_oos],
                             index=pd.DatetimeIndex([oos["entry_time"].iloc[0]]).append(pd.DatetimeIndex(oos["exit_time"])))
            show("WALK-FORWARD OUT-OF-SAMPLE", summarize(oos, eq_s, bars_per_year=len(oos) / max(
                (eq_s.index[-1] - eq_s.index[0]).days / 365.25, 1e-9)))


if __name__ == "__main__":
    main()
