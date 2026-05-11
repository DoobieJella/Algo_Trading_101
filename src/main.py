import os
import time
import logging
from broker import create_broker
from config import AppConfig
from strategies.quant_strategy import QuantStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_strategies(broker):
    return [
        QuantStrategy(broker, "005930"),
    ]


def run_strategy_loop(broker, strategies, poll_interval_seconds=2, max_ticks=None):
    ticks = 0
    while max_ticks is None or ticks < max_ticks:
        for strategy in strategies:
            current_price = broker.get_current_price(strategy.symbol)
            market_data = {
                'symbol': strategy.symbol,
                'price': current_price,
                'timestamp': time.time()
            }

            signal = strategy.on_market_data(market_data)
            if signal:
                result = broker.execute_signal(signal)
                logger.info(
                    "Order result: %s %s %s x %s @ %s",
                    result.status,
                    result.side,
                    result.symbol,
                    result.quantity,
                    result.price,
                )

        ticks += 1
        time.sleep(poll_interval_seconds)


def main():
    logger.info("Starting Auto Trading Bot...")

    try:
        config = AppConfig.from_env()
        config.validate()
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return

    logger.info(f"Running in {config.trading_mode} mode")

    broker = create_broker(config)
    if not broker.authenticate():
        logger.error("Authentication failed. Exiting.")
        return

    if config.trading_mode == "REAL":
        logger.error("REAL strategy execution is disabled until risk controls are implemented.")
        return

    strategies = build_strategies(broker)
    logger.info(f"Initialized {len(strategies)} strategies. Starting event loop...")

    poll_interval_seconds = float(os.getenv("BOT_POLL_INTERVAL_SECONDS", "2"))
    max_ticks_value = os.getenv("BOT_MAX_TICKS")
    max_ticks = int(max_ticks_value) if max_ticks_value else None

    try:
        run_strategy_loop(broker, strategies, poll_interval_seconds, max_ticks)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
