import numpy as np
import pandas as pd

from quant.backtest import position_size, run_backtest
from quant.config import Config
from quant.data import synthetic_klines
from quant.indicators import donchian
from quant.strategy import build_signals


def test_position_size_matches_risk():
    cfg = Config(risk_per_trade=0.005, max_leverage=10)
    qty = position_size(1000, 100_000, 100_000 * (1 - 0.0075), cfg)
    assert abs(qty * 100_000 - 666.67) < 0.1


def test_leverage_cap():
    cfg = Config(risk_per_trade=0.05, max_leverage=2)
    assert position_size(1000, 100, 99.99, cfg) * 100 <= 2000 + 1e-9


def test_donchian_excludes_current_bar():
    df = pd.DataFrame({"high": [1, 2, 3, 10.0], "low": [0, 1, 2, 3.0]})
    hi, _ = donchian(df, 2)
    assert hi.iloc[3] == 3  # bar 3's own high (10) not included


def test_no_lookahead_in_signals():
    df = synthetic_klines(6000, seed=1)
    cfg = Config()
    full = build_signals(df, cfg)["signal"]
    trunc = build_signals(df.iloc[:5000], cfg)["signal"]
    assert (full.iloc[:5000].values == trunc.values).all()


def test_signals_are_exclusive_and_backtest_runs():
    df = synthetic_klines(15000, seed=2)
    cfg = Config()
    sig = build_signals(df, cfg)
    assert set(np.unique(sig["signal"])) <= {-1, 0, 1}
    trades, eq = run_backtest(sig, cfg)
    assert len(eq) == len(df) and eq.notna().all()
    if not trades.empty:
        # entries strictly after signal bar, no overlapping positions
        assert (trades["entry_time"].iloc[1:].values >= trades["exit_time"].iloc[:-1].values).all()
        # a stop-loss exit should cost roughly 1R (plus costs)
        sl = trades[trades["reason"] == "sl"]
        if len(sl):
            assert sl["r_multiple"].between(-1.3, -0.9).all()
