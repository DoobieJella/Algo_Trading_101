import random

import numpy as np

from rl_execution.simulator import (
    BUY,
    SELL,
    ExecutionConfig,
    choose_child_quantity,
    execute_child_order,
    leftover_penalty,
    reward_from_fill,
)

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # Allows deterministic unit tests without RL dependencies installed locally.
    gym = None

    class _Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

        def sample(self):
            return np.zeros(self.shape, dtype=self.dtype)

    class spaces:
        Box = _Box


class _EnvBase:
    pass


if gym is not None:
    _EnvBase = gym.Env


class OrderExecutionEnv(_EnvBase):
    metadata = {"render_modes": []}

    def __init__(
        self,
        episodes,
        execution_config=None,
        parent_order_fraction=0.05,
        side="random",
        seed=None,
    ):
        self.episodes = [episode for episode in episodes if episode]
        if not self.episodes:
            raise ValueError("OrderExecutionEnv requires at least one non-empty episode")

        self.execution_config = execution_config or ExecutionConfig()
        self.parent_order_fraction = parent_order_fraction
        self.side = side
        self.random = random.Random(seed)
        self.episode_index = 0
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-10.0, high=10.0, shape=(10,), dtype=np.float32)
        self.current_episode = None
        self.current_step = 0
        self.parent_quantity = 0
        self.remaining_quantity = 0
        self.arrival_price = 0.0
        self.current_side = BUY
        self.fills = []
        self.last_action = 0.0

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.random.seed(seed)
        self.current_episode = self.episodes[self.episode_index % len(self.episodes)]
        self.episode_index += 1
        self.current_step = 0
        self.current_side = self._select_side()
        self.arrival_price = self.current_episode[0].close
        total_volume = sum(bar.volume for bar in self.current_episode)
        self.parent_quantity = max(1, int(total_volume * self.parent_order_fraction))
        self.remaining_quantity = self.parent_quantity
        self.fills = []
        self.last_action = 0.0
        return self._observation(), {}

    def step(self, action):
        action_value = float(np.asarray(action).reshape(-1)[0])
        bar = self.current_episode[self.current_step]
        last_step = self.current_step == len(self.current_episode) - 1
        quantity = choose_child_quantity(action_value, self.remaining_quantity, force_complete=last_step)
        fill = execute_child_order(
            bar,
            self.current_side,
            quantity,
            self.arrival_price,
            self.parent_quantity,
            self.execution_config,
        )
        if fill is not None:
            self.fills.append(fill)
            self.remaining_quantity -= quantity

        remaining_fraction = self.remaining_quantity / max(self.parent_quantity, 1)
        reward = reward_from_fill(fill, remaining_fraction, self.execution_config)
        terminated = last_step or self.remaining_quantity <= 0
        if terminated and self.remaining_quantity > 0:
            penalty = leftover_penalty(self.remaining_quantity, self.parent_quantity, self.execution_config)
            reward -= penalty

        self.last_action = min(1.0, max(0.0, action_value))
        self.current_step += 1
        info = self._info()
        observation = self._observation() if not terminated else np.zeros(self.observation_space.shape, dtype=np.float32)
        return observation, float(reward), terminated, False, info

    def _select_side(self):
        if self.side.upper() in {BUY, SELL}:
            return self.side.upper()
        return BUY if self.random.random() < 0.5 else SELL

    def _observation(self):
        index = min(self.current_step, len(self.current_episode) - 1)
        bar = self.current_episode[index]
        previous = self.current_episode[max(0, index - 1)]
        recent = self.current_episode[max(0, index - 5):index + 1]
        returns = [
            (recent[pos].close / recent[pos - 1].close) - 1
            for pos in range(1, len(recent))
            if recent[pos - 1].close
        ]
        total_volume = sum(item.volume for item in self.current_episode)
        elapsed_volume = sum(item.volume for item in self.current_episode[:index + 1])
        return np.array(
            [
                (len(self.current_episode) - index) / len(self.current_episode),
                self.remaining_quantity / max(self.parent_quantity, 1),
                1.0 if self.current_side == BUY else -1.0,
                (bar.close / previous.close) - 1 if previous.close else 0.0,
                float(np.std(returns)) if returns else 0.0,
                bar.volume / max(total_volume, 1),
                elapsed_volume / max(total_volume, 1),
                (bar.close / self.arrival_price) - 1 if self.arrival_price else 0.0,
                1 - (self.remaining_quantity / max(self.parent_quantity, 1)),
                self.last_action,
            ],
            dtype=np.float32,
        )

    def _info(self):
        executed_quantity = self.parent_quantity - self.remaining_quantity
        total_shortfall = sum(fill.shortfall for fill in self.fills)
        total_shortfall_bps = total_shortfall / max(self.arrival_price * self.parent_quantity, 1) * 10000
        return {
            "symbol": self.current_episode[0].symbol,
            "date": self.current_episode[0].date,
            "side": self.current_side,
            "parent_quantity": self.parent_quantity,
            "executed_quantity": executed_quantity,
            "remaining_quantity": self.remaining_quantity,
            "shortfall": total_shortfall,
            "shortfall_bps": total_shortfall_bps,
            "fills": list(self.fills),
        }
