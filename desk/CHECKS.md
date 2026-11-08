# The 17 entry checks (the door)

Code: `facts.py` → `door()`. Numbers live in `config.py` → `ENTRY`.
Checks run in order and stop at the first failure. That failure's code is written to `checks.csv`.
**A missing field counts as a failure, never a pass.** No AI is involved; these are plain comparisons.

Sources: **rugcheck** (`api.rugcheck.xyz`) for token and holder data, **dexscreener** (`api.dexscreener.com`) for pool and price data. Both are free.

## Token safety (rugcheck)

| # | Fail code | Fails when | Why it matters |
|---|---|---|---|
| 1 | `no_report` | rugcheck has no risk score for the token | Too new to be indexed, or unknown. New doesn't mean clean. |
| 2 | `already_rugged` | rugcheck marks it rugged | Already dead. |
| 3 | `mint_open` | mint authority still exists | The creator can print unlimited new tokens and dump them. |
| 4 | `freeze_open` | freeze authority still exists | The creator can freeze your tokens so you can't sell. |
| 5 | `danger:<name>` | rugcheck lists any risk at "danger" level | rugcheck itself flags a serious problem. |
| 6 | `risk_score` | risk score > **40** (0–100, higher is worse) | Too many smaller warnings combined. |
| 7 | `lp_unlocked` | under **90%** of the biggest pool's liquidity is locked or burned | The creator could pull the liquidity, which is the classic rug. |

## Holders (rugcheck)

| # | Fail code | Fails when | Why it matters |
|---|---|---|---|
| 8 | `top10_heavy` | top 10 holders own > **30%** of supply (pool and locker wallets excluded) | A few whales can crash the price. |
| 9 | `dev_holds` | creator wallet owns > **5%** of supply | The creator has a big bag to dump. |
| 10 | `insiders` | any insider wallets detected (max **0**) | Insiders are linked wallets that bought together, which looks like a hidden dev stash. |
| 11 | `no_creator` | creator wallet unknown | The desk can't watch the creator's wallet, so the main exit rule can't work. |

## Pool and market (dexscreener)

| # | Fail code | Fails when | Why it matters |
|---|---|---|---|
| 12 | `no_pool` | no trading pair found, or price is 0 | Nothing to buy or sell. |
| 13 | `thin_pool` | liquidity < **$30,000** | High slippage, and the pool is easy to drain. |
| 14 | `ticket_too_big` | your $25 is > **1%** of the pool | Your own trade would move the price. |
| 15 | `too_fresh` | pair younger than **30 minutes** (or age unknown) | Most rugs happen in the first minutes. |
| 16 | `too_old` | pair older than **48 hours** | The early move is over. |
| 17 | `nobody_can_sell` | **20+** buys and **0** sells in the last hour | Likely a honeypot, where buying works and selling doesn't. |

## What the checks can't catch

- A rug done in **one transaction**, faster than the 20-second watch.
- Fake buzz from bots. Grok was meant to judge this, or you can check X yourself.
- Changes made after you buy. The exit rules in `watch.py` (creator wallet, top 10 holders, liquidity, price) cover those.

## Tuning

Change a number in `config.py` → `ENTRY` only, and write down why on the same day.
Never loosen a number just to let a token you like get through.
After a week, count the fail codes in `checks.csv` to see which checks block the most tokens.
