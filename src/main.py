import os
import time
import logging
from dotenv import load_dotenv
from kis_api import KisApi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    logger.info("Starting Auto Trading Bot...")
    
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    account_no = os.getenv("KIS_ACCOUNT_NO")
    mode = os.getenv("TRADING_MODE", "MOCK")
    
    logger.info(f"Running in {mode} mode")
    
    # Initialize API Wrapper
    api = KisApi(app_key, app_secret, account_no, mode=mode)
    
    # Authenticate (or Mock Auth)
    if not api.auth():
        logger.error("Authentication failed. Exiting.")
        return

    logger.info("Authentication successful. Initializing Strategies...")

    # Initialize Strategies
    strategies = []
    
    # # 1. Quant Strategy (Samsung Electronics)
    # from strategies.quant_strategy import QuantStrategy
    # strategies.append(QuantStrategy(api, "005930")) # Samsung

    # # 2. Arbitrage Strategy (KODEX 200 vs KOSPI Futures - Mock symbols)
    # from strategies.arbitrage_strategy import ArbitrageStrategy
    # strategies.append(ArbitrageStrategy(api, "069500", "101000")) 

    # # 3. HFT Scalper (SK Hynix)
    # from strategies.hft_scalper import HFTStrategy
    # strategies.append(HFTStrategy(api, "000660"))

    # # 4. Fundamental (Kakao)
    # from strategies.fundamental_long_short import FundamentalStrategy
    # strategies.append(FundamentalStrategy(api, "035720"))

    # logger.info(f"Initialized {len(strategies)} strategies. Starting event loop...")
    
    # try:
    #     while True:
    #         # Main Event Loop
    #         # In a real WebSocket scenario, this would be callback-driven.
    #         # Here in specific loop, we poll/simulate ticks.

    #         for strategy in strategies:
    #             # Simulate getting a "tick" for the strategy's symbol
    #             current_price = api.get_current_price(strategy.symbol)
                
    #             # Create a data packet
    #             market_data = {
    #                 'symbol': strategy.symbol,
    #                 'price': current_price,
    #                 'timestamp': time.time()
    #             }

    #             # Feed data to strategy
    #             strategy.on_market_data(market_data)
            
    #         time.sleep(2) # Tick every 2 seconds for demo
            
    # except KeyboardInterrupt:
    #     logger.info("Bot stopped by user.")
    # except Exception as e:
        # logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
