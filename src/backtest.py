from dataclasses import dataclass

from broker import MockBroker
from models import DailyBar, MarketData, OrderResult, Signal


@dataclass(frozen=True)
class BacktestResult:
    ticks: int
    signals: list[Signal]
    orders: list[OrderResult]


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 10_000_000
    commission_rate: float = 0.0
    tax_rate: float = 0.0
    slippage_bps: float = 0.0
    execution_policy: str = "next_open"


@dataclass(frozen=True)
class Fill:
    date: str
    symbol: str
    side: str
    quantity: int
    price: float
    value: float
    commission: float
    tax: float
    realized_pnl: float
    cash_after: float
    reason: str = ""


@dataclass(frozen=True)
class RejectedSignal:
    date: str
    symbol: str
    side: str
    quantity: int
    reason: str


@dataclass(frozen=True)
class EquityPoint:
    date: str
    cash: float
    position_value: float
    equity: float


@dataclass(frozen=True)
class DailyBacktestResult:
    config: BacktestConfig
    fills: list[Fill]
    rejected_signals: list[RejectedSignal]
    equity_curve: list[EquityPoint]
    ending_cash: float
    positions: dict


def run_backtest(strategy, market_data):
    broker = strategy.broker
    if not isinstance(broker, MockBroker):
        raise ValueError("Backtests require MockBroker to avoid live order placement")

    signals = []
    orders = []
    ticks = 0

    for row in market_data:
        tick = _coerce_market_data(row, strategy.symbol)
        _set_mock_price(broker, tick.symbol, tick.price)

        signal = strategy.on_market_data(_to_strategy_data(tick))
        ticks += 1
        if signal is None:
            continue

        signals.append(signal)
        orders.append(broker.execute_signal(signal))

    return BacktestResult(ticks=ticks, signals=signals, orders=orders)


def run_daily_backtest(strategy, bars, config=None):
    config = config or BacktestConfig()
    if config.execution_policy != "next_open":
        raise ValueError("Only next_open execution is supported")
    if not isinstance(strategy.broker, MockBroker):
        raise ValueError("Backtests require MockBroker to avoid live order placement")

    daily_bars = sorted((_coerce_daily_bar(row) for row in bars), key=lambda bar: (bar.date, bar.symbol))
    bars_by_date = _group_bars_by_date(daily_bars)

    cash = float(config.initial_cash)
    positions = {}
    fills = []
    rejected_signals = []
    equity_curve = []
    pending_signals = []
    last_prices = {}

    for current_date, day_bars in bars_by_date.items():
        bars_by_symbol = {bar.symbol: bar for bar in day_bars}

        for bar in day_bars:
            strategy.broker.prices[bar.symbol] = bar.open

        for signal in pending_signals:
            bar = bars_by_symbol.get(signal.symbol)
            if bar is None:
                rejected_signals.append(
                    RejectedSignal(current_date, signal.symbol, signal.side, signal.quantity, "No next bar available")
                )
                continue
            cash, fill, rejection = _execute_signal(signal, bar.open, current_date, cash, positions, config)
            if fill:
                fills.append(fill)
            if rejection:
                rejected_signals.append(rejection)

        pending_signals = []

        for bar in day_bars:
            strategy.broker.prices[bar.symbol] = bar.close
            last_prices[bar.symbol] = bar.close

        primary_bar = bars_by_symbol.get(strategy.symbol)
        if primary_bar is not None:
            signal = strategy.on_market_data(_daily_market_data(primary_bar, bars_by_symbol))
            if signal is not None:
                pending_signals.append(signal)

        position_value = _position_value(positions, last_prices)
        equity_curve.append(
            EquityPoint(
                date=current_date,
                cash=cash,
                position_value=position_value,
                equity=cash + position_value,
            )
        )

    for signal in pending_signals:
        rejected_signals.append(
            RejectedSignal(
                equity_curve[-1].date if equity_curve else "",
                signal.symbol,
                signal.side,
                signal.quantity,
                "No future bar available for next_open execution",
            )
        )

    return DailyBacktestResult(
        config=config,
        fills=fills,
        rejected_signals=rejected_signals,
        equity_curve=equity_curve,
        ending_cash=cash,
        positions=positions,
    )


def _coerce_market_data(row, default_symbol):
    if isinstance(row, MarketData):
        return row
    return MarketData.from_dict(row, default_symbol=default_symbol)


def _to_strategy_data(tick):
    return {
        "symbol": tick.symbol,
        "price": tick.price,
        "timestamp": tick.timestamp,
        "volume": tick.volume,
    }


def _set_mock_price(broker, symbol, price):
    broker.prices[symbol] = price


def _coerce_daily_bar(row):
    if isinstance(row, DailyBar):
        return row
    return DailyBar.from_dict(row)


def _group_bars_by_date(bars):
    grouped = {}
    for bar in bars:
        grouped.setdefault(bar.date, []).append(bar)
    return dict(sorted(grouped.items()))


def _daily_market_data(bar, bars_by_symbol):
    return {
        "symbol": bar.symbol,
        "date": bar.date,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "price": bar.close,
        "volume": bar.volume,
        "market": {
            symbol: {
                "open": day_bar.open,
                "high": day_bar.high,
                "low": day_bar.low,
                "close": day_bar.close,
                "price": day_bar.close,
                "volume": day_bar.volume,
            }
            for symbol, day_bar in bars_by_symbol.items()
        },
    }


def _execute_signal(signal, open_price, current_date, cash, positions, config):
    side = signal.side.upper()
    quantity = signal.quantity
    if quantity <= 0:
        return cash, None, RejectedSignal(current_date, signal.symbol, side, quantity, "Quantity must be positive")

    if side == "BUY":
        fill_price = open_price * (1 + config.slippage_bps / 10000)
        value = fill_price * quantity
        commission = value * config.commission_rate
        total_cost = value + commission
        if total_cost > cash:
            return cash, None, RejectedSignal(current_date, signal.symbol, side, quantity, "Insufficient cash")

        position = positions.setdefault(signal.symbol, {"quantity": 0, "average_price": 0.0})
        previous_quantity = position["quantity"]
        new_quantity = previous_quantity + quantity
        position["average_price"] = (
            (position["average_price"] * previous_quantity) + value
        ) / new_quantity
        position["quantity"] = new_quantity
        cash -= total_cost
        return cash, Fill(
            date=current_date,
            symbol=signal.symbol,
            side=side,
            quantity=quantity,
            price=fill_price,
            value=value,
            commission=commission,
            tax=0.0,
            realized_pnl=0.0,
            cash_after=cash,
            reason=signal.reason,
        ), None

    position = positions.get(signal.symbol)
    held_quantity = position["quantity"] if position else 0
    if quantity > held_quantity:
        return cash, None, RejectedSignal(current_date, signal.symbol, side, quantity, "Insufficient position")

    fill_price = open_price * (1 - config.slippage_bps / 10000)
    value = fill_price * quantity
    commission = value * config.commission_rate
    tax = value * config.tax_rate
    realized_pnl = (fill_price - position["average_price"]) * quantity - commission - tax
    cash += value - commission - tax
    position["quantity"] -= quantity
    if position["quantity"] == 0:
        position["average_price"] = 0.0

    return cash, Fill(
        date=current_date,
        symbol=signal.symbol,
        side=side,
        quantity=quantity,
        price=fill_price,
        value=value,
        commission=commission,
        tax=tax,
        realized_pnl=realized_pnl,
        cash_after=cash,
        reason=signal.reason,
    ), None


def _position_value(positions, last_prices):
    total = 0.0
    for symbol, position in positions.items():
        total += position["quantity"] * last_prices.get(symbol, position["average_price"])
    return total
