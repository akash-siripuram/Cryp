"""For each winner, collect first-hour trades on its pump.fun bonding curve.

Output data/early_trades.jsonl: one line per token with launch time and trades
[{wallet, t, sol (negative = spent), tokens (positive = bought), err}].
Resumable. Usage: python early_buyers.py [MAX_TX_PER_TOKEN=150] [THREADS=4]
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
import rpc

MAXTX = int(sys.argv[1]) if len(sys.argv) > 1 else 150
THREADS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
OUT = "data/early_trades.jsonl"

def parse(tx, mint):
    if not tx or tx["meta"]["err"]: return None
    keys = tx["transaction"]["message"]["accountKeys"]
    payer = keys[0]["pubkey"] if isinstance(keys[0], dict) else keys[0]
    sol = (tx["meta"]["postBalances"][0] - tx["meta"]["preBalances"][0]) / 1e9
    tok = lambda bals: sum(float(b["uiTokenAmount"]["uiAmount"] or 0) for b in bals
                           if b["mint"] == mint and b.get("owner") == payer)
    d_tok = tok(tx["meta"]["postTokenBalances"]) - tok(tx["meta"]["preTokenBalances"])
    if d_tok == 0: return None
    return {"wallet": payer, "t": tx["blockTime"], "sol": round(sol, 6), "tokens": d_tok}

def token(w):
    bc = rpc.bonding_curve(w["mint"])
    sigs, pages = rpc.oldest_signatures(bc)
    if not sigs: return {**w, "error": "no signatures"}
    t0 = sigs[0]["blockTime"]
    first = [s for s in sigs if s["blockTime"] and s["blockTime"] - t0 <= 3600 and not s["err"]][:MAXTX]
    trades = []
    for s in first:
        tx = rpc.call("getTransaction", [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])
        p = parse(tx, w["mint"])
        if p: trades.append(p)
    return {**w, "launch_t": t0, "bc_pages": pages, "n_first_hour_sigs": sum(1 for s in sigs if s["blockTime"] and s["blockTime"] - t0 <= 3600),
            "first_hour_maybe_truncated": len(sigs) == 1000, "trades": trades}

if __name__ == "__main__":
    wins = json.load(open("data/winners.json"))
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["mint"] for l in open(OUT)}
    todo = [w for w in wins[::2] + wins[1::2] if w["mint"] not in done]   # every other day first
    print(f"{len(done)} done, {len(todo)} to do", flush=True)
    with ThreadPoolExecutor(THREADS) as ex, open(OUT, "a") as f:
        for i, r in enumerate(ex.map(token, todo), 1):
            f.write(json.dumps(r) + "\n"); f.flush()
            if i % 10 == 0: print(i, r["day"], r["symbol"], len(r.get("trades", [])), flush=True)
