import csv
import json
from dataclasses import asdict
from pathlib import Path

from simple_charts import write_bar_chart, write_histogram, write_line_chart


def write_execution_report(output_dir, metrics, ppo_results, baseline_results=None, title="PPO Execution Report"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_results = baseline_results or {}

    metrics_path = output_dir / "metrics.json"
    episodes_path = output_dir / "episodes.csv"
    fills_path = output_dir / "fills.csv"
    report_path = output_dir / "report.md"
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_episodes(episodes_path, ppo_results, baseline_results)
    _write_fills(fills_path, ppo_results)
    chart_paths = _write_charts(charts_dir, ppo_results, baseline_results)
    _write_markdown(report_path, title, metrics, chart_paths)
    return {
        "report": report_path,
        "metrics": metrics_path,
        "episodes": episodes_path,
        "fills": fills_path,
        "charts": chart_paths,
    }


def _write_episodes(path, ppo_results, baseline_results):
    columns = ["policy", "symbol", "date", "side", "parent_quantity", "executed_quantity", "remaining_quantity", "shortfall_bps"]
    rows = []
    for result in ppo_results:
        rows.append(_episode_row("PPO", result))
    for name, results in baseline_results.items():
        for result in results:
            rows.append(_episode_row(name, result))

    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_fills(path, ppo_results):
    columns = [
        "date",
        "time",
        "symbol",
        "side",
        "quantity",
        "price",
        "value",
        "shortfall",
        "shortfall_bps",
        "participation",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for result in ppo_results:
            for fill in result.get("fills", []):
                writer.writerow(asdict(fill))


def _write_charts(charts_dir, ppo_results, baseline_results):
    paths = {
        "shortfall_distribution": charts_dir / "shortfall_distribution.png",
        "episode_shortfall": charts_dir / "episode_shortfall.png",
        "inventory_completion": charts_dir / "inventory_completion.png",
    }
    write_histogram(paths["shortfall_distribution"], [result["shortfall_bps"] for result in ppo_results])
    write_line_chart(paths["episode_shortfall"], [[result["shortfall_bps"] for result in ppo_results]])
    write_bar_chart(
        paths["inventory_completion"],
        [result["executed_quantity"] / max(result["parent_quantity"], 1) for result in ppo_results],
    )
    for name, results in baseline_results.items():
        path = charts_dir / f"{name.lower()}_shortfall.png"
        write_line_chart(path, [[result["shortfall_bps"] for result in results]])
        paths[f"{name.lower()}_shortfall"] = path
    return paths


def _write_markdown(path, title, metrics, chart_paths):
    lines = [
        f"# {title}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {_format_value(value)} |")
    lines.extend(["", "## Charts", ""])
    for name, chart_path in chart_paths.items():
        lines.append(f"![{name}]({chart_path.relative_to(path.parent)})")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _episode_row(policy, result):
    return {
        "policy": policy,
        "symbol": result["symbol"],
        "date": result["date"],
        "side": result["side"],
        "parent_quantity": result["parent_quantity"],
        "executed_quantity": result["executed_quantity"],
        "remaining_quantity": result["remaining_quantity"],
        "shortfall_bps": result["shortfall_bps"],
    }


def _format_value(value):
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)
