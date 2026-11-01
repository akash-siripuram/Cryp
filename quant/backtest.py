"""Event-driven bar backtester.

Conservative assumptions:
- Signal at bar t close -> market entry at bar t+1 open (taker + slippage).
- If SL and TP both inside one bar, assume SL hit first.
- Gaps through stop fill at the open (worse price).
- Funding charged on notional at each 8h settlement while a position is open.
- One position at a time; opposite signals ignored while in a trade (the OCO "other leg" is cancelled).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config


@dataclass
class Trade:
    side: int
    entry_time: pd.Timestamp
    entry: float
    qty: float
    sl: float
    tp: float
    exit_time: pd.Timestamp | None = None
    exit: float | None = None
    reason: str = ""
    fees: float = 0.0
    funding: float = 0.0
    pnl: float = 0.0
    r_multiple: float = 0.0


def position_size(equity: float, entry: float, stop: float, cfg: Config) -> float:
    risk_cash = equity * cfg.risk_per_trade
    dist = abs(entry - stop)
    if dist <= 0:
        return 0.0
    qty = risk_cash / dist
    max_qty = equity * cfg.max_leverage / entry
    return min(qty, max_qty)


def run_backtest(sig: pd.DataFrame, cfg: Config, funding: pd.Series | None = None):
    slip = cfg.slippage_bps / 1e4
    o, h, l, c = (sig[k].to_numpy() for k in ("open", "high", "low", "close"))
    s, a = sig["signal"].to_numpy(), sig["atr"].to_numpy()
    idx = sig.index
    # funding settled during bar i (in (t_i, t_{i+1}]) -> per-bar summed rate
    fund_bar = np.zeros(len(sig))
    if cfg.use_funding and funding is not None and len(funding):
        f = funding[(funding.index > idx[0]) & (funding.index <= idx[-1])]
        pos_i = np.searchsorted(idx.values, f.index.values, side="left") - 1
        np.add.at(fund_bar, pos_i, f.values)

    equity = cfg.initial_equity
    eq_curve = np.full(len(sig), np.nan)
    trades: list[Trade] = []
    pos: Trade | None = None
    bars_held = 0

    for i in range(len(sig) - 1):
        if pos is not None:
            bars_held += 1
            exit_px, reason = None, ""
            if pos.side == 1:
                if o[i] <= pos.sl:
                    exit_px, reason = o[i], "sl_gap"
                elif l[i] <= pos.sl:
                    exit_px, reason = pos.sl, "sl"
                elif h[i] >= pos.tp:
                    exit_px, reason = max(pos.tp, o[i]), "tp"
            else:
                if o[i] >= pos.sl:
                    exit_px, reason = o[i], "sl_gap"
                elif h[i] >= pos.sl:
                    exit_px, reason = pos.sl, "sl"
                elif l[i] <= pos.tp:
                    exit_px, reason = min(pos.tp, o[i]), "tp"
            if exit_px is None and bars_held >= cfg.max_hold_bars:
                exit_px, reason = c[i], "time"
            if fund_bar[i]:
                pos.funding += pos.side * fund_bar[i] * pos.qty * c[i]  # longs pay positive funding
            if exit_px is not None:
                fee_rate = cfg.maker_fee if reason == "tp" else cfg.taker_fee  # TP as resting limit
                fill = exit_px if reason == "tp" else exit_px * (1 - pos.side * slip)
                pos.exit, pos.exit_time, pos.reason = fill, idx[i], reason
                pos.fees += fee_rate * pos.qty * fill
                gross = pos.side * (fill - pos.entry) * pos.qty
                pos.pnl = gross - pos.fees - pos.funding
                risk = abs(pos.entry - pos.sl) * pos.qty
                pos.r_multiple = pos.pnl / risk if risk else 0.0
                equity += pos.pnl
                trades.append(pos)
                pos = None

        eq_curve[i] = equity + (pos.side * (c[i] - pos.entry) * pos.qty if pos else 0.0)

        if pos is None and s[i] != 0 and np.isfinite(a[i]) and equity > 0:
            side = int(s[i])
            entry = o[i + 1] * (1 + side * slip)
            sl = entry - side * cfg.sl_atr * a[i]
            tp = entry + side * cfg.tp_atr * a[i]
            qty = position_size(equity, entry, sl, cfg)
            if qty > 0:
                pos = Trade(side, idx[i + 1], entry, qty, sl, tp,
                            fees=cfg.taker_fee * qty * entry)
                bars_held = -1  # entry bar processed next iteration counts as 0

    eq_curve[-1] = equity
    eq = pd.Series(eq_curve, index=idx).ffill()
    tdf = pd.DataFrame([t.__dict__ for t in trades])
    return tdf, eq
