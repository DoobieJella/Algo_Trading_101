import unittest

from broker import MockBroker
from strategies.hft_scalper import HFTStrategy
from strategies.quant_strategy import QuantStrategy


class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.mock_broker = MockBroker({"005930": 1000})
        self.strategy = QuantStrategy(self.mock_broker, "005930", short_window=2, long_window=5)

    def test_quant_logic(self):
        # Feed data
        prices = [100, 110, 120, 130, 140, 150]
        signal = None
        for p in prices:
            signal = self.strategy.on_market_data({'price': p})
            
        # Check if prices were stored
        self.assertEqual(len(self.strategy.prices), 5)
        self.assertEqual(self.strategy.prices[-1], 150)
        self.assertIsNone(signal)

    def test_quant_strategy_returns_signal_on_crossover(self):
        strategy = QuantStrategy(self.mock_broker, "005930", short_window=2, long_window=3)

        self.assertIsNone(strategy.on_market_data({'price': 3}))
        self.assertIsNone(strategy.on_market_data({'price': 2}))
        self.assertIsNone(strategy.on_market_data({'price': 1}))
        self.assertIsNone(strategy.on_market_data({'price': 2}))
        signal = strategy.on_market_data({'price': 3})

        self.assertEqual(signal.side, "BUY")
        self.assertEqual(signal.symbol, "005930")
        self.assertEqual(signal.price, 3)

    def test_hft_strategy_returns_signal_on_price_drop(self):
        strategy = HFTStrategy(self.mock_broker, "005930", tick_size=100)

        self.assertIsNone(strategy.on_market_data({'price': 1000}))
        signal = strategy.on_market_data({'price': 900})

        self.assertEqual(signal.side, "BUY")
        self.assertEqual(signal.symbol, "005930")
        self.assertEqual(signal.price, 900)

if __name__ == '__main__':
    unittest.main()
