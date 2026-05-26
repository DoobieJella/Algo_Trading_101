import unittest

from rl_execution.baselines import evaluate_twap, evaluate_vwap, twap_schedule, vwap_schedule
from rl_execution.data import make_synthetic_episode
from rl_execution.simulator import BUY


class TestRlExecutionBaselines(unittest.TestCase):
    def test_twap_schedule_completes_parent_quantity(self):
        schedule = twap_schedule(10, 3)

        self.assertEqual(sum(schedule), 10)
        self.assertEqual(schedule, [4, 3, 3])

    def test_vwap_schedule_completes_parent_quantity(self):
        bars = make_synthetic_episode(minutes=3)
        schedule = vwap_schedule(10, bars)

        self.assertEqual(sum(schedule), 10)

    def test_baseline_evaluation_returns_shortfall(self):
        bars = make_synthetic_episode(minutes=3)

        result = evaluate_twap(bars, BUY, 10)
        vwap = evaluate_vwap(bars, BUY, 10)

        self.assertEqual(result["executed_quantity"], 10)
        self.assertEqual(vwap["executed_quantity"], 10)
        self.assertIn("shortfall_bps", result)


if __name__ == "__main__":
    unittest.main()
