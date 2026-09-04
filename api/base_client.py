from __future__ import annotations

import logging
from typing import Any

import requests

from config import BASE_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class BaseApiClient:

    def __init__(self, base_url: str = BASE_URL, timeout: int = REQUEST_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _log_exchange(self, method: str, url: str, response: requests.Response, **kwargs: Any) -> None:
        body = kwargs.get("json")
        logger.info(">>> %s %s", method.upper(), url)
        if body is not None:
            logger.info(">>> request body: %s", body)
        logger.info("<<< status: %s", response.status_code)
        logger.info("<<< response body: %s", response.text)

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = self._url(path)
        response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        self._log_exchange(method, url, response, **kwargs)
        return response

    def close(self) -> None:
        self.session.close()
