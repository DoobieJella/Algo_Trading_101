import logging
import json
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

class KisApi:
    BASE_URL_REAL = "https://openapi.koreainvestment.com:9443"
    BASE_URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    def __init__(self, app_key, app_secret, account_no, mode="MOCK"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.mode = mode.upper()
        self.access_token = None
        
        if self.mode == "REAL":
            self.base_url = self.BASE_URL_REAL
        else:
            self.base_url = self.BASE_URL_VIRTUAL

    def auth(self):
        """
        Authenticate with KIS API to get Access Token.
        """
        if self.mode == "MOCK":
            logger.info("[MOCK] Authentication successful (simulated)")
            self.access_token = "MOCK_TOKEN"
            return True
            
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            logger.info("OAuth POST call in progress...")
            # ENDPOINT: /oauth2/tokenP (Production/Real) typically differs slightly from VTS
            # For simplicity using standard endpoint pattern, but highly dependent on specifically which API (Domestic/Overseas)
            # This is a placeholder for the actual OAUTH call
            url = f"{self.base_url}/oauth2/tokenP" 
            resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
            resp.raise_for_status()
            data = resp.json()

            self.access_token = data["access_token"]
            logger.info("KIS authentication successful")

            return True 
        except Exception as e:
            logger.error(f"Authentication failed, error: {e}")
            return False

    def request(self, method, path, tr_id="", params=None, body=None, timeout=10):
        if self.mode == "MOCK":
            return self._mock_response(path, params or {})

        if not self.access_token and not self.auth():
            raise RuntimeError("KIS authentication failed")

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        url = f"{self.base_url}{path}"
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params if method.upper() == "GET" else None,
            data=json.dumps(body) if body is not None else None,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_current_price(self, code):
        """
        Get current price of a stock (Mock or Real).
        """
        if self.mode == "MOCK":
            return 70000

        data = self.request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
            },
        )
        output = data.get("output", {})
        price = output.get("stck_prpr")
        return float(price) if price not in (None, "") else None

    def get_domestic_daily_itemchartprice(
        self,
        code,
        start_date,
        end_date,
        market_code="J",
        period="D",
        adjusted=True,
    ):
        return self.request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": market_code,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": _compact_date(start_date),
                "FID_INPUT_DATE_2": _compact_date(end_date),
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": "0" if adjusted else "1",
            },
        )

    def get_domestic_time_itemchartprice(
        self,
        code,
        input_hour="153000",
        market_code="J",
        include_previous=False,
    ):
        return self.request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            tr_id="FHKST03010200",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": market_code,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": input_hour,
                "FID_PW_DATA_INCU_YN": "Y" if include_previous else "N",
            },
        )

    def place_order(self, code, qty, price, side="BUY"):
        """
        Place an order.
        """
        logger.info(f"[{self.mode}] Placing {side} Order: {code} x {qty} @ {price}")
        return True

    def _mock_response(self, path, params):
        symbol = params.get("FID_INPUT_ISCD", "005930")
        if path.endswith("/inquire-price"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output": {
                    "stck_shrn_iscd": symbol,
                    "stck_prpr": "70000",
                    "stck_oprc": "69500",
                    "stck_hgpr": "70500",
                    "stck_lwpr": "69000",
                    "acml_vol": "1000000",
                    "acml_tr_pbmn": "70000000000",
                },
            }
        if path.endswith("/inquire-daily-price"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output": _mock_daily_rows(symbol, days=5),
            }
        if path.endswith("/inquire-daily-itemchartprice"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output1": {
                    "stck_shrn_iscd": symbol,
                    "stck_prpr": "70000",
                    "acml_vol": "1000000",
                    "acml_tr_pbmn": "70000000000",
                },
                "output2": _mock_daily_rows(symbol, days=5),
            }
        if path.endswith("/inquire-time-itemchartprice"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output1": {
                    "stck_shrn_iscd": symbol,
                    "stck_prpr": "70000",
                    "acml_vol": "1000000",
                },
                "output2": _mock_minute_rows(symbol, minutes=30),
            }
        if path.endswith("/inquire-asking-price-exp-ccn"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output1": {
                    "askp1": "70050",
                    "bidp1": "69950",
                    "askp_rsqn1": "1000",
                    "bidp_rsqn1": "1200",
                },
            }
        if path.endswith("/inquire-ccnl") or path.endswith("/inquire-time-itemconclusion"):
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "mock success",
                "output": _mock_minute_rows(symbol, minutes=5),
            }
        return {
            "rt_cd": "1",
            "msg_cd": "MOCK404",
            "msg1": f"No mock response for {path}",
            "output": {},
        }


def _compact_date(value):
    return str(value).replace("-", "")


def _mock_daily_rows(symbol, days):
    end = date(2024, 1, 5)
    rows = []
    for offset in range(days):
        current = end - timedelta(days=offset)
        close = 70000 - (offset * 500)
        rows.append(
            {
                "stck_bsop_date": current.strftime("%Y%m%d"),
                "stck_oprc": str(close - 300),
                "stck_hgpr": str(close + 600),
                "stck_lwpr": str(close - 800),
                "stck_clpr": str(close),
                "acml_vol": str(1000000 + offset),
                "acml_tr_pbmn": str(close * (1000000 + offset)),
                "stck_shrn_iscd": symbol,
            }
        )
    return rows


def _mock_minute_rows(symbol, minutes):
    rows = []
    base = 70000
    for index in range(minutes):
        close = base + ((index % 7) - 3) * 10 + index
        hour = 930 + index
        rows.append(
            {
                "stck_bsop_date": "20240105",
                "stck_cntg_hour": f"{hour:04d}00",
                "stck_oprc": str(close - 5),
                "stck_hgpr": str(close + 15),
                "stck_lwpr": str(close - 15),
                "stck_prpr": str(close),
                "stck_clpr": str(close),
                "cntg_vol": str(1000 + index * 10),
                "acml_vol": str(1000 + index * 10),
                "acml_tr_pbmn": str(close * (1000 + index * 10)),
                "stck_shrn_iscd": symbol,
            }
        )
    return rows
