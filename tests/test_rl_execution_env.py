import unittest

from rl_execution.data import make_synthetic_episode
from rl_execution.env import OrderExecutionEnv
from rl_execution.simulator import BUY, ExecutionConfig


class TestOrderExecutionEnv(unittest.TestCase):
    def test_reset_and_step_follow_gymnasium_contract(self):
        env = OrderExecutionEnv(
            [make_synthetic_episode(minutes=3)],
            execution_config=ExecutionConfig(),
            side=BUY,
        )

        obs, info = env.reset(seed=1)
        next_obs, reward, terminated, truncated, step_info = env.step([0.5])

        self.assertEqual(obs.shape, (10,))
        self.assertEqual(next_obs.shape, (10,))
        self.assertIsInstance(info, dict)
        self.assertFalse(truncated)
        self.assertIsInstance(reward, float)
        self.assertIn("remaining_quantity", step_info)

    def test_terminal_step_forces_completion(self):
        env = OrderExecutionEnv(
            [make_synthetic_episode(minutes=1)],
            execution_config=ExecutionConfig(),
            side=BUY,
        )

        env.reset()
        _, _, terminated, _, info = env.step([0.0])

        self.assertTrue(terminated)
        self.assertEqual(info["remaining_quantity"], 0)
        self.assertEqual(info["executed_quantity"], info["parent_quantity"])


if __name__ == "__main__":
    unittest.main()
