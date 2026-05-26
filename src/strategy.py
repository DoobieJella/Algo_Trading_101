from abc import ABC, abstractmethod
import logging

from models import Signal

logger = logging.getLogger(__name__)

class Strategy(ABC):
    def __init__(self, broker, symbol):
        self.broker = broker
        self.api = broker
        self.symbol = symbol
        self.name = self.__class__.__name__

    @abstractmethod
    def on_market_data(self, data):
        """
        Called when new market data is received.
        :param data: Dictionary containing 'price', 'volume', etc.
        """
        pass

    def execute_buy(self, context="", price=None):
        logger.info(f"[{self.name}] BUY Signal for {self.symbol} ({context})")
        return Signal(self.symbol, "BUY", quantity=1, price=price, reason=context)

    def execute_sell(self, context="", price=None):
        logger.info(f"[{self.name}] SELL Signal for {self.symbol} ({context})")
        return Signal(self.symbol, "SELL", quantity=1, price=price, reason=context)
