"""Out-of-sample hit rate: for a set of wallets, sample their recent buys of pump.fun
tokens (any token, winners AND losers), then check what became of each token today
via DexScreener (market cap / liquidity; missing = dead or never graduated).

Usage: python wallet_hitrate.py WALLETS.csv LABEL [N_WALLETS=30] [TX_PER_WALLET=60]
Writes data/hitrate_<LABEL>.json
"""
import json, sys, subprocess, time, pandas as pd
from concurrent.futures import ThreadPoolExecutor
import rpc

def buys_of(wallet, ntx):
    sigs = rpc.call("getSignaturesForAddress", [wallet, {"limit": 1000}]) or []
    sigs = [s for s in sigs if not s["err"]][:ntx * 3]
    out, seen = [], 0
    for s in sigs:
        if seen >= ntx: break
        tx = rpc.call("getTransaction", [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])
        if not tx or tx["meta"]["err"]: continue
        seen += 1
        keys = tx["transaction"]["message"]["accountKeys"]
        payer = keys[0]["pubkey"] if isinstance(keys[0], dict) else keys[0]
        if payer != wallet: continue
        dsol = (tx["meta"]["postBalances"][0] - tx["meta"]["preBalances"][0]) / 1e9
        pre = {b["mint"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in tx["meta"]["preTokenBalances"] if b.get("owner") == wallet}
        post = {b["mint"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in tx["meta"]["postTokenBalances"] if b.get("owner") == wallet}
        for m in set(pre) | set(post):
            if m.endswith("pump") and post.get(m, 0) - pre.get(m, 0) > 0 and dsol < 0:
                out.append({"wallet": wallet, "mint": m, "t": tx["blockTime"], "sol": -dsol})
    return out

def dex(mints):
    res = {}
    for i in range(0, len(mints), 30):
        u = "https://api.dexscreener.com/tokens/v1/solana/" + ",".join(mints[i:i + 30])
        try:
            d = json.loads(subprocess.run(["curl", "-sSf", "-m", "20", u], capture_output=True, text=True, check=True).stdout)
        except Exception:
            d = []
        for p in d:
            m = p["baseToken"]["address"]
            mc = p.get("marketCap") or p.get("fdv") or 0
            if mc > res.get(m, 0): res[m] = mc
        time.sleep(0.3)
    return res

if __name__ == "__main__":
    src, label = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    ntx = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    wallets = list(pd.read_csv(src).iloc[:, 0][:n])
    with ThreadPoolExecutor(3) as ex:
        buys = [b for bs in ex.map(lambda w: buys_of(w, ntx), wallets) for b in bs]
    mints = sorted({b["mint"] for b in buys})
    mc = dex(mints)
    for b in buys: b["mcap_now"] = mc.get(b["mint"], 0)
    json.dump(buys, open(f"data/hitrate_{label}.json", "w"))
    df = pd.DataFrame(buys)
    if df.empty: print("no buys found"); sys.exit()
    tok = df.drop_duplicates("mint")
    print(f"{label}: {df.wallet.nunique()} wallets with buys, {len(tok)} distinct tokens bought "
          f"({time.strftime('%Y-%m-%d', time.gmtime(df.t.min()))} .. {time.strftime('%Y-%m-%d', time.gmtime(df.t.max()))})")
    for th in (1e5, 1e6, 1e7):
        print(f"  tokens now worth >= ${th:,.0f} market cap: {(tok.mcap_now >= th).mean():.1%}")
    print(f"  tokens not found on DexScreener (dead / never graduated): {(tok.mcap_now == 0).mean():.1%}")
