import os
from dataclasses import dataclass

from dotenv import load_dotenv


VALID_TRADING_MODES = {"MOCK", "REAL"}
VALID_KIS_API_ENVS = {"MOCK", "VIRTUAL", "REAL"}
PLACEHOLDER_VALUES = {
    "your_app_key_here",
    "your_app_secret_here",
    "your_account_number",
    "12345678",
}


@dataclass(frozen=True)
class AppConfig:
    trading_mode: str = "MOCK"
    kis_api_env: str = "VIRTUAL"
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""
    kis_cano: str = ""
    kis_acqe: str = ""

    def __post_init__(self):
        object.__setattr__(self, "trading_mode", self.trading_mode.upper())
        object.__setattr__(self, "kis_api_env", self.kis_api_env.upper())

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            trading_mode=os.getenv("TRADING_MODE", "MOCK"),
            kis_api_env=os.getenv("KIS_API_ENV", "VIRTUAL"),
            kis_app_key=os.getenv("KIS_APP_KEY", ""),
            kis_app_secret=os.getenv("KIS_APP_SECRET", ""),
            kis_account_no=os.getenv("KIS_ACCOUNT_NO", ""),
            kis_cano=os.getenv("KIS_CANO", ""),
            kis_acqe=os.getenv("KIS_ACQE", ""),
        )

    def validate(self):
        if self.trading_mode not in VALID_TRADING_MODES:
            raise ValueError(f"Unsupported TRADING_MODE: {self.trading_mode}")
        if self.kis_api_env not in VALID_KIS_API_ENVS:
            raise ValueError(f"Unsupported KIS_API_ENV: {self.kis_api_env}")

        if self.trading_mode == "MOCK":
            return

        self._validate_kis_credentials("REAL mode")

    def validate_kis_data_access(self):
        if self.kis_api_env not in VALID_KIS_API_ENVS:
            raise ValueError(f"Unsupported KIS_API_ENV: {self.kis_api_env}")
        if self.kis_api_env == "MOCK":
            return

        self._validate_kis_credentials(f"{self.kis_api_env} KIS data access")

    def _validate_kis_credentials(self, context):
        missing = [
            name
            for name, value in {
                "KIS_APP_KEY": self.kis_app_key,
                "KIS_APP_SECRET": self.kis_app_secret,
                "KIS_ACCOUNT_NO": self.kis_account_no,
                "KIS_CANO": self.kis_cano,
                "KIS_ACQE": self.kis_acqe,
            }.items()
            if not value.strip() or value.strip() in PLACEHOLDER_VALUES
        ]
        if missing:
            raise ValueError(f"Missing required {context} settings: {', '.join(missing)}")
