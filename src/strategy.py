from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class Strategy(ABC):
    def __init__(self, api, symbol):
        self.api = api
        self.symbol = symbol
        self.name = self.__class__.__name__

    @abstractmethod
    def on_market_data(self, data):
        """
        Called when new market data is received.
        :param data: Dictionary containing 'price', 'volume', etc.
        """
        pass

    def execute_buy(self, context=""):
        logger.info(f"[{self.name}] BUY Signal for {self.symbol} ({context})")
        # Logic to calculate quantity based on balance (simplified)
        qty = 1 
        price = self.api.get_current_price(self.symbol)
        if price:
            self.api.place_order(self.symbol, qty, price, "BUY")

    def execute_sell(self, context=""):
        logger.info(f"[{self.name}] SELL Signal for {self.symbol} ({context})")
        # Logic to calculate quantity to sell
        qty = 1
        price = self.api.get_current_price(self.symbol)
        if price:
            self.api.place_order(self.symbol, qty, price, "SELL")
