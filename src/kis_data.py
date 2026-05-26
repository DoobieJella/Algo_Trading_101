import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from models import DailyBar


DAILY_FIELD_MAPPING = {
    "date": "stck_bsop_date",
    "open": "stck_oprc",
    "high": "stck_hgpr",
    "low": "stck_lwpr",
    "close": "stck_clpr",
    "volume": "acml_vol",
    "trading_value": "acml_tr_pbmn",
}

DAILY_COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trading_value",
    "source",
    "adjusted",
]


def normalize_daily_bars(symbol, payload, source="KIS", adjusted=True):
    rows = payload.get("output2")
    if rows is None:
        rows = payload.get("output", [])
    if isinstance(rows, dict):
        rows = [rows]

    bars = []
    for row in rows:
        if not row.get("stck_bsop_date"):
            continue
        bars.append(
            DailyBar(
                symbol=symbol,
                date=_normalize_date(row["stck_bsop_date"]),
                open=_to_float(row.get("stck_oprc")),
                high=_to_float(row.get("stck_hgpr")),
                low=_to_float(row.get("stck_lwpr")),
                close=_to_float(row.get("stck_clpr")),
                volume=int(_to_float(row.get("acml_vol"))),
                trading_value=_to_optional_float(row.get("acml_tr_pbmn")),
                source=source,
                adjusted=adjusted,
            )
        )
    return sorted(bars, key=lambda bar: bar.date)


def write_daily_bars(symbol, bars, output_root=Path("data/kis/domestic_stock/daily"), metadata=None):
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    csv_path = output_root / f"{symbol}.csv"
    metadata_path = output_root / f"{symbol}.metadata.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DAILY_COLUMNS)
        writer.writeheader()
        for bar in bars:
            writer.writerow(bar.to_dict())

    metadata_payload = {
        "symbol": symbol,
        "row_count": len(bars),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "field_mapping": DAILY_FIELD_MAPPING,
    }
    if metadata:
        metadata_payload.update(metadata)

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata_payload, file, ensure_ascii=False, indent=2)

    return csv_path, metadata_path


def read_daily_bars(csv_path):
    csv_path = Path(csv_path)
    with csv_path.open("r", newline="", encoding="utf-8") as file:
        return [DailyBar.from_dict(row) for row in csv.DictReader(file)]


def fetch_and_store_daily_bars(
    api,
    symbol,
    start_date,
    end_date,
    output_root=Path("data/kis/domestic_stock/daily"),
    market_code="J",
    adjusted=True,
):
    payload = api.get_domestic_daily_itemchartprice(
        symbol,
        start_date=start_date,
        end_date=end_date,
        market_code=market_code,
        period="D",
        adjusted=adjusted,
    )
    bars = normalize_daily_bars(symbol, payload, adjusted=adjusted)
    metadata = {
        "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        "tr_id": "FHKST03010100",
        "market_code": market_code,
        "start_date": start_date,
        "end_date": end_date,
        "adjusted": adjusted,
        "source": "KIS",
    }
    return write_daily_bars(symbol, bars, output_root=output_root, metadata=metadata)


def _normalize_date(value):
    value = str(value)
    if "-" in value:
        return value
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"


def _to_float(value):
    if value in (None, ""):
        return 0.0
    return float(str(value).replace(",", ""))


def _to_optional_float(value):
    if value in (None, ""):
        return None
    return _to_float(value)
