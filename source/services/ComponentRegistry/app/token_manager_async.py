import os
import requests
import json
from datetime import datetime, timedelta
from authlib.integrations.httpx_client import AsyncOAuth2Client

class TokenManager:

    def __init__(self, token_url, client_id, client_secret, refresh_buffer_seconds = 30) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._access_token = None
        self._token_expiry = None

    async def _token(self) -> str:
        if self._is_token_valid():
            return self._access_token        
        try:
            if self._client_id and self._client_secret and self._token_url:

                # Use authlib OAuth2Client with client credentials
                async with AsyncOAuth2Client(
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    token_endpoint=self._token_url
                ) as oauth_client:
                    # Fetch token using client credentials grant
                    token_data = await oauth_client.fetch_token(
                        self._token_url,
                        grant_type='client_credentials'
                    )
                
            else:
                raise RuntimeError("No credentials provided for token retrieval")
            
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 300)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return self._access_token
        except Exception as e:
            raise RuntimeError(
                f"get_token failed with error message: {e}"
            ) from e

    def _is_token_valid(self):
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now() < (self._token_expiry - timedelta(seconds=self._refresh_buffer_seconds))
        
    def reset(self):
        self._access_token = None
        self._token_expiry = None
