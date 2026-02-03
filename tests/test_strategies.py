import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.strategies.quant_strategy import QuantStrategy
from src.kis_api import KisApi

class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.mock_api = MagicMock(spec=KisApi)
        self.mock_api.get_current_price.return_value = 1000
        self.strategy = QuantStrategy(self.mock_api, "005930", short_window=2, long_window=5)

    def test_quant_logic(self):
        # Feed data
        prices = [100, 110, 120, 130, 140, 150]
        for p in prices:
            self.strategy.on_market_data({'price': p})
            
        # Check if prices were stored
        self.assertEqual(len(self.strategy.prices), 5)
        self.assertEqual(self.strategy.prices[-1], 150)

if __name__ == '__main__':
    unittest.main()
