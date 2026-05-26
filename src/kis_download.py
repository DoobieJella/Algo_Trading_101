import argparse
from pathlib import Path

from config import AppConfig
from kis_api import KisApi
from kis_data import fetch_and_store_daily_bars


def main():
    parser = argparse.ArgumentParser(description="Download and normalize KIS domestic daily bars.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--market-code", default="J")
    parser.add_argument("--output-root", default="data/kis/domestic_stock/daily")
    parser.add_argument("--original-price", action="store_true")
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
    csv_path, metadata_path = fetch_and_store_daily_bars(
        api,
        args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        output_root=Path(args.output_root),
        market_code=args.market_code,
        adjusted=not args.original_price,
    )
    print(f"Saved daily bars: {csv_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()
