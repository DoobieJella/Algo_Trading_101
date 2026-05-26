import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from config import AppConfig
from kis_api import KisApi
from kis_catalog import (
    domestic_stock_data_endpoints,
    find_endpoint,
    load_kis_endpoint_catalog,
)


PROBE_ENDPOINT_NAMES = [
    "주식현재가 시세",
    "주식현재가 일자별",
    "국내주식기간별시세(일/주/월/년)",
]


@dataclass(frozen=True)
class ProbeResult:
    api_name: str
    path: str
    tr_id: str
    symbol: str
    status: str
    rt_cd: str = ""
    msg_cd: str = ""
    row_count: int = 0
    response_keys: str = ""
    error: str = ""


def run_kis_data_probe(
    api,
    catalog_path=Path("KIS/KIS_open_API.xlsx"),
    output_dir=Path("reports/kis_probe"),
    symbols=("005930", "000660"),
    start_date=None,
    end_date=None,
    market_code="J",
):
    start_date, end_date = _default_dates(start_date, end_date)
    endpoints = domestic_stock_data_endpoints(load_kis_endpoint_catalog(catalog_path))
    selected = [find_endpoint(endpoints, name) for name in PROBE_ENDPOINT_NAMES]

    run_dir = Path(output_dir) / _run_id()
    run_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for endpoint in selected:
        tr_id = endpoint.tr_id_mock or endpoint.tr_id_real
        for symbol in symbols:
            results.append(
                _probe_endpoint(
                    api,
                    endpoint.api_name,
                    endpoint.path,
                    tr_id,
                    symbol,
                    params=_params_for_endpoint(
                        endpoint.api_name,
                        symbol,
                        start_date,
                        end_date,
                        market_code,
                    ),
                )
            )

    _write_probe_outputs(run_dir, results)
    return results, run_dir


def _probe_endpoint(api, api_name, path, tr_id, symbol, params):
    try:
        payload = api.request("GET", path, tr_id=tr_id, params=params)
        rt_cd = str(payload.get("rt_cd", ""))
        return ProbeResult(
            api_name=api_name,
            path=path,
            tr_id=tr_id,
            symbol=symbol,
            status="SUPPORTED" if rt_cd == "0" else "ERROR",
            rt_cd=rt_cd,
            msg_cd=str(payload.get("msg_cd", "")),
            row_count=_row_count(payload),
            response_keys=",".join(sorted(payload.keys())),
            error="" if rt_cd == "0" else str(payload.get("msg1", "")),
        )
    except Exception as error:
        return ProbeResult(
            api_name=api_name,
            path=path,
            tr_id=tr_id,
            symbol=symbol,
            status="ERROR",
            error=str(error),
        )


def _params_for_endpoint(api_name, symbol, start_date, end_date, market_code):
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": symbol,
    }
    if api_name == "주식현재가 일자별":
        params.update(
            {
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            }
        )
    elif api_name == "국내주식기간별시세(일/주/월/년)":
        params.update(
            {
                "FID_INPUT_DATE_1": start_date.replace("-", ""),
                "FID_INPUT_DATE_2": end_date.replace("-", ""),
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            }
        )
    return params


def _row_count(payload):
    total = 0
    for key in ("output", "output1", "output2"):
        value = payload.get(key)
        if isinstance(value, list):
            total += len(value)
        elif isinstance(value, dict) and value:
            total += 1
    return total


def _write_probe_outputs(run_dir, results):
    csv_path = run_dir / "availability.csv"
    json_path = run_dir / "availability.json"
    rows = [asdict(result) for result in results]

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)


def _default_dates(start_date, end_date):
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = (date.fromisoformat(end_date) - timedelta(days=30)).isoformat()
    return start_date, end_date


def _run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    parser = argparse.ArgumentParser(description="Probe read-only KIS domestic stock data endpoints.")
    parser.add_argument("--symbols", nargs="+", default=["005930", "000660"])
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--output-dir", default="reports/kis_probe")
    parser.add_argument("--catalog-path", default="KIS/KIS_open_API.xlsx")
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
    results, run_dir = run_kis_data_probe(
        api,
        catalog_path=Path(args.catalog_path),
        output_dir=Path(args.output_dir),
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    supported = sum(1 for result in results if result.status == "SUPPORTED")
    print(f"KIS probe complete: {supported}/{len(results)} supported. Output: {run_dir}")


if __name__ == "__main__":
    main()
