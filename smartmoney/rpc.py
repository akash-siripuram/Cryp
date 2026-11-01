"""Tiny Solana JSON-RPC client with rate limiting, retries and a disk cache."""
import hashlib
import json
import os
import time

import requests

RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
CACHE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache", "rpc")
MIN_INTERVAL = float(os.environ.get("RPC_MIN_INTERVAL", "0.12"))
_last = [0.0]
_s = requests.Session()


def call(method, params, cache=True):
    key = hashlib.sha1(json.dumps([method, params], sort_keys=True).encode()).hexdigest()
    path = os.path.join(CACHE, key[:2], key + ".json")
    if cache and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    for attempt in range(8):
        wait = MIN_INTERVAL - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = _s.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(min(2 ** attempt, 30))
                continue
            j = r.json()
            if "error" in j:
                if j["error"].get("code") in (-32005, 429, -32429):
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise RuntimeError(f"{method}: {j['error']}")
            res = j["result"]
            if cache and res is not None:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    json.dump(res, f)
            return res
        except (requests.RequestException, ValueError):
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"{method} failed after retries")


def signatures(address, before=None, limit=1000):
    opts = {"limit": limit}
    if before:
        opts["before"] = before
    # newest pages change over time, so only cache pages anchored by `before`
    return call("getSignaturesForAddress", [address, opts], cache=before is not None)


def transaction(sig):
    try:
        return _tx(sig)
    except RuntimeError:
        return None  # unparseable / pruned tx: skip rather than abort the whole token


def _tx(sig):
    return call("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}])


def oldest_signatures(address, max_pages=40):
    """Walk back to the earliest signatures. Returns (oldest_first_list, reached_start)."""
    before, page = None, None
    for _ in range(max_pages):
        page = signatures(address, before)
        if len(page) < 1000:
            return list(reversed(page)), True
        before = page[-1]["signature"]
    return list(reversed(page or [])), False
