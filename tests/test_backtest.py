import unittest

from backtest import BacktestConfig, run_backtest, run_daily_backtest
from broker import MockBroker
from models import DailyBar, MarketData, Signal
from strategies.quant_strategy import QuantStrategy
from strategy import Strategy


class PriceLessStrategy(Strategy):
    def on_market_data(self, data):
        return Signal(self.symbol, "BUY")


class BuySellStrategy(Strategy):
    def __init__(self, broker, symbol):
        super().__init__(broker, symbol)
        self.seen = 0

    def on_market_data(self, data):
        self.seen += 1
        if self.seen == 1:
            return Signal(self.symbol, "BUY", quantity=1, reason="enter")
        if self.seen == 2:
            return Signal(self.symbol, "SELL", quantity=1, reason="exit")
        return None


class LargeBuyStrategy(Strategy):
    def __init__(self, broker, symbol):
        super().__init__(broker, symbol)
        self.seen = 0

    def on_market_data(self, data):
        self.seen += 1
        if self.seen == 1:
            return Signal(self.symbol, "BUY", quantity=10)
        return None


class TestBacktest(unittest.TestCase):
    def test_run_backtest_executes_strategy_signals(self):
        broker = MockBroker()
        strategy = QuantStrategy(broker, "005930", short_window=2, long_window=3)
        rows = [{"price": price} for price in [3, 2, 1, 2, 3]]

        result = run_backtest(strategy, rows)

        self.assertEqual(result.ticks, 5)
        self.assertEqual(len(result.signals), 1)
        self.assertEqual(len(result.orders), 1)
        self.assertEqual(result.orders[0].status, "FILLED")
        self.assertEqual(result.orders[0].side, "BUY")
        self.assertEqual(result.orders[0].symbol, "005930")
        self.assertEqual(result.orders[0].price, 3)

    def test_run_backtest_updates_mock_price_for_signals_without_price(self):
        broker = MockBroker()
        strategy = PriceLessStrategy(broker, "005930")

        result = run_backtest(strategy, [MarketData("005930", 72000)])

        self.assertEqual(result.orders[0].price, 72000)

    def test_run_backtest_validates_market_data(self):
        broker = MockBroker()
        strategy = PriceLessStrategy(broker, "005930")

        with self.assertRaisesRegex(ValueError, "price"):
            run_backtest(strategy, [{"symbol": "005930"}])

    def test_run_backtest_requires_mock_broker(self):
        strategy = PriceLessStrategy(object(), "005930")

        with self.assertRaisesRegex(ValueError, "MockBroker"):
            run_backtest(strategy, [{"price": 72000}])

    def test_run_daily_backtest_fills_signals_at_next_open(self):
        broker = MockBroker()
        strategy = BuySellStrategy(broker, "005930")
        bars = [
            DailyBar("005930", "2024-01-02", 10, 10, 10, 10, 100),
            DailyBar("005930", "2024-01-03", 11, 12, 10, 12, 100),
            DailyBar("005930", "2024-01-04", 13, 14, 12, 14, 100),
        ]

        result = run_daily_backtest(strategy, bars, BacktestConfig(initial_cash=100))

        self.assertEqual([fill.side for fill in result.fills], ["BUY", "SELL"])
        self.assertEqual(result.fills[0].date, "2024-01-03")
        self.assertEqual(result.fills[0].price, 11)
        self.assertEqual(result.fills[1].date, "2024-01-04")
        self.assertEqual(result.fills[1].realized_pnl, 2)
        self.assertEqual(result.equity_curve[-1].equity, 102)

    def test_run_daily_backtest_rejects_insufficient_cash(self):
        broker = MockBroker()
        strategy = LargeBuyStrategy(broker, "005930")
        bars = [
            DailyBar("005930", "2024-01-02", 10, 10, 10, 10, 100),
            DailyBar("005930", "2024-01-03", 20, 20, 20, 20, 100),
        ]

        result = run_daily_backtest(strategy, bars, BacktestConfig(initial_cash=100))

        self.assertEqual(len(result.fills), 0)
        self.assertEqual(result.rejected_signals[0].reason, "Insufficient cash")


if __name__ == "__main__":
    unittest.main()
