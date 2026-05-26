import argparse
from datetime import datetime
from pathlib import Path

from backtest import BacktestConfig, run_daily_backtest
from broker import MockBroker
from kis_data import read_daily_bars
from performance import calculate_metrics
from reporting import write_backtest_report
from strategy_registry import create_strategy, validate_daily_backtest_strategy


def main():
    parser = argparse.ArgumentParser(description="Run a daily strategy backtest on normalized KIS data.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--strategy", default="quant")
    parser.add_argument("--initial-cash", type=float, default=10_000_000)
    parser.add_argument("--commission-rate", type=float, default=0.0)
    parser.add_argument("--tax-rate", type=float, default=0.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--output-dir", default="reports/backtests")
    parser.add_argument("--param", action="append", default=[])
    args = parser.parse_args()

    validate_daily_backtest_strategy(args.strategy)
    bars = [bar for bar in read_daily_bars(args.data) if bar.symbol == args.symbol]
    if not bars:
        raise ValueError(f"No bars found for symbol {args.symbol}: {args.data}")

    broker = MockBroker()
    strategy = create_strategy(args.strategy, broker, args.symbol, **_parse_params(args.param))
    config = BacktestConfig(
        initial_cash=args.initial_cash,
        commission_rate=args.commission_rate,
        tax_rate=args.tax_rate,
        slippage_bps=args.slippage_bps,
    )
    result = run_daily_backtest(strategy, bars, config=config)
    metrics = calculate_metrics(result, benchmark_bars=bars)
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{args.strategy}_{args.symbol}"
    outputs = write_backtest_report(
        result,
        metrics,
        bars,
        Path(args.output_dir) / run_id,
        title=f"{args.strategy} backtest: {args.symbol}",
    )
    print(f"Backtest complete: {outputs['report']}")


def _parse_params(params):
    parsed = {}
    for item in params:
        if "=" not in item:
            raise ValueError(f"Strategy param must use key=value: {item}")
        key, value = item.split("=", 1)
        parsed[key] = _coerce_value(value)
    return parsed


def _coerce_value(value):
    for coercer in (int, float):
        try:
            return coercer(value)
        except ValueError:
            pass
    return value


if __name__ == "__main__":
    main()
