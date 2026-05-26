import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rl_execution.baselines import evaluate_twap, evaluate_vwap
from rl_execution.data import make_synthetic_episode
from rl_execution.metrics import summarize_execution_results
from rl_execution.report import write_execution_report
from rl_execution.simulator import BUY


class TestRlExecutionReport(unittest.TestCase):
    def test_writes_execution_report_artifacts(self):
        bars = make_synthetic_episode(minutes=3)
        ppo_result = evaluate_twap(bars, BUY, 10)
        baselines = {
            "TWAP": [evaluate_twap(bars, BUY, 10)],
            "VWAP": [evaluate_vwap(bars, BUY, 10)],
        }
        metrics = summarize_execution_results([ppo_result], baselines)

        with TemporaryDirectory() as directory:
            outputs = write_execution_report(Path(directory), metrics, [ppo_result], baselines)

            self.assertTrue(outputs["report"].exists())
            self.assertTrue(outputs["metrics"].exists())
            self.assertTrue(outputs["episodes"].exists())
            self.assertEqual(outputs["charts"]["shortfall_distribution"].read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
