import unittest

from config import AppConfig


class TestAppConfig(unittest.TestCase):
    def test_mock_mode_does_not_require_kis_credentials(self):
        AppConfig(trading_mode="MOCK").validate()

    def test_real_mode_requires_kis_credentials(self):
        with self.assertRaisesRegex(ValueError, "KIS_APP_KEY"):
            AppConfig(trading_mode="REAL").validate()

    def test_real_mode_rejects_example_placeholders(self):
        config = AppConfig(
            trading_mode="REAL",
            kis_app_key="your_app_key_here",
            kis_app_secret="your_app_secret_here",
            kis_account_no="your_account_number",
            kis_cano="12345678",
            kis_acqe="01",
        )

        with self.assertRaises(ValueError):
            config.validate()

    def test_real_mode_accepts_required_credentials(self):
        config = AppConfig(
            trading_mode="REAL",
            kis_app_key="key",
            kis_app_secret="secret",
            kis_account_no="1234567890",
            kis_cano="87654321",
            kis_acqe="01",
        )

        config.validate()


if __name__ == '__main__':
    unittest.main()
