from rl_execution.simulator import ExecutionConfig, execute_child_order


def twap_schedule(parent_quantity, horizon):
    base = parent_quantity // horizon
    remainder = parent_quantity % horizon
    return [base + (1 if index < remainder else 0) for index in range(horizon)]


def vwap_schedule(parent_quantity, bars):
    total_volume = sum(bar.volume for bar in bars)
    if total_volume <= 0:
        return twap_schedule(parent_quantity, len(bars))

    schedule = []
    allocated = 0
    for bar in bars:
        quantity = int(parent_quantity * (bar.volume / total_volume))
        schedule.append(quantity)
        allocated += quantity
    schedule[-1] += parent_quantity - allocated
    return schedule


def evaluate_schedule(name, bars, side, parent_quantity, quantities, config=None):
    config = config or ExecutionConfig()
    arrival_price = bars[0].close
    fills = []
    remaining = parent_quantity
    for bar, quantity in zip(bars, quantities):
        quantity = min(quantity, remaining)
        fill = execute_child_order(bar, side, quantity, arrival_price, parent_quantity, config)
        if fill is not None:
            fills.append(fill)
            remaining -= quantity
        if remaining <= 0:
            break

    total_shortfall = sum(fill.shortfall for fill in fills)
    return {
        "policy": name,
        "symbol": bars[0].symbol,
        "date": bars[0].date,
        "side": side,
        "parent_quantity": parent_quantity,
        "executed_quantity": parent_quantity - remaining,
        "remaining_quantity": remaining,
        "shortfall": total_shortfall,
        "shortfall_bps": total_shortfall / max(arrival_price * parent_quantity, 1) * 10000,
        "fills": fills,
    }


def evaluate_twap(bars, side, parent_quantity, config=None):
    return evaluate_schedule(
        "TWAP",
        bars,
        side,
        parent_quantity,
        twap_schedule(parent_quantity, len(bars)),
        config=config,
    )


def evaluate_vwap(bars, side, parent_quantity, config=None):
    return evaluate_schedule(
        "VWAP",
        bars,
        side,
        parent_quantity,
        vwap_schedule(parent_quantity, bars),
        config=config,
    )
