from dataclasses import dataclass, asdict


@dataclass
class Config:
    # Market
    symbol: str = "BTCUSDT"
    exec_tf: str = "15m"
    trend_tf: str = "1h"

    # Signal
    donchian_len: int = 20          # previous N candles define the range
    atr_len: int = 14
    ema_fast: int = 50               # on trend_tf
    ema_slow: int = 200              # on trend_tf
    vol_len: int = 20                # volume average window
    vol_mult: float = 1.0            # breakout volume must exceed vol_mult * avg
    atr_regime_len: int = 96 * 7     # ~1 week of 15m bars for ATR percentile
    atr_max_pct: float = 0.90        # skip if ATR above this rolling percentile
    confirm_next_bar: bool = True    # next candle must close outside the range too

    # Exits (multiples of ATR at signal time)
    sl_atr: float = 1.5
    tp_atr: float = 2.5
    max_hold_bars: int = 96          # time stop: 24h on 15m

    # Risk / account
    initial_equity: float = 10_000.0
    risk_per_trade: float = 0.005    # 0.5% of equity
    max_leverage: float = 2.0        # notional cap = equity * max_leverage

    # Costs (Binance USDT-M VIP0 defaults; adjust to your tier)
    taker_fee: float = 0.0005
    maker_fee: float = 0.0002
    slippage_bps: float = 2.0        # per side, applied against you
    use_funding: bool = True

    def to_dict(self):
        return asdict(self)
