import unittest
from unittest.mock import patch

from kis_api import KisApi


class TestKisApiData(unittest.TestCase):
    def test_mock_request_returns_daily_chart_payload_without_http(self):
        api = KisApi("", "", "", mode="MOCK")

        with patch("kis_api.requests.request") as request:
            payload = api.get_domestic_daily_itemchartprice(
                "005930",
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

        request.assert_not_called()
        self.assertEqual(payload["rt_cd"], "0")
        self.assertEqual(len(payload["output2"]), 5)

    def test_mock_current_price_uses_static_price(self):
        api = KisApi("", "", "", mode="MOCK")

        self.assertEqual(api.get_current_price("005930"), 70000)


if __name__ == "__main__":
    unittest.main()
