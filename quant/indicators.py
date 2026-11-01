import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()  # Wilder


def donchian(df: pd.DataFrame, n: int):
    """Range of the *previous* n candles (excludes current bar -> no lookahead)."""
    return df["high"].shift(1).rolling(n).max(), df["low"].shift(1).rolling(n).min()


def rolling_pct_rank(s: pd.Series, n: int) -> pd.Series:
    """Fraction of the previous n-1 values strictly below the current value (0..1)."""
    x = s.to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return pd.Series(out, index=s.index)
    w = np.lib.stride_tricks.sliding_window_view(x, n)
    valid = ~np.isnan(w).any(axis=1)
    out[n - 1:] = np.where(valid, (w[:, :-1] < w[:, -1:]).mean(axis=1), np.nan)
    return pd.Series(out, index=s.index)
