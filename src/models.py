from dataclasses import dataclass
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}


@dataclass(frozen=True)
class MarketData:
    symbol: str
    price: float
    timestamp: Optional[float] = None
    volume: Optional[float] = None

    @classmethod
    def from_dict(cls, data, default_symbol=None):
        price = data.get("price")
        symbol = data.get("symbol", default_symbol)
        if symbol is None:
            raise ValueError("Market data requires a symbol")
        if price is None:
            raise ValueError("Market data requires a price")

        return cls(
            symbol=symbol,
            price=float(price),
            timestamp=data.get("timestamp"),
            volume=data.get("volume"),
        )


@dataclass(frozen=True)
class DailyBar:
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trading_value: Optional[float] = None
    source: str = ""
    adjusted: bool = True

    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol=str(data["symbol"]),
            date=str(data["date"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=int(float(data["volume"])),
            trading_value=_optional_float(data.get("trading_value")),
            source=str(data.get("source", "")),
            adjusted=_coerce_bool(data.get("adjusted", True)),
        )

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trading_value": self.trading_value,
            "source": self.source,
            "adjusted": self.adjusted,
        }


@dataclass(frozen=True)
class MinuteBar:
    symbol: str
    date: str
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trading_value: Optional[float] = None
    source: str = ""

    @classmethod
    def from_dict(cls, data):
        return cls(
            symbol=str(data["symbol"]),
            date=str(data["date"]),
            time=str(data["time"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=int(float(data["volume"])),
            trading_value=_optional_float(data.get("trading_value")),
            source=str(data.get("source", "")),
        )

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "date": self.date,
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trading_value": self.trading_value,
            "source": self.source,
        }


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: str
    quantity: int = 1
    price: Optional[float] = None
    reason: str = ""

    def __post_init__(self):
        side = self.side.upper()
        if side not in VALID_SIDES:
            raise ValueError(f"Unsupported signal side: {self.side}")
        if self.quantity <= 0:
            raise ValueError("Signal quantity must be positive")
        object.__setattr__(self, "side", side)


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: int
    price: float
    reason: str = ""

    def __post_init__(self):
        side = self.side.upper()
        if side not in VALID_SIDES:
            raise ValueError(f"Unsupported order side: {self.side}")
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.price <= 0:
            raise ValueError("Order price must be positive")
        object.__setattr__(self, "side", side)


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    status: str
    message: str = ""


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    average_price: float = 0.0


def _optional_float(value):
    if value in (None, ""):
        return None
    return float(value)


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
