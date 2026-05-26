# Code Review

## 1. Project Objective

Oh My Quant is an early-stage Python trading-bot and research prototype for Korea Investment & Securities API data access, mock/live broker separation, daily strategy backtesting, performance reporting, and offline PPO order-execution research.

## 2. Repository Structure

- `src/main.py`: application entry point; loads config, creates a broker, initializes strategies, and runs the polling loop.
- `src/config.py`: environment-backed configuration for trading mode and read-only KIS data access mode.
- `src/broker.py`: broker abstraction plus `MockBroker`, `KisBroker`, and broker factory.
- `src/kis_api.py`: KIS API wrapper with mock responses, OAuth, generic read-only requests, current price, and domestic daily chart access.
- `src/kis_catalog.py`: parser for the KIS workbook API index.
- `src/kis_probe.py`: read-only domestic stock data endpoint availability probe.
- `src/kis_data.py`: KIS daily OHLCV normalization, CSV/metadata writing, and CSV reading.
- `src/backtest.py`: legacy in-memory runner plus daily next-open event-driven backtester.
- `src/performance.py`, `src/reporting.py`, `src/simple_charts.py`: metrics, Markdown/CSV/PNG reports, and dependency-free chart rendering.
- `src/strategy_registry.py`, `src/run_backtest.py`: strategy lookup and CLI backtest runner.
- `src/rl_execution/`: offline PPO order execution research package with minute-bar data loading, a Gym-compatible environment, simulator, TWAP/VWAP baselines, training/evaluation CLIs, and reports.
- `src/strategies/`: concrete strategy examples.
- `tests/`: pytest/unittest coverage for config, broker behavior, KIS data utilities, probes, backtesting, metrics, reporting, and strategy signals.
- `KIS/`: KIS reference workbook and Excel-to-JSON conversion helper.
- `docs/code_review.md`, `docs/ppo_order_execution_research.md`: agent-maintained repository notes and PPO execution research notes.
- `Dockerfile` and `docker-compose.yml`: Python 3.10 container setup; Compose keeps the container idle for manual commands.

## 3. Main Execution Flow

`main.py` loads `AppConfig`, validates trading settings, creates a broker, authenticates, blocks REAL strategy execution, initializes strategies, and passes current-price ticks into strategies. Strategies return `Signal` objects, and the broker executes them.

KIS data discovery uses `kis_probe.py`: it parses `KIS/KIS_open_API.xlsx`, selects virtual-supported domestic stock quote endpoints, calls them through `KisApi.request()`, and writes availability reports under `reports/kis_probe/`.

Daily data ingestion uses `kis_download.py`: it calls the domestic daily item chart endpoint, normalizes KIS fields into `DailyBar`, and writes CSV plus JSON metadata under `data/kis/domestic_stock/daily/`.

Backtesting uses `run_backtest.py`: it reads normalized daily bars, creates a strategy through the registry, runs `run_daily_backtest()` with next-day-open fills, computes metrics, and writes report artifacts under `reports/backtests/`.

PPO execution research uses `src/rl_execution/`: KIS minute bars are archived to CSV, PPO trains in an offline Gym-compatible environment where actions are participation fractions of remaining parent quantity, and evaluation compares PPO against TWAP and VWAP by implementation shortfall.

## 4. Key Components

- `AppConfig.validate()` validates bot trading mode; `validate_kis_data_access()` validates credentials for `KIS_API_ENV=VIRTUAL|REAL`.
- `KisApi` supports `MOCK`, `VIRTUAL`, and `REAL` modes for read-only data calls. MOCK returns deterministic local payloads and does not call HTTP.
- `DailyBar` is the normalized daily OHLCV contract used by data storage and daily backtests.
- `run_daily_backtest()` requires `MockBroker`, fills signals at next day open, tracks cash, positions, fills, rejected signals, and daily equity.
- `calculate_metrics()` produces return, risk, drawdown, trade-quality, exposure, turnover, and benchmark metrics.
- `write_backtest_report()` writes `report.md`, `metrics.json`, `trades.csv`, `equity_curve.csv`, and PNG charts.
- `OrderExecutionEnv` is an offline RL environment for market-order scheduling; it never calls live KIS order placement.
- `train_ppo.py` and `evaluate_ppo.py` require Stable-Baselines3/PyTorch and write model/report artifacts under `models/ppo_execution/` and `reports/ppo_execution/`.

## 5. Data, Inputs, and Outputs

Configuration comes from `.env`; `.env.example` documents `TRADING_MODE` for bot execution and `KIS_API_ENV` for read-only data tools. KIS probe outputs go to `reports/kis_probe/<run_id>/availability.csv` and `.json`. Normalized daily bars are stored as `data/kis/domestic_stock/daily/<symbol>.csv` plus `<symbol>.metadata.json`. PPO execution minute bars are stored under `data/kis/domestic_stock/minute/<symbol>/<date>.csv`. Backtest outputs go to `reports/backtests/<run_id>/`; RL model/report outputs go to `models/ppo_execution/<run_id>/` and `reports/ppo_execution/<run_id>/`.

## 6. Environment and Execution

The Docker runtime uses Python 3.10 and includes the `KIS/` reference workbook needed by catalog/probe tests. Local setup should use a virtual environment and install `requirements.txt`. Tests run with `PYTHONPATH=src python -m pytest`. Docker Compose starts idle `trading_bot` and `rl_trainer` containers with `tail -f /dev/null`; run commands manually with `docker compose exec ...`. REAL strategy execution is blocked in `main.py` until risk controls are implemented.

## 7. Current Implementation Notes

The code uses absolute imports from `src` with `PYTHONPATH=src`. Tests combine `unittest` assertions with pytest discovery. KIS data probes are intentionally read-only. The daily backtester executes exact strategy signal quantities; there is no portfolio sizing layer yet. PPO execution is offline-only and uses minute bars with simple market-order fill assumptions, not full LOB queue replay. Chart rendering uses a small built-in PNG writer instead of adding plotting dependencies.

## 8. Recent Changes

- Added read-only KIS data environment handling via `KIS_API_ENV`.
- Added KIS API catalog parsing, endpoint probing, daily OHLCV normalization, and CSV/metadata storage.
- Added a daily next-open backtesting engine with fills, rejected signals, equity curve, metrics, and Markdown/PNG reporting.
- Added CLI entry points for probing KIS data, downloading normalized daily bars, and running daily backtests.
- Updated Docker Compose to start an idle development container.
- On May 25, 2026, a read-only KIS virtual probe for `005930` confirmed quote and date-range daily chart access; `inquire-daily-price` returned HTTP 500 for the tested range.
- Added PPO order execution research scaffolding with KIS minute-bar archival, Gym-compatible environment, TWAP/VWAP baselines, SB3 training/evaluation CLIs, and reports.
- On May 26, 2026, Docker PPO smoke testing with MOCK KIS minute data verified minute archival, SB3 training, model artifact writing, evaluation, baseline comparison, and report generation.

## 9. Known Issues, Risks, and TODOs

- Live KIS order methods remain placeholders; REAL strategy execution is still blocked.
- Virtual/REAL KIS integration tests are gated manually and depend on valid credentials and endpoint availability.
- The KIS virtual `inquire-daily-price` endpoint may fail for some requests; v1 normalized OHLCV should use `inquire-daily-itemchartprice`.
- Daily backtests currently execute fixed signal quantities and do not include advanced sizing or margin logic.
- Fundamental strategy backtesting needs historical fundamentals before unbiased evaluation.
- Generated `data/` and `reports/` artifacts are ignored by git.
- PPO execution v1 uses minute bars; SOTA-like limit-order placement requires LOB snapshots, queue modeling, and stronger simulator validation.
- The RL Docker image currently installs Stable-Baselines3 through the normal Python dependency path; PyTorch may make the image large and should be optimized if build/pull size becomes a problem.
