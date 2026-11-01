"""Find Solana tokens that pumped, using DexScreener's free API."""
import time

import requests

DS = "https://api.dexscreener.com"


def _get(path):
    for i in range(5):
        r = requests.get(DS + path, timeout=20)
        if r.status_code == 429:
            time.sleep(2 ** i)
            continue
        r.raise_for_status()
        return r.json()
    return []


def candidate_tokens():
    addrs = []
    for p in ("/token-boosts/top/v1", "/token-boosts/latest/v1", "/token-profiles/latest/v1",
              "/token-profiles/recent-updates/v1", "/community-takeovers/latest/v1"):
        for t in _get(p) or []:
            if t.get("chainId") == "solana":
                addrs.append(t["tokenAddress"])
    for q in SEARCH_TERMS:
        for pr in (_get(f"/latest/dex/search?q={q}") or {}).get("pairs", []):
            if pr.get("chainId") == "solana":
                addrs.append(pr["baseToken"]["address"])
    return list(dict.fromkeys(addrs))


SEARCH_TERMS = ["pump", "sol", "meme", "cat", "dog", "ai", "pepe", "frog", "inu", "moon", "coin",
                "trump", "elon", "baby", "doge", "wif", "bonk", "agent", "chill", "based"]


def pumped_tokens(min_age_h=12, max_age_d=10, min_liq=30_000, min_fdv=500_000, limit=10):
    """Tokens young enough that their first trades are reachable, that clearly ran up."""
    addrs = candidate_tokens()
    best = {}
    for i in range(0, len(addrs), 30):
        for p in _get("/tokens/v1/solana/" + ",".join(addrs[i:i + 30])) or []:
            tok = p["baseToken"]["address"]
            if p.get("quoteToken", {}).get("symbol") not in ("SOL", "WSOL"):
                continue
            liq = (p.get("liquidity") or {}).get("usd") or 0
            if tok not in best or liq > ((best[tok].get("liquidity") or {}).get("usd") or 0):
                best[tok] = p
    now = time.time() * 1000
    out = []
    for tok, p in best.items():
        age_h = (now - (p.get("pairCreatedAt") or now)) / 3.6e6
        liq = (p.get("liquidity") or {}).get("usd") or 0
        fdv = p.get("fdv") or 0
        if min_age_h <= age_h <= max_age_d * 24 and liq >= min_liq and fdv >= min_fdv:
            out.append({"mint": tok, "symbol": p["baseToken"]["symbol"], "fdv": fdv, "liq": liq,
                        "age_h": round(age_h, 1), "vol24": (p.get("volume") or {}).get("h24"),
                        "pair": p["pairAddress"], "url": p.get("url")})
    out.sort(key=lambda x: x["fdv"], reverse=True)
    return out[:limit]


GT = "https://api.geckoterminal.com/api/v2/networks/solana"
WSOL = "So11111111111111111111111111111111111111112"


def _gt(path):
    for i in range(6):
        r = requests.get(GT + path, timeout=20, headers={"accept": "application/json"})
        if r.status_code == 429:
            time.sleep(5 * (i + 1))  # free tier: ~30 req/min
            continue
        r.raise_for_status()
        return r.json().get("data", [])
    return []


def gecko_pumped(min_age_h=12, max_age_d=30, min_liq=20_000, min_fdv=300_000, min_gain_pct=100,
                 pages=5, limit=10):
    """Young SOL-quoted pools that ran up. `min_gain_pct` = max of h24 / h6 gain, or FDV >= 5x min."""
    seen, out = set(), []
    paths = [f"/trending_pools?page={p}&duration=24h" for p in range(1, pages + 1)]
    paths += [f"/pools?page={p}&sort=h24_volume_usd_desc" for p in range(1, pages + 1)]
    now = time.time()
    for path in paths:
        for pool in _gt(path):
            a, rel = pool["attributes"], pool["relationships"]
            mint = rel["base_token"]["data"]["id"].split("_", 1)[1]
            quote = rel["quote_token"]["data"]["id"].split("_", 1)[1]
            if quote != WSOL or mint in seen:
                continue
            seen.add(mint)
            created = a.get("pool_created_at")
            if not created:
                continue
            age_h = (now - time.mktime(time.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")) + time.timezone * 0) / 3600
            fdv = float(a.get("fdv_usd") or 0)
            liq = float(a.get("reserve_in_usd") or 0)
            pc = a.get("price_change_percentage") or {}
            gain = max(float(pc.get("h24") or 0), float(pc.get("h6") or 0))
            if not (min_age_h <= age_h <= max_age_d * 24 and liq >= min_liq and fdv >= min_fdv):
                continue
            if gain < min_gain_pct and fdv < 5 * min_fdv:
                continue
            out.append({"mint": mint, "symbol": a["name"].split(" / ")[0], "fdv": round(fdv),
                        "liq": round(liq), "age_h": round(age_h, 1), "gain_24h": gain,
                        "pair": a["address"], "url": f"https://www.geckoterminal.com/solana/pools/{a['address']}"})
    out.sort(key=lambda x: x["fdv"], reverse=True)
    return out[:limit]
