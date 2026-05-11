from strategy import Strategy
import logging

logger = logging.getLogger(__name__)

class ArbitrageStrategy(Strategy):
    """
    Arbitrage Strategy: Checks spread between the primary symbol and a secondary correlated symbol.
    Example: KOSPI 200 ETF (Spot) vs Futures (conceptual).
    """
    def __init__(self, api, symbol, target_symbol, threshold=0.5):
        super().__init__(api, symbol)
        self.target_symbol = target_symbol
        self.threshold = threshold # Percent spread to trigger

    def on_market_data(self, data):
        # We need the price of the target symbol too
        # In a real event loop, we might need a shared data store or query the API specifically
        
        price_a = data.get('price')
        price_b = self.api.get_current_price(self.target_symbol)
        
        if not price_a or not price_b:
            return

        spread = (price_a - price_b) / price_b * 100
        
        logger.info(f"[{self.name}] Spread between {self.symbol} and {self.target_symbol}: {spread:.2f}%")

        if spread > self.threshold:
            logger.info("Spread high: Sell A, Buy B")
            # Logic to Buy B would go here
            return self.execute_sell(f"Spread {spread:.2f}% > {self.threshold}%", price_a)
            
        elif spread < -self.threshold:
            logger.info("Spread low: Buy A, Sell B")
            return self.execute_buy(f"Spread {spread:.2f}% < -{self.threshold}%", price_a)
        return None
