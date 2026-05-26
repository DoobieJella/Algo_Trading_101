import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from backtest import BacktestConfig, run_daily_backtest
from broker import MockBroker
from models import DailyBar, Signal
from performance import calculate_metrics
from reporting import write_backtest_report
from strategy import Strategy


class BuySellStrategy(Strategy):
    def __init__(self, broker, symbol):
        super().__init__(broker, symbol)
        self.seen = 0

    def on_market_data(self, data):
        self.seen += 1
        if self.seen == 1:
            return Signal(self.symbol, "BUY")
        if self.seen == 2:
            return Signal(self.symbol, "SELL")
        return None


class TestPerformanceReporting(unittest.TestCase):
    def test_calculates_core_metrics(self):
        bars = _bars()
        result = run_daily_backtest(
            BuySellStrategy(MockBroker(), "005930"),
            bars,
            BacktestConfig(initial_cash=100),
        )

        metrics = calculate_metrics(result, benchmark_bars=bars)

        self.assertEqual(metrics["ending_equity"], 102)
        self.assertEqual(metrics["number_of_trades"], 2)
        self.assertEqual(metrics["win_rate"], 1)
        self.assertGreater(metrics["benchmark_return"], 0)

    def test_writes_report_artifacts_and_png_charts(self):
        bars = _bars()
        result = run_daily_backtest(
            BuySellStrategy(MockBroker(), "005930"),
            bars,
            BacktestConfig(initial_cash=100),
        )
        metrics = calculate_metrics(result, benchmark_bars=bars)

        with TemporaryDirectory() as directory:
            outputs = write_backtest_report(result, metrics, bars, Path(directory), title="Test")
            equity_chart = outputs["charts"]["equity"]

            self.assertTrue(outputs["report"].exists())
            self.assertTrue(outputs["metrics"].exists())
            self.assertTrue(outputs["trades"].exists())
            self.assertEqual(equity_chart.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


def _bars():
    return [
        DailyBar("005930", "2024-01-02", 10, 10, 10, 10, 100),
        DailyBar("005930", "2024-01-03", 11, 12, 10, 12, 100),
        DailyBar("005930", "2024-01-04", 13, 14, 12, 14, 100),
    ]


if __name__ == "__main__":
    unittest.main()
