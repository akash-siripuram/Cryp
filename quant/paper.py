"""Paper trader: same signal code as the backtest, run on live closed candles.

No real orders are sent. State persists in a JSON file so restarts are safe.

OCO handling mirrors what a live futures implementation must do (Binance USDT-M has no
native OCO): after entry, a stop (SL) and a take-profit are both "resting"; when one
fills the other is cancelled, and the position is verified flat before re-arming.
"""
import json
import logging
import os
import time
from dataclasses import asdict

import pandas as pd

from .backtest import position_size
from .config import Config
from .data import fetch_recent_klines
from .strategy import build_signals

log = logging.getLogger("paper")


class PaperBroker:
    def __init__(self, cfg: Config, state_path="paper_state.json"):
        self.cfg, self.path = cfg, state_path
        self.state = {"equity": cfg.initial_equity, "position": None, "pending": None,
                      "last_bar": None, "trades": []}
        if os.path.exists(state_path):
            with open(state_path) as f:
                self.state.update(json.load(f))

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2, default=str)
        os.replace(tmp, self.path)

    # --- per closed candle -------------------------------------------------
    def on_bar(self, ts, bar, row):
        cfg, st = self.cfg, self.state
        slip = cfg.slippage_bps / 1e4

        # 1) fill pending entry at this bar's open
        if st["pending"] and st["position"] is None:
            p = st["pending"]
            entry = bar["open"] * (1 + p["side"] * slip)
            sl = entry - p["side"] * cfg.sl_atr * p["atr"]
            tp = entry + p["side"] * cfg.tp_atr * p["atr"]
            qty = position_size(st["equity"], entry, sl, cfg)
            st["position"] = {"side": p["side"], "entry": entry, "qty": qty, "sl": sl, "tp": tp,
                              "entry_time": str(ts), "bars": 0,
                              "fees": cfg.taker_fee * qty * entry}
            log.info("ENTRY %s qty=%.4f @%.2f SL=%.2f TP=%.2f (other side cancelled)",
                     "LONG" if p["side"] > 0 else "SHORT", qty, entry, sl, tp)
        st["pending"] = None

        # 2) manage open position: OCO between SL and TP
        pos = st["position"]
        if pos:
            pos["bars"] += 1
            s = pos["side"]
            hit = None
            if (s > 0 and bar["low"] <= pos["sl"]) or (s < 0 and bar["high"] >= pos["sl"]):
                gap = (s > 0 and bar["open"] <= pos["sl"]) or (s < 0 and bar["open"] >= pos["sl"])
                hit = ("sl", (bar["open"] if gap else pos["sl"]) * (1 - s * slip), cfg.taker_fee)
            elif (s > 0 and bar["high"] >= pos["tp"]) or (s < 0 and bar["low"] <= pos["tp"]):
                hit = ("tp", pos["tp"], cfg.maker_fee)
            elif pos["bars"] >= cfg.max_hold_bars:
                hit = ("time", bar["close"] * (1 - s * slip), cfg.taker_fee)
            if hit:
                reason, px, fee = hit
                pos["fees"] += fee * pos["qty"] * px
                pnl = s * (px - pos["entry"]) * pos["qty"] - pos["fees"]
                st["equity"] += pnl
                st["trades"].append({**pos, "exit": px, "exit_time": str(ts), "reason": reason, "pnl": pnl})
                st["position"] = None
                log.info("EXIT %s @%.2f pnl=%.2f equity=%.2f (sibling order cancelled)",
                         reason, px, pnl, st["equity"])

        # 3) new signal -> arm entry for next bar open (only if flat: OCO)
        if st["position"] is None and row["signal"] != 0:
            st["pending"] = {"side": int(row["signal"]), "atr": float(row["atr"]), "signal_time": str(ts)}
            log.info("SIGNAL %s at close %.2f", "LONG" if row["signal"] > 0 else "SHORT", bar["close"])

        st["last_bar"] = str(ts)

    def step(self):
        df = fetch_recent_klines(self.cfg.symbol, self.cfg.exec_tf, limit=1500)
        sig = build_signals(df, self.cfg)
        last = pd.Timestamp(self.state["last_bar"]) if self.state["last_bar"] else sig.index[-2]
        for ts, row in sig[sig.index > last].iterrows():
            self.on_bar(ts, row, row)
        self.save()


def run(cfg: Config, poll_seconds=30, state_path="paper_state.json"):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log.info("Paper trading %s %s config=%s", cfg.symbol, cfg.exec_tf, json.dumps(asdict(cfg)))
    b = PaperBroker(cfg, state_path)
    while True:
        try:
            b.step()
        except Exception as e:  # network hiccups etc. — never crash the loop
            log.warning("step failed: %s", e)
        time.sleep(poll_seconds)
