import os
from urllib.parse import urlparse
from app.token_manager_async import TokenManager
import logging
import httpx

class OAuthAsyncClient:

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
        print(f"Setting auth required for base URL: {base_url}")
        self._auth_base_urls.add(base_url)

    def _extract_base_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    async def get(self, url, verify=True, **kwargs):
        """Sends a GET request.
    
        :param url: URL for the new :class:`Request` object.
        :param **kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        # Create resource on upstream
        async with httpx.AsyncClient(verify=verify) as client:
            print(f"PRINT GET1 url: {url}")
            if not self._needs_auth(url):
                print(f"GET2")
                response = await client.get(
                    url,
                    **kwargs,
                )
                print(f"GET3, status_code: {response.status_code}")
                if response.status_code != 401:
                    print(f"GET4")
                    return response
                print(f"GET5")
                self._set_auth_required(url)

            print(f"GET6")
            kwargs = await self._add_auth_header(**kwargs)
            print(f"GET7, kwargs headers: {kwargs.get('headers')}")
            response = await client.get(url, **kwargs)
            print(f"GET8, status_code: {response.status_code}")
        return response

    async def delete(self, url, verify=True, **kwargs):
        """Sends a DELETE request.
        """
        # Create resource on upstream
        async with httpx.AsyncClient(verify=verify) as client:
            if not self._needs_auth(url):
                response = await client.delete(
                    url,
                    **kwargs,
                )
                if response.status_code != 401:
                    return response
                self._set_auth_required(url)
            kwargs = await self._add_auth_header(**kwargs)
            response = await client.delete(url, **kwargs)
        return response
    
    async def post(self, url, verify=True, **kwargs):
        """Sends a POST request.
        """
        # Create resource on upstream
        async with httpx.AsyncClient(verify=verify) as client:
            if not self._needs_auth(url):
                response = await client.post(
                    url,
                    **kwargs,
                )
                if response.status_code != 401:
                    return response
                self._set_auth_required(url)
            kwargs = await self._add_auth_header(**kwargs)
            response = await client.post(url, **kwargs)
        return response

    async def patch(self, url, verify=True, **kwargs):
        """Sends a PATCH request.
        """
        # Create resource on upstream
        async with httpx.AsyncClient(verify=verify) as client:
            if not self._needs_auth(url):
                response = await client.patch(
                    url,
                    **kwargs,
                )
                if response.status_code != 401:
                    return response
                self._set_auth_required(url)
            kwargs = await self._add_auth_header(**kwargs)
            response = await client.patch(url, **kwargs)
        return response
        
    
    async def _add_auth_header(self, **kwargs):
        headers = kwargs.get("headers", {})
        token = await self._token_manager._token()
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


auth_client = OAuthAsyncClient()

