import unittest
from unittest.mock import patch

from kis_api import KisApi
from rl_execution.data import normalize_minute_bars


class TestRlExecutionKis(unittest.TestCase):
    def test_mock_minute_endpoint_returns_normalizable_payload_without_http(self):
        api = KisApi("", "", "", mode="MOCK")

        with patch("kis_api.requests.request") as request:
            payload = api.get_domestic_time_itemchartprice("005930")

        request.assert_not_called()
        bars = normalize_minute_bars("005930", payload)
        self.assertEqual(len(bars), 30)
        self.assertEqual(bars[0].symbol, "005930")


if __name__ == "__main__":
    unittest.main()
