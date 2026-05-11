from strategy import Strategy
import logging

logger = logging.getLogger(__name__)

class FundamentalStrategy(Strategy):
    """
    Fundamental Strategy: Long/Short based on Valuation metrics.
    Note: Real-time PBR/PER might not be in the WebSocket tick stream, usually queried daily.
    """
    def __init__(self, api, symbol, max_per=10):
        super().__init__(api, symbol)
        self.max_per = max_per
        self.checked_today = False

    def on_market_data(self, data):
        # Only check once per day/session
        if self.checked_today:
            return

        # Fetch Fundamental Data (Mocked here, as KIS API 'current price' info usually includes some stats or requires separate call)
        # In a real app, you'd call a specific endpoint for 'stock-info'
        current_per = self._get_fake_per() 
        
        logger.info(f"[{self.name}] Analyzed PER: {current_per}")

        if current_per < self.max_per:
            logger.info(f"Undervalued (PER {current_per} < {self.max_per}). signals BUY.")
            signal = self.execute_buy("Fundamental Undervalued", data.get('price'))
            self.checked_today = True
            return signal
        
        self.checked_today = True
        return None

    def _get_fake_per(self):
        # Simulate a PER lookup
        return 8.5
