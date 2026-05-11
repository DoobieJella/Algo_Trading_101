from strategy import Strategy
import logging

logger = logging.getLogger(__name__)

class HFTStrategy(Strategy):
    """
    High Frequency Scalper (Simulated).
    Focuses on small price deviations and quick turnover.
    """
    def __init__(self, api, symbol, tick_size=100):
        super().__init__(api, symbol)
        self.tick_size = tick_size
        self.last_price = None

    def on_market_data(self, data):
        current_price = data.get('price')
        if not current_price:
            return

        if self.last_price:
            # Simple Mean Reversion / Scalp logic
            # If price dropped by tick_size, Buy (expect rebound)
            if current_price <= self.last_price - self.tick_size:
                logger.info(f"[{self.name}] Price Drop Detected. Scalp Buy.")
                signal = self.execute_buy("Dip Scalp", current_price)
                self.last_price = current_price
                return signal
            
            # If price rose by tick_size, Sell
            elif current_price >= self.last_price + self.tick_size:
                logger.info(f"[{self.name}] Price Jump Detected. Scalp Sell.")
                signal = self.execute_sell("Peak Scalp", current_price)
                self.last_price = current_price
                return signal

        self.last_price = current_price
        return None
