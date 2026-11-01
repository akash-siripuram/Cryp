"""Chronological splits + walk-forward parameter selection (small, coarse grid to limit overfit)."""
import itertools
from dataclasses import replace

import pandas as pd

from .backtest import run_backtest
from .config import Config
from .metrics import summarize
from .strategy import build_signals

GRID = {"donchian_len": [20, 40], "sl_atr": [1.5, 2.0], "tp_atr": [2.5, 3.5], "confirm_next_bar": [True, False]}


def _score(m):  # optimise expectancy, but require a minimum sample
    return m.get("expectancy_R", -9) if m.get("trades", 0) >= 30 else -9


def walk_forward(df, cfg: Config, funding=None, train_months=12, test_months=3, warmup_bars=3000):
    start, end = df.index[0], df.index[-1]
    t0 = start + pd.DateOffset(months=train_months)
    oos_trades, chosen = [], []
    while t0 + pd.DateOffset(months=test_months) <= end + pd.Timedelta("1D"):
        t1 = t0 + pd.DateOffset(months=test_months)
        train = df[(df.index >= t0 - pd.DateOffset(months=train_months)) & (df.index < t0)]
        best, best_s = cfg, -1e9
        for combo in itertools.product(*GRID.values()):
            c = replace(cfg, **dict(zip(GRID, combo)))
            tr, eq = run_backtest(build_signals(train, c), c, funding)
            s = _score(summarize(tr, eq))
            if s > best_s:
                best, best_s = c, s
        # test slice includes warmup history for indicators, trades only counted inside window
        test = df[(df.index >= t0 - pd.Timedelta(minutes=15 * warmup_bars)) & (df.index < t1)]
        sig = build_signals(test, best)
        sig.loc[sig.index < t0, "signal"] = 0
        tr, _ = run_backtest(sig, best, funding)
        if not tr.empty:
            oos_trades.append(tr)
        chosen.append({"test_start": t0.date(), "test_end": t1.date(), "train_score_R": round(best_s, 3),
                       **{k: getattr(best, k) for k in GRID}, "oos_trades": len(tr),
                       "oos_R": round(tr["r_multiple"].mean(), 3) if len(tr) else None})
        t0 = t1
    oos = pd.concat(oos_trades, ignore_index=True) if oos_trades else pd.DataFrame()
    return oos, pd.DataFrame(chosen)
