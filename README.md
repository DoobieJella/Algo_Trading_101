# Oh My Quant

**Oh My Quant** is a containerized Python backend for algorithmic trading research and execution, starting with Korea Investment & Securities Open API integration.

The project is designed around modular trading strategies, mock/live execution modes, and a future workflow where AI agents can generate, backtest, evaluate, and iterate on strategies automatically.

> Status: early prototype. The current codebase provides the backend scaffold, KIS API wrapper, KIS data probing, daily-bar normalization, a lightweight backtesting engine, example strategy classes, Docker setup, and tests. Production trading controls and full live broker coverage are still under development.

## Goals

- Integrate Korea Investment & Securities Open API for market data, authentication, and order placement.
- Support interchangeable strategy modules for quant, arbitrage, scalping, and fundamental trading.
- Keep mock and live execution paths explicit so strategies can be tested before capital is at risk.
- Add backtesting, automated strategy evaluation, and AI-assisted strategy generation over time.
- Provide a clean backend foundation that can later support dashboards, schedulers, and research workflows.

## Project Structure

```text
.
├── src/
│   ├── main.py                  # Application entry point
│   ├── kis_api.py               # KIS API wrapper and mock/live broker interface
│   ├── kis_catalog.py           # KIS workbook endpoint catalog parser
│   ├── kis_probe.py             # Read-only KIS data availability probe
│   ├── kis_data.py              # Daily OHLCV normalization and storage
│   ├── backtest.py              # In-memory and daily event-driven backtesting
│   ├── performance.py           # Backtest performance metrics
│   ├── reporting.py             # Markdown/CSV/PNG report writer
│   ├── rl_execution/            # PPO order execution research framework
│   ├── strategy.py              # Base strategy abstraction
│   └── strategies/              # Concrete strategy implementations
├── tests/                       # Strategy and backend tests
├── KIS/                         # KIS reference files and conversion utilities
├── docs/                        # Code review and research notes
├── Dockerfile                   # Python runtime image
├── docker-compose.yml           # Local development container
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variable template
```

## Strategy Modules

Current strategy examples live in `src/strategies/`:

- `quant_strategy.py`: moving-average style quantitative strategy scaffold.
- `arbitrage_strategy.py`: cross-instrument arbitrage strategy scaffold.
- `hft_scalper.py`: short-horizon scalping strategy scaffold.
- `fundamental_long_short.py`: fundamental long/short strategy scaffold.

Each strategy inherits from `Strategy` and implements:

```python
def on_market_data(self, data):
    ...
```

## Setup

Create a local environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create your local configuration:

```bash
cp .env.example .env
```

Fill in KIS credentials in `.env`. Keep `TRADING_MODE=MOCK` for local development unless you are intentionally testing live broker behavior.

Use `KIS_API_ENV=VIRTUAL` for read-only data endpoint verification before using `REAL`.

## Running Locally

Run the application entry point:

```bash
python src/main.py
```

Run tests:

```bash
PYTHONPATH=src python -m pytest
```

Start the Docker development container. The Compose service stays idle so you can run commands manually:

```bash
docker compose up --build
```

Open a shell inside the container:

```bash
docker compose exec trading_bot bash
```

Run commands inside the container:

```bash
docker compose exec trading_bot python -m pytest
```

To run the bot loop explicitly:

```bash
docker compose exec trading_bot python src/main.py
```

## KIS Data Discovery

Probe read-only domestic stock market-data endpoints using the KIS virtual environment:

```bash
PYTHONPATH=src python src/kis_probe.py \
  --symbols 005930 000660 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

The probe writes `availability.csv` and `availability.json` under `reports/kis_probe/<run_id>/`. It targets domestic stock quote and daily OHLCV endpoints only; it does not call order or account mutation endpoints.

Download and normalize daily OHLCV:

```bash
PYTHONPATH=src python src/kis_download.py \
  --symbol 005930 \
  --start-date 2024-01-01 \
  --end-date 2024-03-31
```

Normalized data is stored as CSV plus metadata under `data/kis/domestic_stock/daily/`.

## Backtesting

Run a daily backtest from normalized data:

```bash
PYTHONPATH=src python src/run_backtest.py \
  --data data/kis/domestic_stock/daily/005930.csv \
  --symbol 005930 \
  --strategy quant \
  --param short_window=5 \
  --param long_window=20
```

Backtests use next-day-open execution by default and write `report.md`, `metrics.json`, `trades.csv`, `equity_curve.csv`, and PNG charts under `reports/backtests/<run_id>/`.

## PPO Order Execution Research

The PPO execution framework is offline research only. It trains on archived KIS-derived minute bars and never places live KIS orders.

Probe execution-relevant KIS endpoints:

```bash
PYTHONPATH=src python src/rl_execution/probe_execution_data.py \
  --symbols 005930 000660
```

Archive current-day minute bars:

```bash
PYTHONPATH=src python src/rl_execution/kis_download_minutes.py \
  --symbol 005930 \
  --date 2026-05-26
```

Train PPO on archived minute bars:

```bash
PYTHONPATH=src python src/rl_execution/train_ppo.py \
  --symbol 005930 \
  --data-root data/kis/domestic_stock/minute \
  --horizon-minutes 30 \
  --total-timesteps 500000
```

Evaluate PPO against TWAP and VWAP:

```bash
PYTHONPATH=src python src/rl_execution/evaluate_ppo.py \
  --run-id <run_id> \
  --split test
```

Outputs are written under `models/ppo_execution/<run_id>/` and `reports/ppo_execution/<run_id>/`.

Docker provides a separate idle service for RL work:

```bash
docker compose up --build
docker compose exec rl_trainer python src/rl_execution/train_ppo.py --symbol 005930
docker compose exec rl_trainer python src/rl_execution/evaluate_ppo.py --run-id <run_id> --split test
```

PPO reports include aggregate metrics, per-episode PPO/TWAP/VWAP comparisons, fill-level detail, and PNG charts.

## Configuration

Environment variables are documented in `.env.example`:

- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `KIS_ACCOUNT_NO`
- `KIS_CANO`
- `KIS_ACQE`
- `TRADING_MODE`
- `KIS_API_ENV`

Do not commit real credentials, account numbers, access tokens, or trading logs containing sensitive information.

## Future AI Harness

Oh My Quant is designed to evolve into an AI-assisted strategy research harness. Instead of giving an AI agent direct control over trading, the harness will expose controlled tools for strategy generation, backtesting, evaluation, and review.

Future agents may generate strategy candidates, run them through historical backtests, evaluate risk-adjusted performance, suggest refinements, and produce human-readable reports. Strategies that pass evaluation can then move into mock execution before any live-trading approval.

The goal is to make AI useful in the research loop while keeping broker access, risk controls, and live execution behind explicit system boundaries.

```text
Market Data
   ↓
Strategy Generator Agent
   ↓
Static Review / Risk Review
   ↓
Backtesting Engine
   ↓
Evaluation Metrics
   ↓
Paper Trading / Mock Execution
   ↓
Human Approval
   ↓
Live Execution
```

## Roadmap

- Expand KIS market-data endpoint coverage beyond domestic daily stocks.
- Add a broker abstraction for safer mock/live execution switching.
- Add realistic transaction-cost presets and richer strategy sizing controls.
- Add LOB snapshots and limit-order placement modeling for RL execution research.
- Add AI-assisted strategy generation, risk review, refinement, and reporting workflows.
- Add risk controls, position sizing, and trade safety checks.

## Disclaimer

This project is for research and engineering development. It is not financial advice and is not ready for unattended live trading. Review, test, and risk-limit every strategy before connecting real capital.
