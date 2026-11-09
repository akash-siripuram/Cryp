# DEV WATCH strategy: how to buy and sell

> Not financial advice. Most memecoins go to zero. This is a **paper** desk: fake money, real prices.

**Core idea:** a rug shows up in the creator's (dev's) wallet minutes before it shows up on the chart.
Buy only coins that pass 17 strict checks, then **watch the wallets, not the price**, and get out when the insiders move.

---

## 1. Money rules

| Rule | Value | Where |
|---|---|---|
| Bankroll | **$100** (paper) | `BANKROLL_USD` |
| Ticket size | **$25 per trade, flat**, never bigger after a win or a loss | `TICKET_USD` |
| Max open positions | **4**, so at most $100 in play | `MAX_OPEN` |
| Max new buys per day | **6** | `MAX_ENTRIES_PER_DAY` |
| Daily loss halt | realized **−$50** today means no new buys until tomorrow | `DAILY_LOSS_HALT_USD` |
| Cooldown | never re-buy a coin you closed in the last **24 h** | `COOLDOWN_HOURS` |
| Free cash | no buy if free cash < $25 | `book.cash()` |
| Paper slippage | buys fill **3% above** the screen price, sells **3% below** | `PAPER_SLIP_PCT` |

---

## 2. Buying: the entry funnel

A coin goes through these steps in order. **The first "no" ends it.** Every result is logged to `checks.csv`.

```
coin address
  -> Step 1  limits          (free, instant, no internet)
  -> Step 2  17 door checks  (free, code only)
  -> Step 3  X read          (optional, Grok, paid)
  -> Step 4  wallet snapshot (free, Solana RPC; fails = no trade)
  -> Step 5  BUY $25
```

### Step 0: finding coins
- **Manual:** find a Solana token address (DexScreener new pairs or trending, X, Telegram) and run `python enter.py <address>`.
- **Automatic:** `python scan.py` asks Grok for addresses that 3+ older, real X accounts are posting.

### Step 1: limits (`book.guard`)
Skip if any of these are true: daily loss halt hit, already holding it, 4 open already, less than $25 free cash, 6 buys already today, or closed in the last 24 h.

### Step 2: the 17 door checks (`facts.door`)
Data comes from rugcheck and dexscreener. **A missing number counts as a fail, never a pass.** Full detail is in [CHECKS.md](CHECKS.md).

| # | Check | Passes only if |
|---|---|---|
| 1 | Report exists | rugcheck has a risk score |
| 2 | Not rugged | rugcheck doesn't mark it rugged |
| 3 | Can't create new tokens | mint authority revoked |
| 4 | Can't freeze | freeze authority revoked |
| 5 | No danger flags | zero rugcheck "danger" risks |
| 6 | Risk score | ≤ 40 |
| 7 | Liquidity locked | ≥ 90% of the biggest pool locked or burned |
| 8 | No whales | top 10 holders ≤ 30% (pools and lockers excluded) |
| 9 | Creator holds little | creator ≤ 5% of supply |
| 10 | No insiders | 0 insider wallets |
| 11 | Creator known | creator wallet address exists |
| 12 | Pool exists | a trading pair with a price > 0 |
| 13 | Enough liquidity | ≥ $30,000 |
| 14 | Your trade is small | $25 ≤ 1% of the pool |
| 15 | Not too fresh | pair ≥ 30 minutes old |
| 16 | Not too old | pair ≤ 48 hours old |
| 17 | Selling works | not (20+ buys and 0 sells in the last hour) |

### Step 3: X read (optional)
Grok searches X: is the buzz organic or paid? Is it a copycat token? Was this creator tied to a rug before?
It buys only on **BUY with confidence ≥ 0.7**. This step costs money (~$3–7/day) and is not proven to add profit. You can skip it by checking X yourself.
> Note: the code currently always calls Grok here. A no-Grok switch isn't built yet.

### Step 4: wallet snapshot (`rpc.snapshot`)
At the moment of buying, record:
- total supply
- the **creator's balance** (`dev0`) and its share of supply (`dev0_pct`)
- the balance of **each of the top 10 holder accounts** (`holders0`)

If the snapshot fails, **there's no trade**: you can't guard what you can't see.

### Step 5: buy
Paper: $25 at screen price + 3%. The position is saved to `positions.json`, and `watch.py` guards it from the next tick.

---

## 3. Selling: the exit rules

`watch.py` checks every open position **every 20 seconds**.
Rules are checked **in this order, and the first one that fires wins.** The wallet rules come first because they show trouble earliest. Price comes last.

| Priority | Rule | Fires when | Sells |
|---|---|---|---|
| 1 | **Creator sold** | creator wallet is down **≥ 20%** from the snapshot. This only applies if the creator held ≥ 0.5% at entry. | **all** |
| 2 | **Holders leaving** | the snapshot top 10 combined is down **≥ 25%**, or **3+** of them fully emptied | **all** |
| 3 | **Liquidity pulled** | pool liquidity is down **≥ 30%** from entry | **all** |
| 4a | X dead (if Grok is on) | hourly X read says "dead" | **all** |
| 4b | X fading (if Grok is on) | first "fading" read | **half** (once) |
| 5a | **Stop loss** | price **≤ −30%** | **all** |
| 5b | **Take profit** | price **≥ +80%** (first time only) | **half** |
| 5c | **Trailing stop** | after the take, price is **25% below its highest point** | **the rest** |
| 5d | **Time stop** | **6 h** held and still under **+15%** | **all** |
| — | Pool gone | no pair or price 0 | all at $0, counted as rugged |

If dexscreener or the RPC is down, that tick's checks are skipped and the desk says so. It never guesses.

### Why this order
- **Creator wallet first:** a creator selling is the clearest warning of a rug. In the author's week, the median token fell 71% in the hour after a creator-sell exit.
- **Top 10 holders second:** early whales or insiders leaving quietly.
- **Liquidity third:** the pool is being drained.
- **Price last:** by the time the price shows it, the insiders are usually already out.

---

## 4. Worked examples ($25 ticket, paper)

**A. Winner with a trailing stop**
- Buy: screen $1.00, fill $1.03, 24.27 tokens.
- Screen hits $1.86 (+80% on the fill price), so it sells half at $1.80 (−3%), about +$9.
- Climbs to $3.00 (highest point), then drops to $2.25 (25% below), so it sells the rest at $2.18, about +$14.
- **Total ≈ +$23.**

**B. Creator dumps**
- Bought at a $1.03 fill. The creator had 3% of supply at entry.
- 40 minutes later the creator wallet is down 35%, so it sells **all** at screen $0.95 (fill $0.92), **≈ −$2.60**.
- One hour later the coin is at $0.20. Without the exit you'd be at −$20.

**C. Going nowhere**
- 6 hours in, the price is +6%, so the time stop sells all, about **+$0.70** after slippage.

**D. Straight down**
- The price hits −30% before any wallet rule fires, so the stop loss sells all, **≈ −$8** (including slippage).

---

## 5. Daily routine

| How often | Command | What it does |
|---|---|---|
| every 10 min | `python watch.py --minutes 9 --every 20` | guards open positions |
| every 60 min | `python pulse.py` | X read (Grok only) |
| every 2 h | `python scan.py` | finds coins (Grok only) |
| evening | `python report.py` | checks, buys, exits, P&L, Grok bill, free cash |
| all of it | `./run.sh` | runs everything in one loop |

---

## 6. What it can't protect you from
- A **rug done in one transaction**, faster than the 20 s check. Only the entry checks help there.
- **Slow live selling:** in live mode you get "SELL NOW" and must click yourself.
- **Small sample:** one week of paper results proves very little.
- **Creator rule noise:** it fires on any transfer out of the creator wallet, not only sells. That errs on the safe side.

## 7. After the paper week, read `checks.csv` and `trades.csv`
- Which check blocks the most coins?
- Would you have taken these buys by hand?
- Did any exit fire on noise?
- Did Grok's input beat its cost?

Change one number at a time in `config.py`, and write down why. **Never loosen a rule just to get a coin through.**
