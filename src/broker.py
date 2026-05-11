import logging
from abc import ABC, abstractmethod

from kis_api import KisApi
from models import OrderRequest, OrderResult


logger = logging.getLogger(__name__)


class Broker(ABC):
    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def get_current_price(self, symbol):
        pass

    @abstractmethod
    def place_order(self, order):
        pass

    def execute_signal(self, signal):
        price = signal.price
        if price is None:
            price = self.get_current_price(signal.symbol)
        if price is None:
            return OrderResult(
                order_id="",
                symbol=signal.symbol,
                side=signal.side,
                quantity=signal.quantity,
                price=0,
                status="REJECTED",
                message="No price available for signal",
            )

        order = OrderRequest(
            symbol=signal.symbol,
            side=signal.side,
            quantity=signal.quantity,
            price=price,
            reason=signal.reason,
        )
        return self.place_order(order)


class MockBroker(Broker):
    def __init__(self, prices=None):
        self.prices = prices or {}
        self.orders = []
        self.order_results = []

    def authenticate(self):
        logger.info("[MOCK] Authentication successful")
        return True

    def get_current_price(self, symbol):
        price = self.prices.get(symbol)
        if isinstance(price, list):
            if not price:
                return None
            if len(price) == 1:
                return price[0]
            return price.pop(0)
        if price is not None:
            return price
        return 70000

    def place_order(self, order):
        self.orders.append(order)
        result = OrderResult(
            order_id=f"MOCK-{len(self.orders)}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status="FILLED",
            message="Mock fill",
        )
        self.order_results.append(result)
        logger.info(
            "[MOCK] Filled %s order: %s x %s @ %s",
            order.side,
            order.symbol,
            order.quantity,
            order.price,
        )
        return result


class KisBroker(Broker):
    def __init__(self, api):
        self.api = api

    def authenticate(self):
        return self.api.auth()

    def get_current_price(self, symbol):
        return self.api.get_current_price(symbol)

    def place_order(self, order):
        success = self.api.place_order(
            order.symbol,
            order.quantity,
            order.price,
            order.side,
        )
        status = "ACCEPTED" if success else "REJECTED"
        return OrderResult(
            order_id="",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status=status,
            message="KIS order submitted" if success else "KIS order rejected",
        )


def create_broker(config):
    if config.trading_mode == "MOCK":
        return MockBroker()

    api = KisApi(
        config.kis_app_key,
        config.kis_app_secret,
        config.kis_account_no,
        mode=config.trading_mode,
    )
    return KisBroker(api)
