#!/usr/bin/env bash
# runs the whole paper desk in one terminal. ctrl-c to stop.
cd "$(dirname "$0")"
i=0
while true; do
  (( i % 12 == 0 )) && python scan.py
  (( i % 6 == 0 ))  && python pulse.py
  python watch.py --minutes 9 --every 20
  sleep 20; i=$((i+1))
  [[ $(date +%H:%M) > "21:00" && $(date +%H:%M) < "21:10" ]] && python report.py
done
