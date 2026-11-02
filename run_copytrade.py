"""Paper copy-trade the wallets in watchlist.txt. Runs until stopped (Ctrl+C).

  python run_copytrade.py                      # 0.5 SOL per copy
  python run_copytrade.py --size 0.2 --poll 15
Report refreshes every 5 min in reports/copytrade.md; state in reports/copytrade_state.json (safe to restart).
Run it for 2-4 weeks on an always-on machine before drawing conclusions.
"""
import argparse

from smartmoney.copytrade import run

ap = argparse.ArgumentParser()
ap.add_argument("--watchlist", default="watchlist.txt")
ap.add_argument("--size", type=float, default=0.5)
ap.add_argument("--poll", type=float, default=20)
ap.add_argument("--slippage", type=float, default=0.03)
a = ap.parse_args()
wallets = [l.strip() for l in open(a.watchlist) if l.strip() and not l.startswith("#")]
run(wallets, poll_s=a.poll, size_sol=a.size, slippage=a.slippage)
