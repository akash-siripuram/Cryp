import numpy as np
import pandas as pd


def summarize(trades: pd.DataFrame, equity: pd.Series, bars_per_year: float = 96 * 365) -> dict:
    if trades.empty:
        return {"trades": 0}
    pnl = trades["pnl"]
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    rets = equity.pct_change().dropna()
    dd = equity / equity.cummax() - 1
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    return {
        "trades": int(len(trades)),
        "win_rate": float((pnl > 0).mean()),
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
        "expectancy_R": float(trades["r_multiple"].mean()),
        "avg_win_R": float(trades.loc[pnl > 0, "r_multiple"].mean()) if len(wins) else 0.0,
        "avg_loss_R": float(trades.loc[pnl <= 0, "r_multiple"].mean()) if len(losses) else 0.0,
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1),
        "cagr": float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1),
        "sharpe": float(rets.mean() / rets.std() * np.sqrt(bars_per_year)) if rets.std() > 0 else 0.0,
        "max_drawdown": float(dd.min()),
        "fees_paid": float(trades["fees"].sum()),
        "funding_paid": float(trades["funding"].sum()),
        "long_trades": int((trades["side"] == 1).sum()),
        "short_trades": int((trades["side"] == -1).sum()),
        "exit_reasons": trades["reason"].value_counts().to_dict(),
    }


ACCEPT = {"profit_factor": (">", 1.3), "sharpe": (">", 1.0),
          "max_drawdown": (">", -0.15), "expectancy_R": (">", 0.0), "trades": (">=", 500)}


def acceptance(m: dict) -> dict:
    out = {}
    for k, (op, thr) in ACCEPT.items():
        v = m.get(k, 0)
        out[k] = bool(v > thr if op == ">" else v >= thr)
    return out
