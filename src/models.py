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
