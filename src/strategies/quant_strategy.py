from strategy import Strategy
import logging

logger = logging.getLogger(__name__)

class QuantStrategy(Strategy):
    """
    A simple Quantitative Strategy using Moving Average Crossover.
    """
    def __init__(self, api, symbol, short_window=5, long_window=20):
        super().__init__(api, symbol)
        self.short_window = short_window
        self.long_window = long_window
        self.prices = []

    def on_market_data(self, data):
        price = data.get('price')
        if price is None:
            return

        self.prices.append(price)
        if len(self.prices) > self.long_window:
            self.prices.pop(0)

        if len(self.prices) < self.long_window:
            return

        # Simple SMA calculation
        short_ma = sum(self.prices[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices) / self.long_window
        
        logger.debug(f"[{self.name}] SMA{self.short_window}: {short_ma}, SMA{self.long_window}: {long_ma}")

        # Basic Crossover Logic
        # Note: In a real system, you'd check if it JUST crossed over this tick to avoid repeated signals
        if short_ma > long_ma:
             # Example condition: simple signal if short MA is above long MA
             # In production, use state to trigger only on the crossover moment
             pass 
        elif short_ma < long_ma:
             pass
