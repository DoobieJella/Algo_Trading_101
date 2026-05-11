import logging
import requests
import json

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
            # Use Virtual Server or Internal Mock Logic
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

    def get_current_price(self, code):
        """
        Get current price of a stock (Mock or Real).
        """
        if self.mode == "MOCK":
            return 70000

        # Implementation for Real/VTS API would go here
        # headers = { ... }
        # url = ...
        return None

    def place_order(self, code, qty, price, side="BUY"):
        """
        Place an order.
        """
        logger.info(f"[{self.mode}] Placing {side} Order: {code} x {qty} @ {price}")
        return True
