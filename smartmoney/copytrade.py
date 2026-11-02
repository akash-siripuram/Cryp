"""Paper copy-trader: watch wallets live, copy their buys/sells at the price *we* would get.

Copy price = DexScreener price at the moment we detect the trade (so detection delay and
price impact count against us), plus slippage and a per-trade fee for priority/tips.
Nothing is ever sent on-chain.
"""
import json
import os
import time

import requests

from . import rpc
from .parse import all_swaps

DS = "https://api.dexscreener.com/tokens/v1/solana/"


def prices(mints):
    """mint -> (price in SOL per token, liquidity USD). Uses deepest SOL-quoted pair."""
    out = {}
    mints = list(mints)
    for i in range(0, len(mints), 30):
        try:
            r = requests.get(DS + ",".join(mints[i:i + 30]), timeout=15)
            r.raise_for_status()
            pairs = r.json() or []
        except Exception:
            continue
        for p in pairs:
            m = p["baseToken"]["address"]
            if p.get("quoteToken", {}).get("symbol") not in ("SOL", "WSOL") or not p.get("priceNative"):
                continue
            liq = (p.get("liquidity") or {}).get("usd") or 0
            if m not in out or liq > out[m][1]:
                out[m] = (float(p["priceNative"]), liq, p["baseToken"].get("symbol", m[:6]))
    return out


class CopyTrader:
    def __init__(self, wallets, state_path="reports/copytrade_state.json", size_sol=0.5,
                 slippage=0.03, fee_sol=0.002, min_liq_usd=10_000, min_their_buy_sol=0.05):
        self.path = state_path
        self.size, self.slip, self.fee = size_sol, slippage, fee_sol
        self.min_liq, self.min_buy = min_liq_usd, min_their_buy_sol
        self.st = {"wallets": {}, "positions": {}, "closed": [], "events": []}
        if os.path.exists(state_path):
            with open(state_path) as f:
                self.st.update(json.load(f))
        for w in wallets:
            self.st["wallets"].setdefault(w, {"last_sig": None, "their_trades": 0, "their_sol": 0.0,
                                              "copies": 0, "skipped": 0, "delays": []})

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.st, f, indent=1)
        os.replace(tmp, self.path)

    def _log(self, msg):
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
        print(line, flush=True)
        self.st["events"] = (self.st["events"] + [line])[-500:]

    def new_swaps(self, wallet):
        ws = self.st["wallets"][wallet]
        page = rpc.signatures(wallet, limit=100)
        if not page:
            return []
        if ws["last_sig"] is None:  # first sight: start watching from now, no backfill
            ws["last_sig"] = page[0]["signature"]
            return []
        fresh = []
        for s in page:
            if s["signature"] == ws["last_sig"]:
                break
            fresh.append(s)
        ws["last_sig"] = page[0]["signature"]
        swaps = []
        for s in reversed(fresh):
            if not s.get("err"):
                swaps += all_swaps(rpc.transaction(s["signature"]))
        return swaps

    def step(self):
        events = []
        for w in self.st["wallets"]:
            try:
                events += self.new_swaps(w)
            except Exception as e:
                self._log(f"poll {w[:6]} failed: {e}")
        if not events:
            return
        px = prices({e["mint"] for e in events})
        now = time.time()
        for e in events:
            w, m, ws = e["wallet"], e["mint"], self.st["wallets"][e["wallet"]]
            ws["their_trades"] += 1
            ws["their_sol"] += e["sol_delta"]
            delay = now - (e["time"] or now)
            key = f"{w}:{m}"
            p = px.get(m)
            if e["token_delta"] > 0 and e["sol_delta"] < -self.min_buy:  # they bought
                if key in self.st["positions"]:
                    continue  # already copying this token for this wallet; ignore add-ons
                if not p or p[1] < self.min_liq:
                    ws["skipped"] += 1
                    self._log(f"SKIP {w[:6]} buy {m[:6]} (no SOL pair or liq < ${self.min_liq})")
                    continue
                fill = p[0] * (1 + self.slip)
                qty = (self.size - self.fee) / fill
                self.st["positions"][key] = {"wallet": w, "mint": m, "symbol": p[2], "qty": qty,
                                             "cost_sol": self.size, "entry_px": fill, "opened": now,
                                             "their_entry_px": -e["sol_delta"] / e["token_delta"]}
                ws["copies"] += 1
                ws["delays"] = (ws["delays"] + [round(delay, 1)])[-200:]
                self._log(f"COPY BUY {p[2]} after {w[:6]} delay={delay:.0f}s "
                          f"their_px={-e['sol_delta'] / e['token_delta']:.3e} our_px={fill:.3e}")
            elif e["token_delta"] < 0 and key in self.st["positions"]:  # they sold
                pos = self.st["positions"][key]
                frac = min(1.0, -e["token_delta"] / (-e["token_delta"] + e["post_balance"]))
                if frac > 0.98:
                    frac = 1.0
                price = (p[0] if p else 0.0) * (1 - self.slip)
                q = pos["qty"] * frac
                proceeds = max(q * price - self.fee, 0.0)
                cost = pos["cost_sol"] * frac
                pos["qty"] -= q
                pos["cost_sol"] -= cost
                self.st["closed"].append({"wallet": w, "mint": m, "symbol": pos["symbol"], "frac": frac,
                                          "cost_sol": cost, "proceeds_sol": proceeds,
                                          "pnl_sol": proceeds - cost, "closed": now, "delay_s": delay})
                self._log(f"COPY SELL {pos['symbol']} {frac:.0%} after {w[:6]} pnl={proceeds - cost:+.3f} SOL")
                if pos["qty"] <= 1e-12 or frac == 1.0:
                    del self.st["positions"][key]

    def mark_to_market(self):
        px = prices({p["mint"] for p in self.st["positions"].values()})
        out = []
        for k, p in self.st["positions"].items():
            cur = px.get(p["mint"], (0.0, 0, p["symbol"]))[0]
            out.append({**p, "value_sol": p["qty"] * cur * (1 - self.slip), "unrealized_sol": p["qty"] * cur * (1 - self.slip) - p["cost_sol"]})
        return out

    def report(self, path="reports/copytrade.md"):
        opens = self.mark_to_market()
        lines = [f"# Copy-trade paper test — updated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n",
                 f"Copy size {self.size} SOL, slippage {self.slip:.0%}, fee {self.fee} SOL/trade, "
                 f"min liquidity ${self.min_liq:,}. Prices = DexScreener at detection time.\n",
                 "| wallet | their trades | their net SOL | copies | skipped | median delay s | realized SOL | unrealized SOL | copy total SOL |",
                 "|---|---|---|---|---|---|---|---|---|"]
        for w, ws in self.st["wallets"].items():
            real = sum(c["pnl_sol"] for c in self.st["closed"] if c["wallet"] == w)
            unr = sum(o["unrealized_sol"] for o in opens if o["wallet"] == w)
            d = sorted(ws["delays"])
            med = d[len(d) // 2] if d else "-"
            lines.append(f"| `{w}` | {ws['their_trades']} | {ws['their_sol']:+.3f} | {ws['copies']} | {ws['skipped']} | "
                         f"{med} | {real:+.3f} | {unr:+.3f} | {real + unr:+.3f} |")
        lines += ["\n## Open copied positions\n", "| wallet | token | cost SOL | value SOL | unrealized |", "|---|---|---|---|---|"]
        lines += [f"| `{o['wallet'][:8]}` | {o['symbol']} | {o['cost_sol']:.3f} | {o['value_sol']:.3f} | {o['unrealized_sol']:+.3f} |" for o in opens]
        lines += ["\n## Recent events\n", "```"] + self.st["events"][-40:] + ["```"]
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")


def run(wallets, poll_s=20, report_every_s=300, **kw):
    ct = CopyTrader(wallets, **kw)
    ct._log(f"Watching {len(wallets)} wallets")
    last_rep = 0
    while True:
        try:
            ct.step()
        except Exception as e:
            ct._log(f"step failed: {e}")
        ct.save()
        if time.time() - last_rep > report_every_s:
            try:
                ct.report()
            except Exception as e:
                ct._log(f"report failed: {e}")
            last_rep = time.time()
        time.sleep(poll_s)
