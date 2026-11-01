"""Historical data from Binance's public archive (data.binance.vision) + live REST.

Archive is the recommended source for backtests: complete, free, no API key.
"""
import io
import os
import zipfile
from datetime import date

import numpy as np
import pandas as pd
import requests

ARCHIVE = "https://data.binance.vision/data/futures/um/monthly"
FAPI = "https://fapi.binance.com"
KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
         "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
CACHE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache")


def _months(start: str, end: str):
    y, m = map(int, start.split("-")[:2])
    ey, em = map(int, end.split("-")[:2])
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m > 12:
            y, m = y + 1, 1


def _fetch_zip_csv(url: str) -> pd.DataFrame | None:
    r = requests.get(url, timeout=60)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        raw = z.read(z.namelist()[0]).decode()
    first = raw.split("\n", 1)[0]
    has_header = not first.split(",")[0].strip().isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if has_header else None)


def load_klines(symbol="BTCUSDT", interval="15m", start="2021-01", end=None) -> pd.DataFrame:
    end = end or date.today().strftime("%Y-%m")
    os.makedirs(CACHE, exist_ok=True)
    frames = []
    for mo in _months(start, end):
        path = os.path.join(CACHE, f"{symbol}-{interval}-{mo}.parquet")
        if os.path.exists(path):
            frames.append(pd.read_parquet(path))
            continue
        df = _fetch_zip_csv(f"{ARCHIVE}/klines/{symbol}/{interval}/{symbol}-{interval}-{mo}.zip")
        if df is None:  # current month not archived yet
            continue
        df.columns = KCOLS
        df = df[["open_time", "open", "high", "low", "close", "volume"]].astype(float)
        df.to_parquet(path)
        frames.append(df)
    if not frames:
        raise RuntimeError("No kline data downloaded")
    return _finalize(pd.concat(frames))


def load_funding(symbol="BTCUSDT", start="2021-01", end=None) -> pd.Series:
    """Funding rate per 8h settlement, indexed by settlement time (UTC)."""
    end = end or date.today().strftime("%Y-%m")
    os.makedirs(CACHE, exist_ok=True)
    out = []
    for mo in _months(start, end):
        path = os.path.join(CACHE, f"{symbol}-funding-{mo}.parquet")
        if os.path.exists(path):
            out.append(pd.read_parquet(path))
            continue
        df = _fetch_zip_csv(f"{ARCHIVE}/fundingRate/{symbol}/{symbol}-fundingRate-{mo}.zip")
        if df is None:
            continue
        df = df.iloc[:, [0, 2]]
        df.columns = ["time", "rate"]
        df = df.astype(float)
        df.to_parquet(path)
        out.append(df)
    if not out:
        return pd.Series(dtype=float)
    f = pd.concat(out).drop_duplicates("time")
    unit = "us" if f["time"].max() > 1e14 else "ms"
    return pd.Series(f["rate"].values, index=pd.to_datetime(f["time"], unit=unit, utc=True)).sort_index()


def fetch_recent_klines(symbol="BTCUSDT", interval="15m", limit=1000) -> pd.DataFrame:
    """Live REST (public). Used by the paper trader."""
    r = requests.get(f"{FAPI}/fapi/v1/klines",
                     params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=20)
    r.raise_for_status()
    df = pd.DataFrame(r.json(), columns=KCOLS)
    df = df[["open_time", "open", "high", "low", "close", "volume", "close_time"]].astype(float)
    now_ms = pd.Timestamp.utcnow().value // 1_000_000
    df = df[df["close_time"] < now_ms]  # drop the still-forming candle
    return _finalize(df.drop(columns="close_time"))


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    unit = "us" if df["open_time"].max() > 1e14 else "ms"  # archive switched to µs in 2025
    df = df.copy()
    df.index = pd.to_datetime(df["open_time"], unit=unit, utc=True)
    df = df.drop(columns="open_time")
    return df[~df.index.duplicated()].sort_index()


def synthetic_klines(n=20_000, seed=0, freq="15min") -> pd.DataFrame:
    """Regime-switching random walk for tests/offline demos. Has NO real edge."""
    rng = np.random.default_rng(seed)
    regime = np.repeat(rng.choice([-1, 0, 1], size=n // 500 + 1), 500)[:n]
    vol = 0.002 * np.exp(rng.normal(0, 0.3, n).cumsum() * 0.01)
    rets = regime * 0.0001 + rng.normal(0, 1, n) * vol
    close = 30_000 * np.exp(np.cumsum(rets))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0, 1, n)) * vol * close
    df = pd.DataFrame({
        "open": open_, "close": close,
        "high": np.maximum(open_, close) + spread,
        "low": np.minimum(open_, close) - spread,
        "volume": rng.lognormal(5, 0.5, n) * (1 + 50 * np.abs(rets)),
    }, index=pd.date_range("2022-01-01", periods=n, freq=freq, tz="UTC"))
    return df
