import argparse
import json
from pathlib import Path

from rl_execution.baselines import evaluate_twap, evaluate_vwap
from rl_execution.data import load_symbol_episodes, split_episodes_by_date
from rl_execution.env import OrderExecutionEnv
from rl_execution.metrics import summarize_execution_results
from rl_execution.report import write_execution_report
from rl_execution.simulator import BUY, ExecutionConfig


def main():
    parser = argparse.ArgumentParser(description="Evaluate a trained PPO execution model against TWAP and VWAP.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--models-root", default="models/ppo_execution")
    parser.add_argument("--reports-root", default="reports/ppo_execution")
    parser.add_argument("--split", choices=["train", "validation", "test"], default="test")
    args = parser.parse_args()

    PPO, DummyVecEnv, VecNormalize = _load_sb3()
    model_dir = Path(args.models_root) / args.run_id
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    episodes = load_symbol_episodes(config["data_root"], config["symbol"], config["horizon_minutes"])
    splits = split_episodes_by_date(episodes)
    selected = getattr(splits, args.split)
    if not selected:
        raise ValueError(f"No {args.split} episodes available for {args.run_id}")

    execution_config = ExecutionConfig(initial_cash=config["initial_cash"])
    env = DummyVecEnv([lambda: OrderExecutionEnv(selected, execution_config=execution_config, side=BUY)])
    env = VecNormalize.load(model_dir / "vecnormalize.pkl", env)
    env.training = False
    env.norm_reward = False
    model = PPO.load(model_dir / "model", env=env, device="cpu")

    ppo_results = _evaluate_model(model, env, len(selected))
    baselines = _evaluate_baselines(selected, execution_config)
    metrics = summarize_execution_results(ppo_results, baselines)
    output_dir = Path(args.reports_root) / args.run_id / args.split
    outputs = write_execution_report(output_dir, metrics, ppo_results, baselines)
    print(f"PPO evaluation complete: {outputs['report']}")


def _evaluate_model(model, env, episodes):
    results = []
    for _ in range(episodes):
        obs = env.reset()
        done = [False]
        info = [{}]
        while not done[0]:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, done, info = env.step(action)
        results.append(info[0])
    return results


def _evaluate_baselines(episodes, config):
    twap = []
    vwap = []
    for episode in episodes:
        parent_quantity = max(1, int(sum(bar.volume for bar in episode) * 0.05))
        twap.append(evaluate_twap(episode, BUY, parent_quantity, config=config))
        vwap.append(evaluate_vwap(episode, BUY, parent_quantity, config=config))
    return {"TWAP": twap, "VWAP": vwap}


def _load_sb3():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    except ImportError as error:
        raise RuntimeError(
            "PPO evaluation requires stable-baselines3, gymnasium, and torch. "
            "Install the project RL requirements or run inside the rl_trainer container."
        ) from error
    return PPO, DummyVecEnv, VecNormalize


if __name__ == "__main__":
    main()
