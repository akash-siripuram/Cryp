"""Signal generation. All columns at bar t use only info available at t's close."""
import numpy as np
import pandas as pd

from .config import Config
from .indicators import atr, donchian, ema, rolling_pct_rank

_TF = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}


def trend_filter(df: pd.DataFrame, cfg: Config) -> pd.Series:
    """+1 / -1 / 0 from higher-TF EMA fast vs slow, aligned without lookahead."""
    htf = df.resample(_TF[cfg.trend_tf], label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f, s = ema(htf["close"], cfg.ema_fast), ema(htf["close"], cfg.ema_slow)
    trend = np.sign(f - s).where(s.notna(), 0.0)
    # An HTF bar labelled T is only known at T + period. Shift index so it applies afterwards.
    trend.index = trend.index + pd.Timedelta(_TF[cfg.trend_tf])
    exec_close_time = df.index + pd.Timedelta(_TF[cfg.exec_tf])
    return pd.Series(trend.reindex(exec_close_time, method="ffill").fillna(0).values, index=df.index)


def build_signals(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(df, cfg.atr_len)
    out["dc_hi"], out["dc_lo"] = donchian(df, cfg.donchian_len)
    out["vol_avg"] = df["volume"].shift(1).rolling(cfg.vol_len).mean()
    out["atr_rank"] = rolling_pct_rank(out["atr"], cfg.atr_regime_len)
    out["trend"] = trend_filter(df, cfg)

    vol_ok = df["volume"] > cfg.vol_mult * out["vol_avg"]
    atr_ok = out["atr_rank"] <= cfg.atr_max_pct
    brk_up = (df["close"] > out["dc_hi"]) & vol_ok & atr_ok & (out["trend"] > 0)
    brk_dn = (df["close"] < out["dc_lo"]) & vol_ok & atr_ok & (out["trend"] < 0)

    if cfg.confirm_next_bar:
        # Breakout on bar t-1 confirmed if bar t also closes beyond the *same* level.
        lvl_hi, lvl_lo = out["dc_hi"].shift(1), out["dc_lo"].shift(1)
        long_sig = brk_up.shift(1, fill_value=False) & (df["close"] > lvl_hi)
        short_sig = brk_dn.shift(1, fill_value=False) & (df["close"] < lvl_lo)
    else:
        long_sig, short_sig = brk_up, brk_dn

    # Mutually exclusive by construction (trend sign), but enforce anyway: OCO.
    out["signal"] = np.where(long_sig, 1, np.where(short_sig, -1, 0))
    return out
