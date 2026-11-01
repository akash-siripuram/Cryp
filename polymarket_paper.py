"""Paper-trade the "buy at 1c, sell at 99c" Polymarket longshot strategy.

No real money, no wallet. Uses Polymarket's public Gamma API for live prices.

    python polymarket_paper.py run      # update open positions, then buy new longshots
    python polymarket_paper.py update   # only settle / take profit on open positions
    python polymarket_paper.py status   # print the ledger

State lives in paper_ledger.json. Run it daily (e.g. cron) to keep it going.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
LEDGER = Path(__file__).with_name("paper_ledger.json")

START_BALANCE = 100.0
STAKE = 1.00            # dollars per position -> ~100 bets with $100
MAX_ENTRY = 0.02        # only buy outcomes whose ask is <= 2c
TAKE_PROFIT = 0.99      # sell when the outcome's bid reaches 99c
MIN_LIQUIDITY = 5_000   # skip illiquid markets (a 1c ask you can't actually fill is fake)
MAX_NEW_PER_RUN = 10


def get(path):
    req = urllib.request.Request(GAMMA + path, headers={"User-Agent": "paper-trader"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"cash": START_BALANCE, "open": [], "closed": []}


def save(led):
    LEDGER.write_text(json.dumps(led, indent=2))


def quotes(m):
    """Return {outcome: (ask, bid)} for a binary market."""
    names = json.loads(m.get("outcomes") or "[]")
    if len(names) != 2:
        return {}
    ask, bid = m.get("bestAsk"), m.get("bestBid")
    if ask is None or bid is None:
        return {}
    ask, bid = float(ask), float(bid)
    # Book is quoted on outcome 0; outcome 1 is the mirror image.
    return {names[0]: (ask, bid), names[1]: (round(1 - bid, 4), round(1 - ask, 4))}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def update(led):
    still_open = []
    for p in led["open"]:
        try:
            m = get(f"/markets/{p['market_id']}")
        except Exception as e:
            print(f"  ! could not fetch {p['market_id']}: {e}")
            still_open.append(p)
            continue
        exit_price, reason = None, None
        if m.get("closed"):
            names = json.loads(m["outcomes"])
            prices = [float(x) for x in json.loads(m["outcomePrices"])]
            exit_price, reason = prices[names.index(p["outcome"])], "resolved"
        else:
            q = quotes(m).get(p["outcome"])
            if q and q[1] >= TAKE_PROFIT:
                exit_price, reason = q[1], "take-profit"
        if exit_price is None:
            q = quotes(m).get(p["outcome"])
            p["last_bid"] = q[1] if q else p.get("last_bid", 0)
            still_open.append(p)
            continue
        proceeds = p["shares"] * exit_price
        led["cash"] += proceeds
        p.update(exit=exit_price, proceeds=round(proceeds, 2),
                 pnl=round(proceeds - p["cost"], 2), reason=reason, closed_at=now())
        led["closed"].append(p)
        print(f"  CLOSE {reason:11} {p['pnl']:+8.2f}  {p['outcome']} @ {exit_price}  {p['question'][:60]}")
    led["open"] = still_open


def buy(led):
    held = {(p["market_id"], p["outcome"]) for p in led["open"]}
    bought, offset = 0, 0
    while bought < MAX_NEW_PER_RUN and led["cash"] >= STAKE and offset < 2000:
        batch = get(f"/markets?closed=false&active=true&limit=200&offset={offset}"
                    f"&liquidity_num_min={MIN_LIQUIDITY}&order=volume24hr&ascending=false")
        if not batch:
            break
        offset += len(batch)
        for m in batch:
            for outcome, (ask, _bid) in quotes(m).items():
                if not (0 < ask <= MAX_ENTRY) or (m["id"], outcome) in held:
                    continue
                shares = STAKE / ask
                led["cash"] -= STAKE
                led["open"].append({
                    "market_id": m["id"], "question": m["question"], "outcome": outcome,
                    "entry": ask, "shares": round(shares, 2), "cost": STAKE,
                    "opened_at": now(), "end_date": m.get("endDate"),
                })
                held.add((m["id"], outcome))
                bought += 1
                print(f"  BUY   {outcome:4} @ {ask:.3f}  ${STAKE:.2f}  {m['question'][:60]}")
                if bought >= MAX_NEW_PER_RUN or led["cash"] < STAKE:
                    return


def status(led):
    open_cost = sum(p["cost"] for p in led["open"])
    open_mark = sum(p["shares"] * p.get("last_bid", p["entry"]) for p in led["open"])
    realized = sum(p["pnl"] for p in led["closed"])
    wins = [p for p in led["closed"] if p["pnl"] > 0]
    equity = led["cash"] + open_mark
    print(f"\nCash ${led['cash']:.2f} | open {len(led['open'])} (cost ${open_cost:.2f}, mark ${open_mark:.2f})")
    print(f"Closed {len(led['closed'])} | wins {len(wins)} | realized P&L ${realized:+.2f}")
    print(f"Equity ${equity:.2f}  ({(equity / START_BALANCE - 1) * 100:+.1f}% vs ${START_BALANCE:.0f})")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    led = load()
    if cmd in ("run", "update"):
        print("Updating open positions...")
        update(led)
    if cmd == "run":
        print("Looking for <=%dc longshots..." % round(MAX_ENTRY * 100))
        buy(led)
    save(led)
    status(led)


if __name__ == "__main__":
    main()
