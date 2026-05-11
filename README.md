# Oh My Quant

**Oh My Quant** is a containerized Python backend for algorithmic trading research and execution, starting with Korea Investment & Securities Open API integration.

The project is designed around modular trading strategies, mock/live execution modes, and a future workflow where AI agents can generate, backtest, evaluate, and iterate on strategies automatically.

> Status: early prototype. The current codebase provides the backend scaffold, KIS API wrapper, example strategy classes, Docker setup, and initial tests. Production trading controls, full broker coverage, and backtesting are still under development.

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
│   ├── strategy.py              # Base strategy abstraction
│   └── strategies/              # Concrete strategy implementations
├── tests/                       # Strategy and backend tests
├── KIS/                         # KIS reference files and conversion utilities
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

## Running Locally

Run the application entry point:

```bash
python src/main.py
```

Run tests:

```bash
PYTHONPATH=src python -m pytest
```

Start the Docker development container:

```bash
docker compose up --build
```

Open a shell inside the container:

```bash
docker compose exec trading_bot bash
```

## Configuration

Environment variables are documented in `.env.example`:

- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `KIS_ACCOUNT_NO`
- `KIS_CANO`
- `KIS_ACQE`
- `TRADING_MODE`

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

- Complete KIS API authentication, market data, and order endpoints.
- Add a broker abstraction for safer mock/live execution switching.
- Add historical data ingestion and backtesting.
- Add strategy evaluation metrics and automated reports.
- Add AI-assisted strategy generation, risk review, refinement, and reporting workflows.
- Add risk controls, position sizing, and trade safety checks.

## Disclaimer

This project is for research and engineering development. It is not financial advice and is not ready for unattended live trading. Review, test, and risk-limit every strategy before connecting real capital.
