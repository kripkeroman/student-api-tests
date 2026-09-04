from __future__ import annotations

import logging
from io import StringIO

import allure
import pytest
from allure_commons import hookimpl, plugin_manager

from api.student_client import StudentApiClient
from api.waiters import wait_until_student_readable


class _HideFixtureLifecyclePlugin:

    @hookimpl(tryfirst=True)
    def report_container(self, container):
        container.befores.clear()
        container.afters.clear()


def pytest_configure(config):
    plugin = _HideFixtureLifecyclePlugin()
    plugin_manager.register(plugin, "hide_fixture_lifecycle")
    config.add_cleanup(lambda: plugin_manager.unregister(name="hide_fixture_lifecycle"))


@pytest.fixture
def api_client() -> StudentApiClient:
    client = StudentApiClient()
    yield client
    client.close()


@pytest.fixture(autouse=True)
def _capture_test_log(request):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root = logging.getLogger()
    previous_level = root.level
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    request.node._test_log_stream = stream

    yield

    root.removeHandler(handler)
    root.setLevel(previous_level)
    handler.close()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    stream = getattr(item, "_test_log_stream", None)
    allure.attach(
        stream.getvalue() if stream is not None else "(no log output)",
        name="test-log",
        attachment_type=allure.attachment_type.TEXT,
    )


@pytest.fixture
def created_student(api_client: StudentApiClient):
    created_ids: list[int] = []

    def _create(payload) -> dict:
        with allure.step("Создать студента и дождаться доступности"):
            response = api_client.create_student(payload)
            assert response.status_code == 200, response.text
            body = response.json()
            assert body.get("status") == 1, body
            student_id = body["student"]["id"]
            created_ids.append(student_id)
            return wait_until_student_readable(api_client, student_id)

    yield _create

    for student_id in created_ids:
        api_client.delete_student(student_id)
