"""Pick one 'trending winner' per day for the last 500 days.

Historical trending lists aren't available for free, so the proxy is: among
pump.fun-launched coins tracked by CoinGecko, the coin whose all-time high fell
on that day and whose peak market cap (ATH price x total supply) was largest.
"""
import json, datetime as dt
coins = json.load(open("data/cg_pumpfun_markets.json"))
end = dt.date(2026, 11, 1); start = end - dt.timedelta(days=500)
best = {}
for c in coins:
    if not (c.get("mint") or "").endswith("pump") or not c.get("ath_date") or not c.get("ath"): continue
    day = dt.date.fromisoformat(c["ath_date"][:10])
    if not (start <= day < end): continue
    peak = c["ath"] * (c.get("total_supply") or 1e9)
    if day not in best or peak > best[day]["peak_mcap"]:
        best[day] = {"day": day.isoformat(), "id": c["id"], "symbol": c["symbol"], "mint": c["mint"],
                     "peak_mcap": peak, "ath": c["ath"], "price_now": c["current_price"]}
rows = [best[d] for d in sorted(best)]
json.dump(rows, open("data/winners.json", "w"), indent=0)
print(f"{len(rows)} days with a winner (of 500); median peak mcap ${sorted(r['peak_mcap'] for r in rows)[len(rows)//2]:,.0f}")
