#!/bin/bash
# One experiment: commit strategy.py, score it, log to results.tsv.  Usage: ./run.sh "description"
cd "$(dirname "$0")"
git add strategy.py && git commit -qm "exp: $1" >/dev/null
python3 backtest.py > run.log 2>&1
pct=$(grep "^val_pct_per_day:" run.log | awk '{print $2}'); bets=$(grep "^val_bets:" run.log | awk '{print $2}')
[ -z "$pct" ] && { pct=0; bets=0; tail -5 run.log; }
printf '%s\t%s\t%s\t%s\t%s\n' "$(git rev-parse --short HEAD)" "$pct" "$bets" "?" "$1" >> results.tsv
grep -E "^val_" run.log
