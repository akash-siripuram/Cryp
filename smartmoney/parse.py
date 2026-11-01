"""Turn a parsed transaction into per-wallet swap deltas for one token."""
WSOL = "So11111111111111111111111111111111111111112"


def swap_delta(tx, mint):
    """Return dict for the signer: token delta, SOL delta (incl. WSOL, fees), token account, time.

    None if the signer's balance of `mint` did not change or the tx failed.
    """
    if not tx or tx.get("meta") is None or tx["meta"].get("err"):
        return None
    meta, msg = tx["meta"], tx["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    signer = keys[0]

    def bal(lst):
        out = {}
        for b in lst or []:
            if b.get("owner") == signer and b["mint"] in (mint, WSOL):
                amt = float(b["uiTokenAmount"]["uiAmount"] or 0)
                out[(b["mint"], keys[b["accountIndex"]])] = amt
        return out

    pre, post = bal(meta.get("preTokenBalances")), bal(meta.get("postTokenBalances"))
    tok, wsol, tok_acct = 0.0, 0.0, None
    for k in set(pre) | set(post):
        d = post.get(k, 0.0) - pre.get(k, 0.0)
        if k[0] == mint:
            tok += d
            tok_acct = k[1]
        else:
            wsol += d
    if abs(tok) < 1e-12:
        return None
    sol = (meta["postBalances"][0] - meta["preBalances"][0]) / 1e9 + wsol
    return {"wallet": signer, "token_delta": tok, "sol_delta": sol, "token_account": tok_acct,
            "slot": tx["slot"], "time": tx.get("blockTime")}
