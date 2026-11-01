"""Minimal Solana JSON-RPC helpers over the public endpoint (curl, rate-limit aware)."""
import json, subprocess, time
from solders.pubkey import Pubkey

RPC = "https://api.mainnet-beta.solana.com"
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

def call(method, params, tries=8):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    for i in range(tries):
        out = subprocess.run(["curl", "-sS", "-m", "40", RPC, "-H", "content-type: application/json", "-d", body],
                             capture_output=True, text=True).stdout
        try:
            d = json.loads(out)
            if "result" in d: return d["result"]
            if d.get("error", {}).get("code") in (429, -32429) or "Too many" in out: raise ValueError
            return None
        except Exception:
            time.sleep(min(30, 2 * (i + 1)))
    return None

def bonding_curve(mint):
    return str(Pubkey.find_program_address([b"bonding-curve", bytes(Pubkey.from_string(mint))], PUMP)[0])

def oldest_signatures(addr, max_pages=200):
    """Page back to the account's first transactions; returns signatures oldest-first (last page)."""
    before, pages, last = None, 0, []
    while pages < max_pages:
        opt = {"limit": 1000}
        if before: opt["before"] = before
        res = call("getSignaturesForAddress", [addr, opt])
        if res is None: return None, pages
        pages += 1
        if not res: break
        last = res
        if len(res) < 1000: break
        before = res[-1]["signature"]
    return list(reversed(last)), pages
