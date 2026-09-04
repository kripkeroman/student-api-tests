from __future__ import annotations

from typing import Any

import allure
import requests


def assert_business_error(
    response: requests.Response,
    *,
    message_contains: str,
    expected_http: int = 200,
) -> dict[str, Any]:
    with allure.step(f"Проверить ошибку: содержит '{message_contains}'"):
        assert response.status_code == expected_http, response.text
        body = response.json()
        allure.attach(
            response.text,
            name="error-response",
            attachment_type=allure.attachment_type.JSON,
        )
        assert body.get("status") == 0, body
        assert message_contains.lower() in str(body.get("message", "")).lower(), body
        assert not body.get("student"), body
        return body
