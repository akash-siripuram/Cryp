# Smart-wallet research: first-hour buyers of daily pump.fun winners (Nov 1, 2026)

**Question:** if we find the wallets that bought each day's top pump.fun coin in its first hour, and
follow them, do we catch the next winner?
**Answer: no.** The wallets that keep showing up early in winners are sniper bots that buy almost
every launch. Of the coins they bought recently, **0 of 77 is worth ≥ $100k today** (60% are
already dead). Copying them means buying mostly coins that go to zero.

## Data (all free, on-chain)
| Step | Source | Result |
|---|---|---|
| Daily winner, last 500 days | CoinGecko "Pump.fun Ecosystem" (3,399 coins). Proxy for "top trending by EOD": the coin whose all-time high fell on that day, largest peak market cap | 472 winner-days (median peak market cap $3.2M) |
| First-hour trades per winner | Solana public RPC: pump.fun bonding-curve account → first 60 trades in the first hour (creator's launch buy removed) | 243 winners processed in the time budget (every other day across all 500 days), 7,567 early buys, 6,247 wallets |
| Entry price in USD | SOL spent ÷ tokens received × SOL/USD that day (Coinbase) | per wallet per coin |
| What smart wallets buy beyond winners | Solana RPC wallet history + DexScreener market caps today | 15 smart and 30 comparison wallets |

pump.fun's own API is behind a Cloudflare bot check and DexScreener/GeckoTerminal only show what's
trending now, so neither could supply 500 days of history.

## Results
**1. Being early in a winner pays on paper but not in practice.** Median first-hour buyer of a winner:
- −2% realized on what they sold within the hour (30% sold some),
- +119% if held until today (but 33% are at a loss even on these *winners*),
- +33,000% if sold exactly at the all-time high (nobody does this; it's the theoretical ceiling).

**2. The same wallets show up early again and again (out of sample).** Chronological split: train =
first 70% of winner-days (to May 9, 2026), test = last 30%.

| Wallet group (from train) | Wallets | Early in ≥1 test winner |
|---|---|---|
| Early in ≥5 train winners | 48 | 48% |
| Early in ≥3 train winners | 162 | 32% |
| Early in ≥2 train winners | 452 | 19% |
| Early in exactly 1 | 4,263 | 1.7% |

Train hits and test hits correlate at 0.67. At first sight, a strong "smart wallet" signal.

**3. But those wallets buy almost everything.** Checking the coins they bought recently, winners
and losers alike:

| | Smart wallets (top 15) | Comparison (30 one-time early buyers) |
|---|---|---|
| Distinct coins bought (sample) | 77 | 93 |
| Worth ≥ $100k today | **0%** | 1.1% |
| Worth ≥ $1M today | 0% | 0% |
| Dead / not on DexScreener | 60% | 96% |
| Median SOL per buy | 0.40 | 0.11 |

The top wallets typically buy within ~5 seconds of launch, often have vanity addresses
(`nya666…`, `DDDD…`, `696969…`, `BoBo…`) and spread small buys across many launches. Showing up
early in a winner is guaranteed if you buy every launch; it says nothing about picking.
Also seen: wallets buying in the **same second as launch** on several winners (rank 1, 0 s), which
is the pattern of creators or insiders buying through a second wallet, not skill.

## Why the "daily trending coin + smart wallets" plan doesn't work as stated
- **Hindsight:** the daily winner is only known at the end of the day; the first hour is long gone.
- **Survivorship:** we only see wallets on coins that won. Their losers are invisible unless you
  check their full history, and that history is mostly losers.
- **Speed:** the repeat early buyers act in seconds. A human checking a list before entering is
  minutes late, buying from them.
- **Base rate:** only a small share of pump.fun launches ever reach a meaningful market cap.

## Limitations
- 243 of 472 winner-days processed (rate limits on the free RPC); results were stable as data grew
  from 117 → 215 → 243 winners.
- Hit-rate check used ~40 recent transactions per wallet; a smart-wallet coin's median age was 18
  days (46 coins were ≥ 7 days old, still 0 worth ≥ $100k).
- "Winner" = CoinGecko-listed coins only; "profit %" uses entry vs ATH/current price, not each
  wallet's full exit history.

## What could still be worth testing
1. **Filter out bots** (buys/day, seconds after launch, number of distinct launches) and look for
   wallets with few, larger, later buys that still hit winners. That's a different, smaller group
   than the repeat early buyers. It needs full wallet histories (a paid RPC/indexer like Helius
   or Birdeye would make this feasible).
2. **Score whole wallets on all their buys** (precision, % return per buy), not on presence in
   winners.
3. **Paper-trade any shortlist forward** for weeks before using real money.

## Files
`select_winners.py`, `early_buyers.py`, `analyze.py`, `wallet_hitrate.py`, `rpc.py`;
`data/winners.json`, `data/smart_wallets.csv`, `data/analysis_latest.txt`, `data/hitrate_*.json`.
