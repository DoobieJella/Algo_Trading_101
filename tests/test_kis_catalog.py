import unittest

from kis_catalog import domestic_stock_data_endpoints, find_endpoint, load_kis_endpoint_catalog


class TestKisCatalog(unittest.TestCase):
    def test_loads_domestic_daily_chart_endpoint_from_workbook(self):
        endpoints = load_kis_endpoint_catalog()

        endpoint = find_endpoint(endpoints, "국내주식기간별시세(일/주/월/년)")

        self.assertEqual(endpoint.path, "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice")
        self.assertEqual(endpoint.tr_id_mock, "FHKST03010100")

    def test_filters_virtual_supported_domestic_stock_data_endpoints(self):
        endpoints = domestic_stock_data_endpoints(load_kis_endpoint_catalog())
        names = {endpoint.api_name for endpoint in endpoints}

        self.assertIn("주식현재가 시세", names)
        self.assertIn("국내주식기간별시세(일/주/월/년)", names)
        self.assertNotIn("주식주문(현금)", names)


if __name__ == "__main__":
    unittest.main()
