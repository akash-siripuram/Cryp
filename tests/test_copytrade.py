import time

from smartmoney import copytrade
from smartmoney.copytrade import CopyTrader


def test_copy_buy_then_partial_and_full_sell(tmp_path, monkeypatch):
    ct = CopyTrader(["W"], state_path=str(tmp_path / "s.json"), size_sol=1.0, slippage=0.0, fee_sol=0.0)
    now = time.time()
    feed = [[{"wallet": "W", "mint": "M", "token_delta": 1000, "post_balance": 1000, "sol_delta": -1.0, "time": now}],
            [{"wallet": "W", "mint": "M", "token_delta": -500, "post_balance": 500, "sol_delta": 1.0, "time": now}],
            [{"wallet": "W", "mint": "M", "token_delta": -500, "post_balance": 0, "sol_delta": 1.0, "time": now}]]
    px = iter([0.001, 0.002, 0.004])  # SOL per token at each detection
    monkeypatch.setattr(ct, "new_swaps", lambda w: feed.pop(0) if feed else [])
    monkeypatch.setattr(copytrade, "prices", lambda mints: {m: (next(px), 1e6, "TOK") for m in mints})
    ct.step()
    assert abs(ct.st["positions"]["W:M"]["qty"] - 1000) < 1e-9
    ct.step()  # they sell half -> we sell half at 0.002: 500*0.002 - 0.5 cost = +0.5
    assert abs(ct.st["closed"][0]["pnl_sol"] - 0.5) < 1e-9
    ct.step()  # they exit -> we exit remaining 500 at 0.004: 2.0 - 0.5 = +1.5
    assert "W:M" not in ct.st["positions"]
    assert abs(sum(c["pnl_sol"] for c in ct.st["closed"]) - 2.0) < 1e-9


def test_skips_illiquid(tmp_path, monkeypatch):
    ct = CopyTrader(["W"], state_path=str(tmp_path / "s.json"))
    monkeypatch.setattr(ct, "new_swaps", lambda w: [{"wallet": "W", "mint": "M", "token_delta": 1, "post_balance": 1,
                                                     "sol_delta": -1.0, "time": time.time()}])
    monkeypatch.setattr(copytrade, "prices", lambda mints: {m: (1.0, 500, "TOK") for m in mints})
    ct.step()
    assert not ct.st["positions"] and ct.st["wallets"]["W"]["skipped"] == 1
