import argparse
from pathlib import Path

from config import AppConfig
from kis_api import KisApi
from rl_execution.data import fetch_and_store_minute_bars


def main():
    parser = argparse.ArgumentParser(description="Download and normalize KIS domestic minute bars.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--input-hour", default="153000")
    parser.add_argument("--market-code", default="J")
    parser.add_argument("--output-root", default="data/kis/domestic_stock/minute")
    args = parser.parse_args()

    config = AppConfig.from_env()
    config.validate()
    config.validate_kis_data_access()
    api = KisApi(
        config.kis_app_key,
        config.kis_app_secret,
        config.kis_account_no,
        mode=config.kis_api_env,
    )
    csv_path, metadata_path = fetch_and_store_minute_bars(
        api,
        args.symbol,
        args.date,
        output_root=Path(args.output_root),
        market_code=args.market_code,
        input_hour=args.input_hour,
    )
    print(f"Saved minute bars: {csv_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()
