# autoresearch: BTC 5-min Up/Down strategy

Adapted from github.com/karpathy/autoresearch. The agent edits one file,
runs a fixed scorer, keeps changes that improve the score, reverts the rest.

## Files
- `backtest.py` — FIXED harness (data split, costs, look-ahead check, score). Never edit.
- `strategy.py` — the only file you edit. Implements `fit(train_df)` and
  `decide(df) -> (side, fraction)`.
- `results.tsv` — untracked log: `commit	val_pct_per_day	val_bets	status	description`.

## Metric
`val_pct_per_day` (mean daily log-growth on the validation split, after
slippage and fees). Goal: 3.0. Higher is better. A strategy that places few
bets (< 100 on val) is not trustworthy; treat it as discard unless it is
clearly robust.

## Loop
1. Edit `strategy.py` with one idea. `git commit`.
2. `python backtest.py > run.log 2>&1`; read `grep "^val_" run.log`.
3. Log the result in `results.tsv`.
4. If `val_pct_per_day` improved, keep the commit; otherwise `git reset --hard HEAD~1`.
5. Repeat.

## Rules
- Never read or score the test split while searching. Only at the very end run
  `python backtest.py --final` once on the chosen strategy.
- No look-ahead: a row's decision may use only its pre-open fields
  (`start_ts`, `price_to_beat`, `p_up_open`, and `p_up_1m`..`p_up_km` when entering at minute k) and earlier rows. The harness enforces this.
- Prefer simple strategies; many tried ideas inflate the chance a val win is luck.
