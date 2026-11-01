# Memecoins: Pump or Dump? A solution notebook

Competition: https://www.kaggle.com/competitions/memecoins-pump-or-dump

- `pump_or_dump_ev_policy.ipynb`: the notebook to submit. CPU only, no internet, trains inside the run.
- `solution.py`: the same code as a script (`# %%` cells). The notebook is generated from it.

## Why it should beat the starter notebooks

| Starter 2 | This notebook |
|---|---|
| Trains on the 30-day `train.csv` only | Also trains on `train_archive.csv`, with recency weights (30-day half-life) |
| Fixed take-profit of 5x | One calibrated classifier per level, P(max_x >= L) for L in 3, 4, 5, 6.5, 8, 10, 13, 17. Each token gets the tp with the best expected value. |
| Threshold = top q% of scores | Buys only if EV = P·(L−1.3) + (1−P)·E[held, miss] > `MARGIN`. That is an absolute rule fixed from training, so it is legal. |
| About 50 features | About 120 features: holder concentration, creator holdings and sells, sniper share, sell pressure inside the minute, dumping by curve holders, pool depth, regime, sniper and buyer reputation, creator history |

Leakage controls: every history feature (reputation, regime, creator outcomes) uses only tokens
with `mt < UTC-day-start − 2h`. That is exactly what is known on the test day, so train and test
features have the same distribution. Each token is decided independently.

## Tune before you submit (on the real data, inside Kaggle)

Set the environment variables in the first cell, or edit the constants:

```
PD_VALIDATE=1 PD_VAL_DAYS=14
```

This prints the embargoed walk-forward PnL for each margin, next to a fixed-tp=5 baseline.
Pick the `MARGIN` with the best total and the most green days. Prefer the stable choice over the
single best one: the daily metric is very noisy. Then submit with validation off. Runtime goes up
with validation on, roughly 14 extra fits of the full model.
