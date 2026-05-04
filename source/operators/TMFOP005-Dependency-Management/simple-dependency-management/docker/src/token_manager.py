import os
import requests
import json
from datetime import datetime, timedelta

class TokenManager:

    def __init__(self, token_url, client_id, client_secret, refresh_buffer_seconds = 30) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._access_token = None
        self._token_expiry = None
                
    def _token(self) -> str:
        if self._is_token_valid():
            return self._access_token        
        try:
            if self._client_id and self._client_secret and self._token_url:
                r = requests.post(
                    self._token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                )
            else:
                raise RuntimeError("No credentials provided for token retrieval")
            r.raise_for_status()
            
            token_data = r.json()
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 300)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return self._access_token
        except requests.HTTPError as e:
            raise RuntimeError(
                f"get_token failed with HTTP status {r.status_code}: {e}"
            ) from None

    def _is_token_valid(self):
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now() < (self._token_expiry - timedelta(seconds=self._refresh_buffer_seconds))
        
    def reset(self):
        self._access_token = None
        self._token_expiry = None
