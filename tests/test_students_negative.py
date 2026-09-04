from __future__ import annotations

import uuid

import allure
import pytest

from api.builders import StudentBuilder
from api.student_client import StudentApiClient
from api.waiters import wait_until_student_readable
from tests.assertions import assert_business_error

MISSING_STUDENT_ID = 999_999_99


def _phone() -> str:
    return f"+7{uuid.uuid4().int % 10**10:010d}"


def _email(prefix: str = "neg") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:8]}@example.com"


def _create_payload(**overrides) -> dict:
    payload = (
        StudentBuilder()
        .with_name(f"Neg {uuid.uuid4().hex[:6]}")
        .with_email(_email())
        .with_phone(_phone())
        .with_gender("male")
        .with_status(1)
        .build_create()
        .to_dict()
    )
    payload.update(overrides)
    return payload


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestCreateStudentNegative:
    @allure.story("POST /student — gender")
    @pytest.mark.parametrize("gender", ["other", "Male", None], ids=["other", "Male", "null"])
    def test_create_rejects_invalid_gender(self, api_client: StudentApiClient, gender):
        allure.dynamic.title(f"POST: невалидный gender={gender!r}")
        response = api_client.create_student(_create_payload(gender=gender))
        assert_business_error(response, message_contains="Wrong gender")

    @allure.story("POST /student — status")
    @pytest.mark.parametrize("status", [2, "1", None], ids=["out_of_range", "string", "null"])
    def test_create_rejects_invalid_status(self, api_client: StudentApiClient, status):
        allure.dynamic.title(f"POST: невалидный status={status!r}")
        response = api_client.create_student(_create_payload(status=status))
        assert_business_error(response, message_contains="Wrong status")

    @allure.story("POST /student — JSON")
    @pytest.mark.parametrize(
        "payload, message_part",
        [
            ({}, "Empty JSON"),
            ({"name": "N", "email": "a@b.c", "phone_no": "+1", "status": 1}, "Wrong JSON"),
        ],
        ids=["empty", "missing_gender"],
    )
    def test_create_rejects_invalid_json(
        self,
        api_client: StudentApiClient,
        payload: dict,
        message_part: str,
    ):
        allure.dynamic.title(f"POST: {message_part}")
        response = api_client.create_student(payload)
        assert_business_error(response, message_contains=message_part)

    @allure.story("POST /student — уникальность name+phone")
    @allure.title("Повтор пары name+phone отклоняется")
    def test_create_rejects_duplicate_name_and_phone(
        self,
        api_client: StudentApiClient,
        created_student,
    ):
        name = f"Dup {uuid.uuid4().hex[:6]}"
        phone = _phone()
        created_student(
            StudentBuilder()
            .with_name(name)
            .with_email(_email("dup1"))
            .with_phone(phone)
            .with_gender("male")
            .with_status(1)
            .build_create()
        )

        with allure.step("Повторно создать с тем же name и phone_no"):
            response = api_client.create_student(
                _create_payload(name=name, phone_no=phone, email=_email("dup2"))
            )

        assert_business_error(response, message_contains="not unique")


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestGetStudentNegative:
    @allure.story("GET /student/{id}")
    @allure.title("Несуществующий студент")
    def test_get_nonexistent_student(self, api_client: StudentApiClient):
        response = api_client.get_student(MISSING_STUDENT_ID)
        assert_business_error(response, message_contains="Student not found")

    @allure.story("GET /student/{id}")
    @allure.title("Нечисловой id")
    def test_get_student_invalid_id_format(self, api_client: StudentApiClient):
        response = api_client.request("GET", "/student/abc")
        with allure.step("Ожидаем HTTP 404"):
            assert response.status_code == 404


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestUpdateStudentNegative:
    @allure.story("PUT /student/{id}")
    @allure.title("Несуществующий студент")
    def test_update_nonexistent_student(self, api_client: StudentApiClient):
        payload = (
            StudentBuilder()
            .with_name("Ghost")
            .with_email(_email("ghost"))
            .with_gender("male")
            .with_status(1)
            .build_update()
        )
        response = api_client.update_student(MISSING_STUDENT_ID, payload)
        assert_business_error(response, message_contains="Student not found")

    @allure.story("PUT /student/{id}")
    @allure.title("Невалидный gender на существующем студенте")
    def test_update_existing_rejects_invalid_gender(
        self,
        api_client: StudentApiClient,
        created_student,
    ):
        created = created_student(
            StudentBuilder()
            .with_name(f"Upd Neg {uuid.uuid4().hex[:6]}")
            .with_email(_email("upd"))
            .with_phone(_phone())
            .with_gender("male")
            .with_status(1)
            .build_create()
        )
        payload = {
            "name": created["name"],
            "email": created["email"],
            "gender": "other",
            "status": 1,
        }

        response = api_client.update_student(created["id"], payload)
        assert_business_error(response, message_contains="Wrong gender")

        current = wait_until_student_readable(api_client, created["id"])
        assert current["gender"] == "male"

    @allure.story("PUT /student/{id}")
    @allure.title("Пустой JSON")
    def test_update_rejects_empty_json(self, api_client: StudentApiClient):
        response = api_client.update_student(MISSING_STUDENT_ID, {})
        assert_business_error(response, message_contains="Empty JSON")


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestDeleteStudentNegative:
    @allure.story("DELETE /student/{id}")
    @allure.title("Удаление несуществующего студента")
    def test_delete_nonexistent_student(self, api_client: StudentApiClient):
        response = api_client.delete_student(MISSING_STUDENT_ID)
        assert_business_error(response, message_contains="not found")


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestCreateEdgeNegative:
    @allure.story("POST /student")
    @allure.title("Длинное name — JSON-ответ без HTTP 500")
    def test_long_name_must_not_500(self, api_client: StudentApiClient):
        response = api_client.create_student(_create_payload(name="N" * 60))
        with allure.step("Ожидаем JSON-ответ без 5xx"):
            assert response.status_code == 200, response.text[:300]
            body = response.json()
            assert body.get("status") in (0, 1), body
            if body.get("status") == 1 and body.get("student"):
                api_client.delete_student(body["student"]["id"])

    @allure.story("POST /student")
    @allure.title("Длинный email — JSON-ответ без HTTP 500")
    def test_long_email_must_not_500(self, api_client: StudentApiClient):
        response = api_client.create_student(_create_payload(email=("a" * 45) + "@ex.com"))
        with allure.step("Ожидаем JSON-ответ без 5xx"):
            assert response.status_code == 200, response.text[:300]
            body = response.json()
            assert body.get("status") in (0, 1), body
            if body.get("status") == 1 and body.get("student"):
                api_client.delete_student(body["student"]["id"])

    @allure.story("POST /student")
    @allure.title("Длинный phone_no — JSON-ответ без HTTP 500")
    def test_long_phone_must_not_500(self, api_client: StudentApiClient):
        response = api_client.create_student(_create_payload(phone_no="1" * 26))
        with allure.step("Ожидаем JSON-ответ без 5xx"):
            assert response.status_code == 200, response.text[:300]
            body = response.json()
            assert body.get("status") in (0, 1), body
            if body.get("status") == 1 and body.get("student"):
                api_client.delete_student(body["student"]["id"])

    @allure.story("POST /student")
    @allure.title("name как object — бизнес-ошибка Wrong JSON")
    def test_name_object_must_be_business_error(self, api_client: StudentApiClient):
        payload = _create_payload()
        payload["name"] = {"first": "Ivan"}
        response = api_client.create_student(payload)
        assert_business_error(response, message_contains="Wrong JSON")

    @allure.story("POST /student")
    @allure.title("status=true отклоняется (допустимы только 0|1)")
    def test_boolean_status_must_be_rejected(self, api_client: StudentApiClient):
        response = api_client.create_student(_create_payload(status=True))
        assert_business_error(response, message_contains="Wrong status")


@allure.epic("Students API")
@allure.feature("Negative scenarios")
class TestDeleteSideEffects:
    @allure.story("DELETE /student/{id}")
    @allure.title("После DELETE студент недоступен по GET")
    def test_delete_must_remove_student(self, api_client: StudentApiClient):
        create_resp = api_client.create_student(_create_payload())
        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body.get("status") == 1, body
        student_id = body["student"]["id"]
        wait_until_student_readable(api_client, student_id)

        with allure.step("Удалить студента"):
            delete_resp = api_client.delete_student(student_id)
            assert delete_resp.status_code == 200
            assert delete_resp.json().get("status") == 1

        with allure.step("GET после DELETE — студент не найден"):
            get_resp = api_client.get_student(student_id)
            assert_business_error(get_resp, message_contains="Student not found")
