"""Find early + profitable wallets across recently pumped Solana tokens.

  python run_smartmoney.py                    # discover tokens via GeckoTerminal
  python run_smartmoney.py --mints A,B,C      # analyse specific mints
Set SOLANA_RPC_URL to a private RPC (Helius/QuickNode free tier) for speed.
Output: reports/smart_wallets.md, reports/early_buyers.csv, reports/wallet_ranking.csv
"""
import argparse
import datetime as dt
import json
import os

import pandas as pd

from smartmoney.analyze import analyze_token, rank_wallets, wallet_profile
from smartmoney.discover import gecko_pumped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mints", default="")
    ap.add_argument("--tokens", type=int, default=9)
    ap.add_argument("--max-age-days", type=float, default=30)
    ap.add_argument("--buyers", type=int, default=60)
    ap.add_argument("--profile-top", type=int, default=25)
    a = ap.parse_args()
    os.makedirs("reports", exist_ok=True)

    if a.mints:
        toks = [{"mint": m, "symbol": m[:6]} for m in a.mints.split(",")]
    else:
        toks = gecko_pumped(limit=a.tokens, max_age_d=a.max_age_days)
    print("Tokens:", json.dumps([(t["symbol"], t["mint"]) for t in toks]), flush=True)

    rows, done = [], []
    for t in toks:
        print(f"Analysing {t['symbol']} {t['mint']}", flush=True)
        try:
            r = analyze_token(t, max_buyers=a.buyers, log=lambda m: print(m, flush=True))
        except Exception as e:
            print("  failed:", e, flush=True)
            continue
        rows += r
        if r:
            done.append(t)
        pd.DataFrame(rows).to_csv("reports/early_buyers.csv", index=False)

    df = pd.DataFrame(rows)
    rank = pd.DataFrame(rank_wallets(rows))
    if rank.empty:
        print("No tokens could be analysed (history too long or RPC errors).")
        return
    rank.to_csv("reports/wallet_ranking.csv", index=False)

    # Background checks on the best candidates (exclude obvious snipers)
    cand = rank[(rank["realized_pnl_sol"] > 0) & (rank["sniper_hits"] == 0)].head(a.profile_top)
    profs = []
    for w in cand["wallet"]:
        try:
            profs.append(wallet_profile(w))
        except Exception as e:
            profs.append({"wallet": w, "error": str(e)})
    prof = pd.DataFrame(profs)
    top = cand.merge(prof, on="wallet", how="left") if len(prof) else cand
    top.to_csv("reports/top_wallets.csv", index=False)

    # Funding clusters: several "different" top wallets funded by the same source = one operator
    clusters = top["funded_by"].value_counts() if "funded_by" in top else pd.Series(dtype=int)
    clusters = clusters[clusters > 1]

    with open("reports/smart_wallets.md", "w") as f:
        f.write(f"# Smart-money scan — {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n")
        f.write("Early buyers (first ~60 per token) of recently pumped Solana tokens, scored on *realized* SOL PnL "
                "from their own trades. Not financial advice; past PnL does not predict future PnL.\n\n")
        f.write("## Tokens analysed\n\n")
        f.write(pd.DataFrame(done).drop(columns=["pair"], errors="ignore").to_markdown(index=False) + "\n\n")
        if len(df):
            f.write("## Early-buyer outcomes per token\n\n")
            s = df.groupby("token").agg(buyers=("wallet", "count"), profitable=("realized_pnl_sol", lambda x: (x > 0).sum()),
                                        snipers=("sniper", "sum"), median_pnl_sol=("realized_pnl_sol", "median"),
                                        best_pnl_sol=("realized_pnl_sol", "max"))
            f.write(s.round(3).to_markdown() + "\n\n")
        f.write("## Wallets profitable in 2+ tokens\n\n")
        multi = rank[(rank["n_tokens"] >= 2) & (rank["wins"] >= 2)]
        f.write((multi.to_markdown(index=False) if len(multi) else "_None in this sample._") + "\n\n")
        f.write("## Top candidates (non-sniper, positive realized PnL) with background checks\n\n")
        cols = [c for c in ["wallet", "tokens", "wins", "realized_pnl_sol", "roi", "moved_tokens_out", "age_days",
                            "tx_count", "txs_per_day", "last_active_h", "funded_by", "first_funding_sol"] if c in top]
        f.write(top[cols].to_markdown(index=False) + "\n\n")
        if len(clusters):
            f.write("## ⚠️ Shared funding sources (likely same operator)\n\n" + clusters.to_markdown() + "\n\n")
    print("Done -> reports/smart_wallets.md", flush=True)


if __name__ == "__main__":
    main()
