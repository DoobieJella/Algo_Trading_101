from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.fundamental_long_short import FundamentalStrategy
from strategies.hft_scalper import HFTStrategy
from strategies.quant_strategy import QuantStrategy


STRATEGIES = {
    "quant": QuantStrategy,
    "arbitrage": ArbitrageStrategy,
    "hft": HFTStrategy,
    "fundamental": FundamentalStrategy,
}

DAILY_BACKTEST_READY = {"quant"}


def create_strategy(name, broker, symbol, **params):
    key = name.lower()
    if key not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    if key == "arbitrage" and "target_symbol" not in params:
        raise ValueError("Arbitrage strategy requires target_symbol")
    return STRATEGIES[key](broker, symbol, **params)


def validate_daily_backtest_strategy(name):
    key = name.lower()
    if key not in DAILY_BACKTEST_READY:
        raise ValueError(f"Strategy is not daily-backtest-ready: {name}")
