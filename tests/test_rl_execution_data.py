import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from models import MinuteBar
from rl_execution.data import (
    load_symbol_episodes,
    make_synthetic_episode,
    normalize_minute_bars,
    read_minute_bars,
    split_episodes_by_date,
    write_minute_bars,
)


class TestRlExecutionData(unittest.TestCase):
    def test_normalizes_kis_minute_payload(self):
        payload = {
            "output2": [
                {
                    "stck_bsop_date": "20240105",
                    "stck_cntg_hour": "093000",
                    "stck_oprc": "70000",
                    "stck_hgpr": "70100",
                    "stck_lwpr": "69900",
                    "stck_prpr": "70050",
                    "cntg_vol": "1000",
                    "acml_tr_pbmn": "70050000",
                }
            ]
        }

        bars = normalize_minute_bars("005930", payload)

        self.assertEqual(bars[0].date, "2024-01-05")
        self.assertEqual(bars[0].time, "09:30:00")
        self.assertEqual(bars[0].close, 70050)
        self.assertEqual(bars[0].volume, 1000)

    def test_writes_reads_and_splits_minute_episodes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for offset, trade_date in enumerate(["2024-01-01", "2024-01-02", "2024-01-03"]):
                write_minute_bars(
                    "005930",
                    trade_date,
                    make_synthetic_episode(trade_date=trade_date, start_price=70000 + offset),
                    output_root=root,
                )

            loaded = load_symbol_episodes(root, "005930", horizon_minutes=30)
            splits = split_episodes_by_date(loaded)

        self.assertEqual(len(loaded), 3)
        self.assertIsInstance(loaded[0][0], MinuteBar)
        self.assertEqual(len(splits.train), 2)
        self.assertEqual(len(splits.validation), 1)
        self.assertEqual(len(splits.test), 0)

    def test_read_minute_bars_roundtrip(self):
        bars = make_synthetic_episode(minutes=2)
        with TemporaryDirectory() as directory:
            csv_path, _ = write_minute_bars("005930", "2024-01-05", bars, output_root=Path(directory))
            loaded = read_minute_bars(csv_path)

        self.assertEqual(loaded[1].time, bars[1].time)


if __name__ == "__main__":
    unittest.main()
