"""Smart-wallet research on first-hour buyers of daily pump.fun winners.

1. Per (token, wallet): first-hour entry price in USD, entry rank, seconds after launch,
   realized % on first-hour sells, and % to ATH and to today's price.
2. Chronological split: train = first 70% of winner-days, test = last 30%.
3. 'Smart' wallets = early buyers (first-hour) in >= MIN_HITS train winners.
4. Out-of-sample: do smart wallets show up early in test winners more than other
   early buyers do (per wallet, and per token)?
Usage: python analyze.py [MIN_HITS=2]
"""
import json, sys, csv, bisect, numpy as np, pandas as pd

MIN_HITS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
sol = sorted((int(r["ts"]), float(r["close"])) for r in csv.DictReader(open("data/sol_usd_daily.csv")))
sol_ts = [t for t, _ in sol]
def sol_usd(t):
    i = max(0, bisect.bisect_right(sol_ts, t) - 1); return sol[i][1]

def load():
    rows = []
    for l in open("data/early_trades.jsonl"):
        r = json.loads(l)
        tr = r.get("trades") or []
        if not tr: continue
        dev = tr[0]["wallet"]                                    # creator's launch buy
        buys, rank = {}, 0
        for x in tr:
            w = x["wallet"]
            if w == dev: continue
            if x["tokens"] > 0 and x["sol"] < 0:
                rank += 1
                b = buys.setdefault(w, {"cost_sol": 0, "tok": 0, "sold_tok": 0, "proceeds_sol": 0,
                                        "rank": rank, "secs": x["t"] - r["launch_t"]})
                b["cost_sol"] += -x["sol"]; b["tok"] += x["tokens"]
            elif x["tokens"] < 0 and w in buys:
                buys[w]["sold_tok"] += -x["tokens"]; buys[w]["proceeds_sol"] += max(x["sol"], 0)
        px_sol = sol_usd(r["launch_t"])
        for w, b in buys.items():
            if b["tok"] <= 0 or b["cost_sol"] <= 0: continue
            entry = b["cost_sol"] * px_sol / b["tok"]                # USD per token
            sold_frac = min(1, b["sold_tok"] / b["tok"])
            rows.append({"day": r["day"], "symbol": r["symbol"], "mint": r["mint"], "wallet": w,
                         "rank": b["rank"], "secs": b["secs"], "cost_sol": b["cost_sol"],
                         "pct_to_ath": (r["ath"] / entry - 1) * 100,
                         "pct_hold_now": (r["price_now"] / entry - 1) * 100,
                         "sold_frac_1h": sold_frac,
                         "pct_realized_1h": ((b["proceeds_sol"] / (b["cost_sol"] * sold_frac)) - 1) * 100 if sold_frac > 0.05 else np.nan})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    d = load()
    days = sorted(d.day.unique()); cut = days[int(len(days) * .7)]
    tr, te = d[d.day < cut], d[d.day >= cut]
    print(f"{d.mint.nunique()} winners, {len(d)} early (token,wallet) buys, {d.wallet.nunique()} wallets; "
          f"train {tr.mint.nunique()} winners < {cut} <= test {te.mint.nunique()} winners")
    print("\nEarly-buyer returns on winners (median, %):")
    print(d[["pct_realized_1h", "pct_to_ath", "pct_hold_now"]].median().round(0).to_dict(),
          "| share that sold some within 1h:", round((d.sold_frac_1h > 0.05).mean(), 2),
          "| share whose hold-to-now is a loss:", round((d.pct_hold_now < 0).mean(), 2))

    hits = tr.groupby("wallet").mint.nunique()
    smart = set(hits[hits >= MIN_HITS].index); once = set(hits[hits == 1].index)
    te_w = set(te.wallet)
    print(f"\nTrain: {len(smart)} wallets early in >= {MIN_HITS} winners; {len(once)} early in exactly 1")
    for name, grp in (("smart", smart), ("one-hit", once)):
        rate = len(grp & te_w) / max(len(grp), 1)
        print(f"  {name:8s}: {rate:.1%} of them are early in >=1 test winner")
    # per test token: how many smart wallets among its early buyers
    per_tok = te.groupby("mint").wallet.apply(lambda s: len(set(s) & smart))
    print(f"Test winners with >=1 smart wallet among early buyers: {(per_tok > 0).mean():.1%} "
          f"(median {per_tok.median():.0f}, max {per_tok.max()})")
    # top smart wallets by train record
    st = tr[tr.wallet.isin(smart)].groupby("wallet").agg(train_hits=("mint", "nunique"),
            med_rank=("rank", "median"), med_secs=("secs", "median"), med_pct_ath=("pct_to_ath", "median"),
            med_pct_realized=("pct_realized_1h", "median"), sold_1h=("sold_frac_1h", "mean"))
    st["test_hits"] = te[te.wallet.isin(smart)].groupby("wallet").mint.nunique().reindex(st.index).fillna(0).astype(int)
    st = st.sort_values(["train_hits", "test_hits"], ascending=False)
    st.to_csv("data/smart_wallets.csv")
    print("\nTop smart wallets (train record -> test):")
    print(st.head(15).round(0).to_string())
    print(f"\nCorrelation of train hits with test hits among smart wallets: {st.train_hits.corr(st.test_hits):.2f}")
