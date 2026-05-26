from dataclasses import dataclass


BUY = "BUY"
SELL = "SELL"


@dataclass(frozen=True)
class ExecutionConfig:
    initial_cash: float = 10_000_000
    commission_rate: float = 0.0
    tax_rate: float = 0.0
    slippage_bps: float = 0.0
    impact_bps_per_participation: float = 1.0
    leftover_penalty_bps: float = 25.0
    risk_penalty_bps: float = 0.0


@dataclass(frozen=True)
class ExecutionFill:
    date: str
    time: str
    symbol: str
    side: str
    quantity: int
    price: float
    value: float
    shortfall: float
    shortfall_bps: float
    participation: float


def choose_child_quantity(action, remaining_quantity, force_complete=False):
    if remaining_quantity <= 0:
        return 0
    if force_complete:
        return remaining_quantity
    fraction = min(1.0, max(0.0, float(action)))
    quantity = int(remaining_quantity * fraction)
    if fraction > 0 and quantity == 0:
        quantity = 1
    return min(quantity, remaining_quantity)


def execute_child_order(bar, side, quantity, arrival_price, parent_quantity, config):
    if quantity <= 0:
        return None

    participation = quantity / max(1, bar.volume)
    bps = config.slippage_bps + (participation * config.impact_bps_per_participation)
    if side == BUY:
        price = bar.close * (1 + bps / 10000)
        shortfall = (price - arrival_price) * quantity
        tax = 0.0
    else:
        price = bar.close * (1 - bps / 10000)
        shortfall = (arrival_price - price) * quantity
        tax = price * quantity * config.tax_rate

    value = price * quantity
    commission = value * config.commission_rate
    total_shortfall = shortfall + commission + tax
    shortfall_bps = total_shortfall / max(arrival_price * parent_quantity, 1) * 10000
    return ExecutionFill(
        date=bar.date,
        time=bar.time,
        symbol=bar.symbol,
        side=side,
        quantity=quantity,
        price=price,
        value=value,
        shortfall=total_shortfall,
        shortfall_bps=shortfall_bps,
        participation=participation,
    )


def reward_from_fill(fill, remaining_fraction, config):
    reward = 0.0
    if fill is not None:
        reward -= fill.shortfall_bps
    reward -= remaining_fraction * config.risk_penalty_bps
    return reward


def leftover_penalty(remaining_quantity, parent_quantity, config):
    return (remaining_quantity / max(parent_quantity, 1)) * config.leftover_penalty_bps
