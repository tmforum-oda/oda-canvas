import os
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
from token_manager import TokenManager
import logging

logger = logging.getLogger("depapiop")


class OAuth2Requests:

    def __init__(self, token_url = None, client_id = None, client_secret = None, refresh_buffer_seconds = 30) -> None:
        self.token_url = token_url if token_url else os.getenv("OAUTH2_TOKEN_URL")
        self.client_id = client_id if client_id else os.getenv("OAUTH2_CLIENT_ID")
        self.client_secret = client_secret if client_secret else os.getenv("OAUTH2_CLIENT_SECRET")
        self.refresh_buffer_seconds = refresh_buffer_seconds
        self._token_manager = TokenManager(self.token_url, self.client_id, self.client_secret, self.refresh_buffer_seconds)
        self._auth_base_urls = set()

    def _needs_auth(self, url: str) -> bool:
        base_url = self._extract_base_url(url)
        return base_url in self._auth_base_urls

    def _set_auth_required(self, url: str):
        base_url = self._extract_base_url(url)
        logger.info(f"Setting auth required for base URL: {base_url}")
        self._auth_base_urls.add(base_url)

    def _extract_base_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def get(self, url, params=None, **kwargs):
        """Sends a GET request.
    
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        if not self._needs_auth(url):
            response = requests.get(url, params=params, **kwargs)
            if response.status_code != 401:
                return response
            self._set_auth_required(url)
        kwargs = self._add_auth_header(**kwargs)
        response = requests.get(url, params=params, **kwargs)
        return response
    
    def _add_auth_header(self, **kwargs):
        headers = kwargs.get("headers", {})
        token = self._token_manager._token()
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        return kwargs
    
    def reset(self, token_url = None, client_id = None, client_secret = None, refresh_buffer_seconds = None) -> None:
        self.token_url = token_url if token_url else self.token_url
        self.client_id = client_id if client_id else self.client_id
        self.client_secret = client_secret if client_secret else self.client_secret
        self.refresh_buffer_seconds = refresh_buffer_seconds if refresh_buffer_seconds else self.refresh_buffer_seconds
        self._token_manager = TokenManager(self.token_url, self.client_id, self.client_secret, self.refresh_buffer_seconds)
        self._auth_base_urls = set()


auth_requests = OAuth2Requests()

