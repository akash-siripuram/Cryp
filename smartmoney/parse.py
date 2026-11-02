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


def all_swaps(tx):
    """Every non-SOL token whose balance changed for the signer: list of dicts with
    mint, token_delta, post_balance, sol_delta (SOL incl. WSOL; whole-tx SOL change)."""
    if not tx or tx.get("meta") is None or tx["meta"].get("err"):
        return []
    meta, msg = tx["meta"], tx["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    signer = keys[0]

    def bal(lst):
        out = {}
        for b in lst or []:
            if b.get("owner") == signer:
                out[b["mint"]] = out.get(b["mint"], 0.0) + float(b["uiTokenAmount"]["uiAmount"] or 0)
        return out

    pre, post = bal(meta.get("preTokenBalances")), bal(meta.get("postTokenBalances"))
    sol = (meta["postBalances"][0] - meta["preBalances"][0]) / 1e9
    sol += post.get(WSOL, 0.0) - pre.get(WSOL, 0.0)
    out = []
    for m in set(pre) | set(post):
        if m == WSOL:
            continue
        d = post.get(m, 0.0) - pre.get(m, 0.0)
        if abs(d) > 1e-12:
            out.append({"wallet": signer, "mint": m, "token_delta": d, "post_balance": post.get(m, 0.0),
                        "sol_delta": sol, "time": tx.get("blockTime"), "slot": tx["slot"]})
    return out
