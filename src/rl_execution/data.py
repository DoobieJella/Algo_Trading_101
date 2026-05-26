import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from models import MinuteBar


MINUTE_COLUMNS = [
    "symbol",
    "date",
    "time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trading_value",
    "source",
]

MINUTE_FIELD_MAPPING = {
    "date": "stck_bsop_date",
    "time": "stck_cntg_hour",
    "open": "stck_oprc",
    "high": "stck_hgpr",
    "low": "stck_lwpr",
    "close": "stck_prpr",
    "volume": "cntg_vol",
    "trading_value": "acml_tr_pbmn",
}


@dataclass(frozen=True)
class DataSplit:
    train: list[list[MinuteBar]]
    validation: list[list[MinuteBar]]
    test: list[list[MinuteBar]]


def normalize_minute_bars(symbol, payload, trade_date=None, source="KIS"):
    rows = payload.get("output2")
    if rows is None:
        rows = payload.get("output", [])
    if isinstance(rows, dict):
        rows = [rows]

    bars = []
    for row in rows:
        time_value = row.get("stck_cntg_hour") or row.get("stck_bsop_hour")
        if not time_value:
            continue
        bars.append(
            MinuteBar(
                symbol=symbol,
                date=_normalize_date(row.get("stck_bsop_date") or trade_date),
                time=_normalize_time(time_value),
                open=_to_float(row.get("stck_oprc") or row.get("stck_prpr")),
                high=_to_float(row.get("stck_hgpr") or row.get("stck_prpr")),
                low=_to_float(row.get("stck_lwpr") or row.get("stck_prpr")),
                close=_to_float(row.get("stck_prpr") or row.get("stck_clpr")),
                volume=int(_to_float(row.get("cntg_vol") or row.get("acml_vol"))),
                trading_value=_to_optional_float(row.get("acml_tr_pbmn")),
                source=source,
            )
        )
    return sorted(bars, key=lambda bar: (bar.date, bar.time))


def write_minute_bars(symbol, trade_date, bars, output_root=Path("data/kis/domestic_stock/minute"), metadata=None):
    output_root = Path(output_root)
    output_dir = output_root / symbol
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{trade_date}.csv"
    metadata_path = output_dir / f"{trade_date}.metadata.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=MINUTE_COLUMNS)
        writer.writeheader()
        for bar in bars:
            writer.writerow(bar.to_dict())

    metadata_payload = {
        "symbol": symbol,
        "date": trade_date,
        "row_count": len(bars),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "field_mapping": MINUTE_FIELD_MAPPING,
    }
    if metadata:
        metadata_payload.update(metadata)

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata_payload, file, ensure_ascii=False, indent=2)

    return csv_path, metadata_path


def read_minute_bars(csv_path):
    with Path(csv_path).open("r", newline="", encoding="utf-8") as file:
        return [MinuteBar.from_dict(row) for row in csv.DictReader(file)]


def load_symbol_episodes(data_root, symbol, horizon_minutes=30):
    symbol_dir = Path(data_root) / symbol
    episodes = []
    for csv_path in sorted(symbol_dir.glob("*.csv")):
        bars = read_minute_bars(csv_path)
        if len(bars) >= horizon_minutes:
            episodes.append(bars[:horizon_minutes])
    return episodes


def split_episodes_by_date(episodes, train_ratio=0.7, validation_ratio=0.15):
    ordered = sorted(episodes, key=lambda episode: episode[0].date if episode else "")
    count = len(ordered)
    train_end = max(1, int(count * train_ratio)) if count else 0
    validation_end = max(train_end, int(count * (train_ratio + validation_ratio)))
    if count >= 3 and validation_end == train_end:
        validation_end += 1
    validation_end = min(validation_end, count)
    return DataSplit(
        train=ordered[:train_end],
        validation=ordered[train_end:validation_end],
        test=ordered[validation_end:],
    )


def fetch_and_store_minute_bars(
    api,
    symbol,
    trade_date,
    output_root=Path("data/kis/domestic_stock/minute"),
    market_code="J",
    input_hour="153000",
):
    payload = api.get_domestic_time_itemchartprice(
        symbol,
        input_hour=input_hour,
        market_code=market_code,
    )
    bars = normalize_minute_bars(symbol, payload, trade_date=trade_date)
    metadata = {
        "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
        "tr_id": "FHKST03010200",
        "market_code": market_code,
        "source": "KIS",
    }
    return write_minute_bars(symbol, trade_date, bars, output_root=output_root, metadata=metadata)


def make_synthetic_episode(symbol="005930", trade_date="2024-01-05", minutes=30, start_price=70000):
    bars = []
    for index in range(minutes):
        price = start_price + index * 10
        bars.append(
            MinuteBar(
                symbol=symbol,
                date=trade_date,
                time=f"09:{30 + index:02d}:00",
                open=price - 5,
                high=price + 20,
                low=price - 20,
                close=price,
                volume=1000 + index * 5,
                trading_value=price * (1000 + index * 5),
                source="synthetic",
            )
        )
    return bars


def _normalize_date(value):
    if value is None:
        raise ValueError("Minute bar requires a date")
    value = str(value)
    if "-" in value:
        return value
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"


def _normalize_time(value):
    value = str(value)
    if ":" in value:
        return value
    value = value.zfill(6)
    return f"{value[0:2]}:{value[2:4]}:{value[4:6]}"


def _to_float(value):
    if value in (None, ""):
        return 0.0
    return float(str(value).replace(",", ""))


def _to_optional_float(value):
    if value in (None, ""):
        return None
    return _to_float(value)
