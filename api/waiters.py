from __future__ import annotations

import time
from typing import Any, Callable

import requests

from api.student_client import StudentApiClient


def wait_until_student_readable(
    api_client: StudentApiClient,
    student_id: int,
    timeout: float = 8.0,
    interval: float = 0.4,
) -> dict:
    deadline = time.time() + timeout
    last_body: dict | None = None
    while time.time() < deadline:
        response = api_client.get_student(student_id)
        last_body = response.json()
        student = last_body.get("student")
        if isinstance(student, dict) and student.get("id") == student_id:
            return student
        time.sleep(interval)
    raise AssertionError(f"Student id={student_id} not readable within {timeout}s: {last_body}")


def retry_until(
    action: Callable[[], requests.Response],
    predicate: Callable[[dict[str, Any]], bool],
    *,
    attempts: int = 6,
    interval: float = 0.5,
) -> requests.Response:
    last: requests.Response | None = None
    for _ in range(attempts):
        last = action()
        try:
            body = last.json()
        except ValueError:
            body = {}
        if predicate(body):
            return last
        time.sleep(interval)
    assert last is not None
    return last
