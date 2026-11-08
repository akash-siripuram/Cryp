# book.py
# the desk's memory: positions.json and trades.csv. two files you can open yourself.
import csv, json, os, sys, time
from config import (POSITIONS, TRADES, PENDING, TICKET_USD, MAX_OPEN, MAX_ENTRIES_PER_DAY,
                    DAILY_LOSS_HALT_USD, COOLDOWN_HOURS, BANKROLL_USD)

FIELDS = ["time", "mint", "symbol", "action", "usd", "pnl", "reason"]


def load() -> dict:
    return json.load(open(POSITIONS)) if os.path.exists(POSITIONS) else {}


def save(book: dict):
    json.dump(book, open(POSITIONS, "w"), indent=2)


def update(mint: str, **fields):
    b = load()
    if mint in b:
        b[mint].update(fields)
        save(b)


def trades() -> list[dict]:
    return list(csv.DictReader(open(TRADES))) if os.path.exists(TRADES) else []


def record(mint, symbol, action, usd, pnl, reason):
    new = not os.path.exists(TRADES)
    with open(TRADES, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"time": time.strftime("%Y-%m-%d %H:%M"), "mint": mint, "symbol": symbol,
                    "action": action, "usd": round(usd, 2), "pnl": round(pnl, 2), "reason": reason})


def today_pnl() -> float:
    day = time.strftime("%Y-%m-%d")
    return sum(float(t["pnl"]) for t in trades() if t["time"].startswith(day))


def cash() -> float:
    """bankroll + all realized pnl - cost of what is still open."""
    realized = sum(float(t["pnl"]) for t in trades())
    tied = sum(p["qty"] * p["entry"] for p in load().values())
    return BANKROLL_USD + realized - tied


def guard(mint: str) -> str | None:
    """limits first. a blocked entry never touches the network."""
    day, book, log = time.strftime("%Y-%m-%d"), load(), trades()
    if today_pnl() <= -DAILY_LOSS_HALT_USD:                    return "halted_daily_loss"
    if mint in book:                                           return "already_open"
    if len(book) >= MAX_OPEN:                                  return "max_open"
    if cash() < TICKET_USD:                                    return "no_cash"
    if sum(t["action"] == "open" and t["time"].startswith(day) for t in log) >= MAX_ENTRIES_PER_DAY:
        return "max_entries_today"
    cutoff = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - COOLDOWN_HOURS * 3600))
    if any(t["mint"] == mint and t["action"] == "close" and t["time"] >= cutoff for t in log):
        return "cooldown"
    return None


def open_position(mint, symbol, price, liq_usd, snap: dict, usd=TICKET_USD):
    """snap = what the wallets looked like the moment you bought. watch.py compares against it."""
    b = load()
    b[mint] = {"symbol": symbol, "entry": price, "qty0": usd / price, "qty": usd / price,
               "peak": price, "liq0": liq_usd, "opened": time.time(), "took": False,
               "pulse": "unread", "last_pulse": 0, "trimmed_on_fade": False, **snap}
    save(b)
    record(mint, symbol, "open", usd, 0, "entry")


def sell(mint, frac_of_original, price, reason) -> float:
    """sells a fraction of the ORIGINAL size (1.0 = everything left). returns realized pnl."""
    b = load()
    p = b[mint]
    q = min(p["qty"], p["qty0"] * frac_of_original)
    pnl = q * (price - p["entry"])
    p["qty"] -= q
    action = "close" if p["qty"] <= p["qty0"] * 1e-6 else "partial"
    record(mint, p["symbol"], action, q * price, pnl, reason)
    if action == "close":
        del b[mint]
    save(b)
    return pnl


if __name__ == "__main__":
    # live mode only. after you buy in your own wallet:  python book.py add <mint> <usd> <fill_price>
    # after you sell by hand:                            python book.py close <mint> <price>
    cmd, mint = sys.argv[1], sys.argv[2]
    if cmd == "add":
        pend = json.load(open(PENDING)) if os.path.exists(PENDING) else {}
        if mint not in pend:
            sys.exit("no snapshot for this mint. run enter.py on it first.")
        s = pend.pop(mint)
        open_position(mint, s["symbol"], float(sys.argv[4]), s["liq_usd"], s["snap"], float(sys.argv[3]))
        json.dump(pend, open(PENDING, "w"), indent=2)
        print(f"{s['symbol']} is in the book. watch.py guards it from the next run.")
    elif cmd == "close":
        print(round(sell(mint, 1.0, float(sys.argv[3]), "manual"), 2))
