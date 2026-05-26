import csv
import json
from dataclasses import asdict
from pathlib import Path

from performance import equity_drawdowns
from simple_charts import write_bar_chart, write_histogram, write_line_chart


def write_backtest_report(result, metrics, bars, output_dir, title="Backtest Report"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = output_dir / "metrics.json"
    trades_path = output_dir / "trades.csv"
    equity_path = output_dir / "equity_curve.csv"
    report_path = output_dir / "report.md"
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    _write_json(metrics_path, metrics)
    _write_trades(trades_path, result.fills)
    _write_equity(equity_path, result.equity_curve)
    chart_paths = _write_charts(charts_dir, result, bars)
    _write_markdown(report_path, title, metrics, chart_paths, result)

    return {
        "report": report_path,
        "metrics": metrics_path,
        "trades": trades_path,
        "equity_curve": equity_path,
        "charts": chart_paths,
    }


def _write_json(path, data):
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _write_trades(path, fills):
    columns = [
        "date",
        "symbol",
        "side",
        "quantity",
        "price",
        "value",
        "commission",
        "tax",
        "realized_pnl",
        "cash_after",
        "reason",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for fill in fills:
            writer.writerow(asdict(fill))


def _write_equity(path, equity_curve):
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "cash", "position_value", "equity"])
        writer.writeheader()
        for point in equity_curve:
            writer.writerow(asdict(point))


def _write_charts(charts_dir, result, bars):
    chart_paths = {}
    equity_values = [point.equity for point in result.equity_curve]
    benchmark = _benchmark_equity(result.config.initial_cash, bars)
    equity_series = [equity_values]
    if benchmark:
        equity_series.append(benchmark)
    chart_paths["equity"] = charts_dir / "equity_curve.png"
    write_line_chart(chart_paths["equity"], equity_series)

    chart_paths["drawdown"] = charts_dir / "drawdown.png"
    write_line_chart(chart_paths["drawdown"], [[row["drawdown"] for row in equity_drawdowns(result.equity_curve)]])

    chart_paths["price"] = charts_dir / "price_trades.png"
    write_line_chart(chart_paths["price"], [[bar.close for bar in bars]])

    chart_paths["monthly_returns"] = charts_dir / "monthly_returns.png"
    write_bar_chart(chart_paths["monthly_returns"], _monthly_returns(result.equity_curve))

    chart_paths["trade_pnl"] = charts_dir / "trade_pnl_distribution.png"
    write_histogram(chart_paths["trade_pnl"], [fill.realized_pnl for fill in result.fills if fill.side == "SELL"])

    return chart_paths


def _write_markdown(path, title, metrics, chart_paths, result):
    lines = [
        f"# {title}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {_format_metric(value)} |")

    lines.extend(
        [
            "",
            "## Charts",
            "",
        ]
    )
    for name, chart_path in chart_paths.items():
        lines.append(f"![{name}]({chart_path.relative_to(path.parent)})")
        lines.append("")

    lines.extend(
        [
            "## Execution",
            "",
            f"- Fills: {len(result.fills)}",
            f"- Rejected signals: {len(result.rejected_signals)}",
            f"- Execution policy: {result.config.execution_policy}",
            f"- Initial cash: {result.config.initial_cash}",
            f"- Ending cash: {result.ending_cash}",
        ]
    )

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _benchmark_equity(initial_cash, bars):
    if not bars:
        return []
    first_close = bars[0].close
    if first_close == 0:
        return []
    return [initial_cash * (bar.close / first_close) for bar in bars]


def _monthly_returns(equity_curve):
    months = {}
    for point in equity_curve:
        months.setdefault(point.date[:7], []).append(point.equity)
    values = []
    for equities in months.values():
        if equities and equities[0] != 0:
            values.append((equities[-1] / equities[0]) - 1)
    return values


def _format_metric(value):
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)
