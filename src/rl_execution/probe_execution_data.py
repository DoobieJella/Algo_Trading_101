import argparse
from pathlib import Path

from config import AppConfig
from kis_api import KisApi
from kis_catalog import domestic_stock_data_endpoints, find_endpoint, load_kis_endpoint_catalog
from kis_probe import _probe_endpoint


EXECUTION_ENDPOINT_NAMES = [
    "주식당일분봉조회",
    "주식현재가 호가/예상체결",
    "주식현재가 체결",
    "주식현재가 당일시간대별체결",
]


def probe_execution_data(api, symbols, catalog_path=Path("KIS/KIS_open_API.xlsx")):
    endpoints = domestic_stock_data_endpoints(load_kis_endpoint_catalog(catalog_path))
    results = []
    for name in EXECUTION_ENDPOINT_NAMES:
        endpoint = find_endpoint(endpoints, name)
        for symbol in symbols:
            results.append(
                _probe_endpoint(
                    api,
                    endpoint.api_name,
                    endpoint.path,
                    endpoint.tr_id_mock or endpoint.tr_id_real,
                    symbol,
                    params=_params(endpoint.api_name, symbol),
                )
            )
    return results


def _params(api_name, symbol):
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
    }
    if api_name == "주식당일분봉조회":
        params.update(
            {
                "FID_ETC_CLS_CODE": "",
                "FID_INPUT_HOUR_1": "153000",
                "FID_PW_DATA_INCU_YN": "N",
            }
        )
    return params


def main():
    parser = argparse.ArgumentParser(description="Probe KIS endpoints needed for PPO order execution research.")
    parser.add_argument("--symbols", nargs="+", default=["005930", "000660"])
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
    results = probe_execution_data(api, args.symbols)
    supported = sum(1 for result in results if result.status == "SUPPORTED")
    for result in results:
        print(f"{result.symbol} {result.api_name}: {result.status} rows={result.row_count} error={result.error}")
    print(f"Execution data probe complete: {supported}/{len(results)} supported")


if __name__ == "__main__":
    main()
