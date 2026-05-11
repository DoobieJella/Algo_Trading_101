import unittest
from unittest.mock import MagicMock, patch

from broker import KisBroker, MockBroker, create_broker
from config import AppConfig
from kis_api import KisApi
from models import Signal


class TestBroker(unittest.TestCase):
    def test_create_broker_uses_mock_for_mock_mode(self):
        broker = create_broker(AppConfig(trading_mode="MOCK"))

        self.assertIsInstance(broker, MockBroker)

    def test_mock_broker_executes_signal_with_signal_price(self):
        broker = MockBroker()

        result = broker.execute_signal(Signal("005930", "BUY", price=1000))

        self.assertEqual(result.status, "FILLED")
        self.assertEqual(result.order_id, "MOCK-1")
        self.assertEqual(broker.orders[0].symbol, "005930")
        self.assertEqual(broker.orders[0].price, 1000)

    def test_mock_broker_uses_configured_price_when_signal_has_no_price(self):
        broker = MockBroker({"005930": 72000})

        result = broker.execute_signal(Signal("005930", "SELL"))

        self.assertEqual(result.status, "FILLED")
        self.assertEqual(result.price, 72000)

    def test_kis_broker_delegates_order_to_api(self):
        api = MagicMock(spec=KisApi)
        api.get_current_price.return_value = 1000
        api.place_order.return_value = True
        broker = KisBroker(api)

        result = broker.execute_signal(Signal("005930", "BUY"))

        api.place_order.assert_called_once_with("005930", 1, 1000, "BUY")
        self.assertEqual(result.status, "ACCEPTED")

    def test_kis_api_mock_auth_does_not_post(self):
        api = KisApi("", "", "", mode="MOCK")

        with patch("kis_api.requests.post") as post:
            self.assertTrue(api.auth())

        post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
