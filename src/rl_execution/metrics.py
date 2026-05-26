def summarize_execution_results(results, baseline_results=None):
    baseline_results = baseline_results or {}
    shortfalls = [result["shortfall_bps"] for result in results]
    completion = [result["executed_quantity"] / max(result["parent_quantity"], 1) for result in results]
    metrics = {
        "episodes": len(results),
        "average_shortfall_bps": _mean(shortfalls),
        "median_shortfall_bps": _median(shortfalls),
        "completion_rate": _mean(completion),
        "average_leftover_quantity": _mean([result["remaining_quantity"] for result in results]),
        "average_participation_rate": _mean(_participations(results)),
        "execution_notional": sum(abs(fill.value) for result in results for fill in result.get("fills", [])),
    }

    for name, baseline in baseline_results.items():
        baseline_shortfalls = [result["shortfall_bps"] for result in baseline]
        wins = [
            result["shortfall_bps"] < benchmark["shortfall_bps"]
            for result, benchmark in zip(results, baseline)
        ]
        metrics[f"{name.lower()}_average_shortfall_bps"] = _mean(baseline_shortfalls)
        metrics[f"win_rate_vs_{name.lower()}"] = _mean([1.0 if win else 0.0 for win in wins])

    return metrics


def _participations(results):
    values = []
    for result in results:
        values.extend(fill.participation for fill in result.get("fills", []))
    return values


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _median(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2
