import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from kis_api import KisApi
from kis_probe import run_kis_data_probe


class TestKisProbe(unittest.TestCase):
    def test_probe_writes_availability_report_from_mock_api(self):
        api = KisApi("", "", "", mode="MOCK")

        with TemporaryDirectory() as directory:
            results, run_dir = run_kis_data_probe(
                api,
                output_dir=Path(directory),
                symbols=("005930",),
                start_date="2024-01-01",
                end_date="2024-01-05",
            )
            rows = json.loads((run_dir / "availability.json").read_text(encoding="utf-8"))

        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.status == "SUPPORTED" for result in results))
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
