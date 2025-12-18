import requests
from datetime import datetime, timedelta

class TokenManager:
    """Manages tokens with automatic refresh."""
    
    def __init__(self, token_url, client_id, client_secret, refresh_buffer=30):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_buffer = refresh_buffer
        self.access_token = None
        self.token_expiry = None
    
    def get_token(self):
        if self._is_token_valid():
            return self.access_token
        else:
            return self._request_new_token()
    
    def _is_token_valid(self):
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < (self.token_expiry - timedelta(seconds=self.refresh_buffer))
    
    def _request_new_token(self):
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 300)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        return self.access_token
    
