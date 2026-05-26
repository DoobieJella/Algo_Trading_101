import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from kis_data import normalize_daily_bars, read_daily_bars, write_daily_bars


class TestKisData(unittest.TestCase):
    def test_normalizes_kis_daily_payload_to_daily_bars(self):
        payload = {
            "output2": [
                {
                    "stck_bsop_date": "20240103",
                    "stck_oprc": "70000",
                    "stck_hgpr": "71000",
                    "stck_lwpr": "69000",
                    "stck_clpr": "70500",
                    "acml_vol": "1234",
                    "acml_tr_pbmn": "87000000",
                },
                {
                    "stck_bsop_date": "20240102",
                    "stck_oprc": "69000",
                    "stck_hgpr": "70000",
                    "stck_lwpr": "68000",
                    "stck_clpr": "69500",
                    "acml_vol": "1000",
                    "acml_tr_pbmn": "69500000",
                },
            ]
        }

        bars = normalize_daily_bars("005930", payload)

        self.assertEqual([bar.date for bar in bars], ["2024-01-02", "2024-01-03"])
        self.assertEqual(bars[0].close, 69500)
        self.assertEqual(bars[0].volume, 1000)

    def test_writes_daily_bars_and_metadata(self):
        bars = normalize_daily_bars(
            "005930",
            {
                "output2": [
                    {
                        "stck_bsop_date": "20240102",
                        "stck_oprc": "69000",
                        "stck_hgpr": "70000",
                        "stck_lwpr": "68000",
                        "stck_clpr": "69500",
                        "acml_vol": "1000",
                        "acml_tr_pbmn": "69500000",
                    }
                ]
            },
        )
        with TemporaryDirectory() as directory:
            csv_path, metadata_path = write_daily_bars(
                "005930",
                bars,
                output_root=Path(directory),
                metadata={"endpoint": "test"},
            )

            loaded = read_daily_bars(csv_path)
            metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))

        self.assertEqual(loaded[0].symbol, "005930")
        self.assertEqual(metadata["endpoint"], "test")
        self.assertEqual(metadata["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
