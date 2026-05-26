import math


def calculate_metrics(result, benchmark_bars=None, periods_per_year=252):
    equity = [point.equity for point in result.equity_curve]
    returns = _returns(equity)
    initial_equity = result.config.initial_cash
    ending_equity = equity[-1] if equity else initial_equity
    total_return = _safe_div(ending_equity, initial_equity) - 1
    years = _safe_div(len(equity), periods_per_year)
    cagr = (ending_equity / initial_equity) ** (1 / years) - 1 if years > 0 and ending_equity > 0 else 0.0
    volatility = _std(returns) * math.sqrt(periods_per_year)
    mean_return = _mean(returns)
    sharpe = _safe_div(mean_return, _std(returns)) * math.sqrt(periods_per_year)
    downside = [value for value in returns if value < 0]
    sortino = _safe_div(mean_return, _std(downside)) * math.sqrt(periods_per_year)
    drawdowns = _drawdowns(equity)
    max_drawdown = min(drawdowns) if drawdowns else 0.0
    calmar = _safe_div(cagr, abs(max_drawdown)) if max_drawdown < 0 else 0.0
    sell_pnls = [fill.realized_pnl for fill in result.fills if fill.side == "SELL"]
    wins = [pnl for pnl in sell_pnls if pnl > 0]
    losses = [pnl for pnl in sell_pnls if pnl < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    avg_equity = _mean(equity) if equity else initial_equity
    turnover = _safe_div(sum(abs(fill.value) for fill in result.fills), avg_equity)
    exposure = _safe_div(
        sum(1 for point in result.equity_curve if point.position_value > 0),
        len(result.equity_curve),
    )

    return {
        "initial_equity": initial_equity,
        "ending_equity": ending_equity,
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_drawdown,
        "calmar": calmar,
        "win_rate": _safe_div(len(wins), len(sell_pnls)),
        "profit_factor": _safe_div(gross_profit, gross_loss),
        "average_win": _mean(wins),
        "average_loss": _mean(losses),
        "number_of_trades": len(result.fills),
        "exposure": exposure,
        "turnover": turnover,
        "rejected_signals": len(result.rejected_signals),
        "benchmark_return": _benchmark_return(benchmark_bars),
    }


def equity_drawdowns(equity_curve):
    equity = [point.equity for point in equity_curve]
    return [
        {"date": point.date, "drawdown": drawdown}
        for point, drawdown in zip(equity_curve, _drawdowns(equity))
    ]


def _returns(equity):
    return [
        (equity[index] / equity[index - 1]) - 1
        for index in range(1, len(equity))
        if equity[index - 1] != 0
    ]


def _drawdowns(equity):
    drawdowns = []
    peak = None
    for value in equity:
        peak = value if peak is None else max(peak, value)
        drawdowns.append((value / peak) - 1 if peak else 0.0)
    return drawdowns


def _benchmark_return(benchmark_bars):
    if not benchmark_bars:
        return 0.0
    first = benchmark_bars[0].close
    last = benchmark_bars[-1].close
    return _safe_div(last, first) - 1


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _std(values):
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0
