# PPO Order Execution Research Notes

## Summary

The v1 PPO execution framework is offline research infrastructure. PPO alone is not the differentiator in execution quality; most of the value comes from the environment, action constraints, reward design, market-impact assumptions, and validation against standard benchmarks.

## Primary References

- Schulman et al., [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347), 2017: PPO alternates rollout collection with clipped policy updates and is a practical policy-gradient baseline.
- [Stable-Baselines3 PPO documentation](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html): SB3 PPO supports continuous `Box` action spaces, vectorized environments, save/load, and CPU-oriented training.
- [Gymnasium Env API](https://gymnasium.farama.org/api/env/): custom environments expose `reset()` and `step()` with explicit observation/action spaces.
- Hendricks and Wilcox, [A reinforcement learning extension to the Almgren-Chriss model for optimal trade execution](https://arxiv.org/abs/1403.2229), 2014: execution RL can adapt volume trajectories using market conditions and optimize implementation shortfall.
- Ning, Lin, and Jaimungal, [Double Deep Q-Learning for Optimal Execution](https://arxiv.org/abs/1812.06600), 2018/2020: execution agents should be validated against standard execution benchmarks using out-of-sample symbols/dates.
- Fang et al., [Imitate then Transcend: Multi-Agent Optimal Execution with Dual-Window Denoise PPO](https://arxiv.org/abs/2206.10736), 2022: stronger execution systems use LOB simulation, imitation or denoising, broad market features, and TWAP comparison.
- IJCAI 2022, [Learn Continuously, Act Discretely: Hybrid Action-Space Reinforcement Learning For Optimal Execution](https://www.ijcai.org/proceedings/2022/543): SOTA-like execution research often separates continuous sizing from discrete limit-price placement.

## V1 Design Takeaways

- Start with market-order scheduling over KIS minute bars before modeling limit-order placement.
- Use implementation shortfall as the primary objective because it directly measures execution cost against arrival price.
- Compare PPO to TWAP and VWAP on the same parent orders and dates.
- Keep the RL agent offline-only until data quality, reward design, and simulator assumptions are validated.
- Preserve clear seams for future LOB snapshots, limit-order actions, imitation learning, and richer market-impact models.

## Current V1 Scope

- Data: KIS domestic stock minute bars, archived to CSV.
- Action: fraction of remaining parent order to execute at each minute.
- Environment: one parent order per episode, fixed horizon, terminal forced completion.
- Reward: negative implementation shortfall with optional risk and leftover penalties.
- Training: Stable-Baselines3 PPO with `MlpPolicy`.
- Validation: PPO vs TWAP vs VWAP reports.
