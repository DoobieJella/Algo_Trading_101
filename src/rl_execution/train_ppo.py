import argparse
import json
from datetime import datetime
from pathlib import Path

from rl_execution.data import load_symbol_episodes, split_episodes_by_date
from rl_execution.env import OrderExecutionEnv
from rl_execution.simulator import ExecutionConfig


def main():
    parser = argparse.ArgumentParser(description="Train PPO for offline order execution research.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--data-root", default="data/kis/domestic_stock/minute")
    parser.add_argument("--initial-cash", type=float, default=10_000_000)
    parser.add_argument("--horizon-minutes", type=int, default=30)
    parser.add_argument("--total-timesteps", type=int, default=500_000)
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--output-root", default="models/ppo_execution")
    args = parser.parse_args()

    PPO, DummyVecEnv, VecNormalize, Monitor = _load_sb3()
    episodes = load_symbol_episodes(args.data_root, args.symbol, horizon_minutes=args.horizon_minutes)
    splits = split_episodes_by_date(episodes)
    if not splits.train:
        raise ValueError(f"No training episodes found for {args.symbol} in {args.data_root}")

    config = ExecutionConfig(initial_cash=args.initial_cash)
    env = DummyVecEnv([
        _make_env(splits.train, config, seed=index)
        for index in range(args.n_envs)
    ])
    env = VecNormalize(env, norm_obs=True, norm_reward=True)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=512,
        batch_size=256,
        learning_rate=3e-4,
        gamma=1.0,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        max_grad_norm=0.5,
        device="cpu",
    )
    model.learn(total_timesteps=args.total_timesteps)

    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{args.symbol}"
    output_dir = Path(args.output_root) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save(output_dir / "model")
    env.save(output_dir / "vecnormalize.pkl")
    (output_dir / "config.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "symbol": args.symbol,
                "data_root": args.data_root,
                "horizon_minutes": args.horizon_minutes,
                "total_timesteps": args.total_timesteps,
                "initial_cash": args.initial_cash,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"PPO training complete: {output_dir}")


def _make_env(episodes, config, seed):
    def factory():
        env = OrderExecutionEnv(episodes, execution_config=config, seed=seed)
        try:
            from stable_baselines3.common.monitor import Monitor
            return Monitor(env)
        except ImportError:
            return env

    return factory


def _load_sb3():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        from stable_baselines3.common.monitor import Monitor
    except ImportError as error:
        raise RuntimeError(
            "PPO training requires stable-baselines3, gymnasium, and torch. "
            "Install the project RL requirements or run inside the rl_trainer container."
        ) from error
    return PPO, DummyVecEnv, VecNormalize, Monitor


if __name__ == "__main__":
    main()
