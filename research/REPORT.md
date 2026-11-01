# BTC 5-min Up/Down: research report (Oct 31, 2026)

**Goal:** 3%/day bankroll growth betting Polymarket's 5-minute crypto Up/Down markets.
**Result:** no strategy found that makes money after real costs. Best validated result: don't bet (0%/day).

## Data collected (all free, no accounts)
| Data | Source | Size |
|---|---|---|
| BTC/ETH/SOL/XRP 5-min market results + Chainlink start/end prices, 120 days | Polymarket Gamma API | ~34.5k windows per asset |
| Market price of "Up" at open and minutes 1–4 | Polymarket CLOB price history | ~138k markets |
| 1-minute spot candles, 121 days | Coinbase public API | ~174k minutes per asset |
| Live order book every 5 s and 1.5 s, plus Coinbase ticker | Polymarket CLOB and Coinbase, recorded live Oct 31 21:15–23:15 UTC | `live/` (not committed) |

## Costs (these decide everything)
- Spread: 1¢ about 96% of the time; top-of-book size is usually several hundred shares.
- Taker fee: 0.07 × p × (1 − p) per share, so 1.75¢ per share at p = 0.50, on every buy and every sell.
- Round trip at 0.50: about 1¢ spread + 3.5¢ fees. Buy-and-hold to settlement: about 0.5–1¢ + 1.75¢.

## What was tested (validation = Sep 13–Oct 7, test = Oct 7–31, never used to choose)
| Idea | Finding |
|---|---|
| Model on past price history (earlier session) | ≈ coin flip |
| Recalibrated market price at minute 0–4 | Market is well calibrated; no bets clear costs |
| Back the favorite / follow or fade price moves within the window | Negative after costs on val |
| Gradient boosting / logistic on market path, previous windows, volatility, hour | Log loss within ±0.003 of the market's own price |
| Coinbase spot vs market, minute data | Apparent edge was look-ahead from ~40 s stale price samples; with proper timing, the market beats the spot model |
| Older BTC market price → ETH market (and reverse) | Gain ≤ 0.0003 log loss; nothing |
| ETH, SOL, XRP instead of BTC | Same; only XRP at open looked good on val (+2.75%/day) |
| XRP odd opening quotes | Profit came from ~20 bets on one night of odd 0.31/0.69 quotes. **Test: −1.25%/day, −27%, max drawdown 46%** |
| Live latency trade: buy after a Coinbase jump, exit 5–20 s later | Early +¢ signal vanished with more data. Final (≈2 h, 21–25 windows, 2 recorders): every variant negative, −0.5 to −2.8¢/share after fees. Polymarket moves in the same 5 s as Coinbase (corr 0.46–0.63); leftover lag corr 0.07–0.09 |
| Live: buy after a jump, hold to settlement | Final: 12–37 trades per variant; results flip sign between the two recordings of the same period (−4.6¢ to +6.1¢/share) — noise, not an edge |

Full experiment log: `results.tsv`.

## Why 3%/day isn't realistic here
- The market's price is already an accurate probability at every minute.
- Costs are about 2–5% of each stake, which is larger than any edge found.
- At 3%/day compounded, $1,000 becomes about $48M in a year. That kind of edge does not exist in a liquid public market.

## Where an edge could still exist (not testable with free historical data)
1. **Market making:** post limit orders and earn the spread plus Polymarket's maker rebates (20% of 5-min crypto fees), with no taker fee. This needs live order-book and fill data, plus inventory-risk management.
2. **Sub-second latency:** websocket feeds and co-located execution. Polling once a second is too slow; most of the market's reaction happens within the same 5 s.
3. **Rare anomalies** (like the XRP quote episodes): would need a live scanner that checks real asks before acting. Episodes are rare and inconsistent.

## Reproduce
```
python fetch_btc_5m_updown.py 120 data/btc_5m_120d.csv btc
python fetch_updown_odds.py data/btc_5m_120d.csv data/btc_5m_120d_odds.csv
python fetch_spot_1m.py BTC-USD 121 data/btc_spot_1m.csv
cd research && ASSET=btc python backtest.py      # edit strategy.py; see program.md
python live/recorder.py HOURS live/out.jsonl 1.5 && python live/analyze.py live/out.jsonl
```
