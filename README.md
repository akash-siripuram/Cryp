# Cryp — Adaptive OCO Breakout research system

A Python backtester + paper trader for a dual-sided volatility breakout on **BTCUSDT perpetual**
(Binance USDT-M): 15m execution, 1h EMA50/200 trend filter, Donchian(20) breakout,
volume + ATR regime filters, ATR-based SL/TP, 0.5% risk per trade, OCO (only one side ever filled).

## Quick start
```bash
pip install -r requirements.txt
python run_backtest.py --start 2021-01 --end 2026-09   # downloads from data.binance.vision, cached in data_cache/
python run_backtest.py --synthetic                     # offline smoke test
python run_backtest.py --paper                         # live paper trading (needs fapi.binance.com access, no keys, no real orders)
python -m pytest -q tests
```
Parameters live in `quant/config.py`.

## Layout
| Module | Role |
|---|---|
| `quant/data.py` | Binance public archive (klines + funding), live REST for paper trading |
| `quant/indicators.py` | EMA, Wilder ATR, Donchian (previous N bars), rolling percentile |
| `quant/strategy.py` | Signals: close outside range, HTF trend, volume, ATR regime, optional next-bar confirmation. No lookahead (tested) |
| `quant/backtest.py` | Event-driven: entry at next open, SL-first when both hit in one bar, gap fills, taker/maker fees, slippage, 8h funding, risk-based sizing with leverage cap |
| `quant/metrics.py` | PF, Sharpe, expectancy (R), drawdown, acceptance thresholds |
| `quant/walkforward.py` | 12-month train / 3-month test rolling optimisation over a small grid |
| `quant/paper.py` | Paper broker with persistent state and OCO-style SL/TP handling |

## Results (Jan 2021 – Sep 2026, 201,504 15m bars, VIP0 fees, 2 bps slippage, real funding)

| Test | Trades | Win rate | Profit factor | Expectancy | Max DD |
|---|---|---|---|---|---|
| Default params, full period | 3,237 | 35.0% | 0.71 | −0.31R | −99% |
| Same, **zero costs** | 3,246 | 36.8% | 0.96 | −0.02R | −42% |
| No next-bar confirmation | 4,396 | 35.7% | 0.74 | −0.31R | −99.8% |
| Wider stops (3 / 6 ATR) | 2,004 | 32.5% | 0.81 | −0.15R | −78% |
| **Walk-forward out-of-sample** | 2,311 | 38.3% | 0.70 | −0.23R | −94% |

Train, validation and test splits are all negative, and 18 of 19 walk-forward quarters lose money.

**Conclusion: this strategy, as specified, has no edge on BTCUSDT 15m.** It is roughly break-even
*before* costs. On a ~0.45% stop, fees and slippage cost about 0.3R per trade, which turns it
into a reliable loser. That matches the research cited in the original plan: short-horizon
crypto momentum is smaller than transaction costs. **Do not trade it live.**

Directions worth testing next (the framework already supports them):
1. Slower timeframes (1h/4h execution), where costs are a smaller share of each move.
2. Maker-only (limit/retest) entries to cut taker fees.
3. Fading breakouts instead (the zero-cost win rate suggests false breakouts are common).
4. Adding a volatility-compression precondition (e.g. a Bollinger/Keltner squeeze) before breakouts.

## Live-trading notes
Binance USDT-M futures has no native OCO. A live engine must place reduce-only STOP_MARKET and
TAKE_PROFIT_MARKET orders, listen for fills on the user-data stream, cancel the sibling, and
**verify** the position is flat. Never assume a cancellation succeeded. Live order code is
deliberately not included.

> ⚠️ Earlier versions of `app.py` had testnet API keys committed. They are still in git history:
> revoke them in the Binance testnet console.
