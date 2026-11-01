"""Early-buyer PnL per token, cross-token ranking, and wallet background checks."""
import time
from collections import defaultdict

from . import rpc
from .parse import swap_delta

SNIPER_SLOTS = 2  # bought within N slots of the first trade -> likely sniper/bundler bot


def early_buyers(mint, max_buyers=80, max_txs=500, max_pages=150):
    sigs, reached = rpc.oldest_signatures(mint, max_pages=max_pages)
    if not reached:
        return None, "history too long to reach launch with public RPC"
    first_slot, creator, buyers = None, None, {}
    for s in sigs[:max_txs]:
        if s.get("err"):
            continue
        d = swap_delta(rpc.transaction(s["signature"]), mint)
        if first_slot is None:
            first_slot = s["slot"]
        if not d:
            continue
        if creator is None:
            creator = d["wallet"]
        if d["token_delta"] > 0 and d["sol_delta"] < 0 and d["wallet"] not in buyers:
            buyers[d["wallet"]] = {**d, "slots_after_launch": d["slot"] - first_slot}
            if len(buyers) >= max_buyers:
                break
    return {"first_slot": first_slot, "creator": creator, "buyers": buyers}, None


def wallet_token_pnl(wallet, token_account, mint, max_pages=3):
    """Sum every trade this wallet made in `mint`, using its token account's history."""
    sigs, before = [], None
    for _ in range(max_pages):
        page = rpc.signatures(token_account, before)
        sigs += page
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
    spent = received = bought = sold = transferred_out = 0.0
    n = 0
    for s in sigs:
        if s.get("err"):
            continue
        d = swap_delta(rpc.transaction(s["signature"]), mint)
        if not d or d["wallet"] != wallet:
            continue
        n += 1
        if d["token_delta"] > 0:
            bought += d["token_delta"]
            spent += max(-d["sol_delta"], 0)
        elif d["sol_delta"] > 1e-4:
            sold += -d["token_delta"]
            received += d["sol_delta"]
        else:
            transferred_out += -d["token_delta"]  # moved tokens away without getting SOL
    return {"trades": n, "sol_spent": spent, "sol_received": received, "tokens_bought": bought,
            "tokens_sold": sold, "tokens_transferred_out": transferred_out,
            "realized_pnl_sol": received - spent,
            "sold_pct": (sold / bought) if bought else 0.0}


def analyze_token(tok, max_buyers=80, log=print):
    eb, err = early_buyers(tok["mint"], max_buyers=max_buyers)
    if err:
        log(f"  skip {tok['symbol']}: {err}")
        return []
    rows = []
    for i, (w, b) in enumerate(eb["buyers"].items()):
        if w == eb["creator"]:
            continue
        p = wallet_token_pnl(w, b["token_account"], tok["mint"])
        rows.append({"token": tok["symbol"], "mint": tok["mint"], "wallet": w,
                     "slots_after_launch": b["slots_after_launch"],
                     "minutes_after_launch": None,
                     "first_buy_time": b["time"], "sniper": b["slots_after_launch"] <= SNIPER_SLOTS, **p})
        if (i + 1) % 20 == 0:
            log(f"  {tok['symbol']}: {i + 1}/{len(eb['buyers'])} buyers scored")
    return rows


def rank_wallets(rows, min_tokens=1):
    agg = defaultdict(lambda: {"tokens": [], "wins": 0, "pnl": 0.0, "spent": 0.0, "sniper_hits": 0,
                               "transfers": 0})
    for r in rows:
        a = agg[r["wallet"]]
        a["tokens"].append(r["token"])
        a["pnl"] += r["realized_pnl_sol"]
        a["spent"] += r["sol_spent"]
        a["wins"] += r["realized_pnl_sol"] > 0
        a["sniper_hits"] += r["sniper"]
        a["transfers"] += r["tokens_transferred_out"] > 0
    out = [{"wallet": w, "n_tokens": len(a["tokens"]), "tokens": ",".join(a["tokens"]),
            "wins": a["wins"], "realized_pnl_sol": round(a["pnl"], 3), "sol_spent": round(a["spent"], 3),
            "roi": round(a["pnl"] / a["spent"], 2) if a["spent"] else None,
            "sniper_hits": a["sniper_hits"], "moved_tokens_out": a["transfers"]}
           for w, a in agg.items() if len(a["tokens"]) >= min_tokens]
    out.sort(key=lambda x: (x["wins"], x["realized_pnl_sol"]), reverse=True)
    return out


def wallet_profile(wallet, max_pages=5):
    """Age, activity and funding source (who sent its first SOL)."""
    sigs, before, total = [], None, 0
    for _ in range(max_pages):
        page = rpc.signatures(wallet, before)
        total += len(page)
        sigs = page or sigs
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
    reached = total < max_pages * 1000
    newest = rpc.signatures(wallet)[:1]
    oldest = sigs[-1] if sigs else None
    funder, fund_amt = None, None
    if reached and oldest:
        for s in reversed(sigs[-25:]):  # first few txs, oldest first
            tx = rpc.transaction(s["signature"])
            for ix in (tx or {}).get("transaction", {}).get("message", {}).get("instructions", []):
                info = (ix.get("parsed") or {}).get("info", {}) if isinstance(ix.get("parsed"), dict) else {}
                if ix.get("program") == "system" and info.get("destination") == wallet and info.get("lamports", 0) >= 10_000_000:  # ignore dust spam
                    funder, fund_amt = info["source"], info["lamports"] / 1e9
                    break
            if funder:
                break
    first_t = oldest.get("blockTime") if oldest and reached else None
    last_t = newest[0].get("blockTime") if newest else None
    days = (time.time() - first_t) / 86400 if first_t else None
    return {"wallet": wallet, "tx_count": total if reached else f">{total}",
            "age_days": round(days, 1) if days else (f">{(time.time() - oldest['blockTime']) / 86400:.0f}" if oldest and oldest.get("blockTime") else None),
            "txs_per_day": round(total / days, 1) if days else None,
            "last_active_h": round((time.time() - last_t) / 3600, 1) if last_t else None,
            "funded_by": funder, "first_funding_sol": fund_amt}
