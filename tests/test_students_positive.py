from __future__ import annotations

import uuid

import allure
import pytest

from api.builders import StudentBuilder
from api.student_client import StudentApiClient
from api.waiters import retry_until, wait_until_student_readable


def _uniq(prefix: str = "auto") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:8]}"


def _phone() -> str:
    return f"+7999{uuid.uuid4().int % 10_000_000:07d}"


@allure.epic("Students API")
@allure.feature("Positive scenarios")
class TestGetStudents:
    @allure.story("GET /student")
    @allure.title("Получить список студентов")
    def test_get_students_list(self, api_client: StudentApiClient):
        with allure.step("Отправить GET /student"):
            response = api_client.get_students()

        with allure.step("Проверить HTTP 200 и структуру ответа"):
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == 1
            assert isinstance(body["students"], list)

        if body["students"]:
            with allure.step("Проверить поля первого студента в списке"):
                student = body["students"][0]
                for field in ("id", "name", "email", "phone_no", "gender", "status"):
                    assert field in student


@allure.epic("Students API")
@allure.feature("Positive scenarios")
class TestCreateStudent:
    @allure.story("POST /student")
    @pytest.mark.parametrize(
        "name,gender,status",
        [
            ("Anna Petrova", "female", 1),
            ("Petr Sidorov", "male", 0),
            ("Auto Test User", "male", 1),
        ],
        ids=["female_active", "male_inactive", "male_active"],
    )
    def test_create_student(
        self,
        created_student,
        name: str,
        gender: str,
        status: int,
    ):
        allure.dynamic.title(f"Создать студента: {name} / {gender} / status={status}")
        tag = _uniq("create")

        payload = (
            StudentBuilder()
            .with_name(name)
            .with_email(f"{tag}@example.com")
            .with_phone(_phone())
            .with_gender(gender)
            .with_status(status)
            .build_create()
        )

        with allure.step("Создать студента через API"):
            student = created_student(payload)

        with allure.step("Проверить, что ответ содержит переданные данные"):
            assert student["name"] == name
            assert student["email"] == payload.email
            assert student["phone_no"] == payload.phone_no
            assert student["gender"] == gender
            assert int(student["status"]) == status
            assert isinstance(student["id"], int)


@allure.epic("Students API")
@allure.feature("Positive scenarios")
class TestGetStudentById:
    @allure.story("GET /student/{id}")
    @pytest.mark.parametrize("picker", ["first", "last"], ids=["first_in_list", "last_in_list"])
    def test_get_student_by_id_from_list(self, api_client: StudentApiClient, picker: str):
        allure.dynamic.title(f"Получить студента по ID ({picker})")

        with allure.step("Получить список студентов"):
            list_response = api_client.get_students()
            assert list_response.status_code == 200
            students = list_response.json()["students"]
            assert students, "Список студентов пуст — нечего запрашивать по ID"
            expected = students[0] if picker == "first" else students[-1]

        with allure.step(f"GET /student/{expected['id']}"):
            student = wait_until_student_readable(api_client, expected["id"])

        with allure.step("Сверить данные с элементом списка"):
            assert student["id"] == expected["id"]
            assert student["name"] == expected["name"]
            assert student["email"] == expected["email"]
            assert student["phone_no"] == expected["phone_no"]
            assert student["gender"] == expected["gender"]
            assert int(student["status"]) == int(expected["status"])

    @allure.story("GET /student/{id}")
    @pytest.mark.parametrize(
        "gender,status",
        [("male", 1), ("female", 0)],
        ids=["created_male_active", "created_female_inactive"],
    )
    def test_get_newly_created_student(
        self,
        api_client: StudentApiClient,
        created_student,
        gender: str,
        status: int,
    ):
        allure.dynamic.title(f"GET только что созданного студента ({gender}, status={status})")
        tag = _uniq(f"get.{gender}")

        payload = (
            StudentBuilder()
            .with_name(f"Get By Id {gender}")
            .with_email(f"{tag}@example.com")
            .with_phone(_phone())
            .with_gender(gender)
            .with_status(status)
            .build_create()
        )

        with allure.step("Подготовить студента"):
            created = created_student(payload)
            student_id = created["id"]

        with allure.step(f"Повторно получить студента id={student_id}"):
            student = wait_until_student_readable(api_client, student_id)

        with allure.step("Проверить данные студента"):
            assert student["id"] == student_id
            assert student["name"] == payload.name
            assert student["email"] == payload.email
            assert student["phone_no"] == payload.phone_no
            assert student["gender"] == gender
            assert int(student["status"]) == status


@allure.epic("Students API")
@allure.feature("Positive scenarios")
class TestUpdateStudent:
    @allure.story("PUT /student/{id}")
    @pytest.mark.parametrize(
        "new_name,new_gender,new_status",
        [
            ("Updated Male", "male", 1),
            ("Updated Female", "female", 0),
        ],
        ids=["to_male_active", "to_female_inactive"],
    )
    def test_update_student(
        self,
        api_client: StudentApiClient,
        created_student,
        new_name: str,
        new_gender: str,
        new_status: int,
    ):
        allure.dynamic.title(f"Обновить студента → {new_name}")
        tag = _uniq("upd")

        create_payload = (
            StudentBuilder()
            .with_name("Before Update")
            .with_email(f"{tag}@example.com")
            .with_phone(_phone())
            .with_gender("male")
            .with_status(1)
            .build_create()
        )

        with allure.step("Создать студента для обновления"):
            created = created_student(create_payload)
            student_id = created["id"]
            original_phone = created["phone_no"]

        update_payload = (
            StudentBuilder()
            .with_name(new_name)
            .with_email(f"{tag}.new@example.com")
            .with_gender(new_gender)
            .with_status(new_status)
            .build_update()
        )

        with allure.step(f"Обновить студента id={student_id} (с ретраями)"):
            response = retry_until(
                lambda: api_client.update_student(student_id, update_payload),
                lambda body: body.get("status") == 1 and "student" in body,
            )

        with allure.step("Проверить результат обновления"):
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == 1, body
            assert body["message"] == "Student updated successfully"
            student = body["student"]
            assert student["id"] == student_id
            assert student["name"] == new_name
            assert student["email"] == update_payload.email
            assert student["gender"] == new_gender
            assert int(student["status"]) == new_status
            assert student["phone_no"] == original_phone


@allure.epic("Students API")
@allure.feature("Positive scenarios")
class TestDeleteStudent:
    @allure.story("DELETE /student/{id}")
    @pytest.mark.parametrize(
        "gender,status",
        [("male", 1), ("female", 1)],
        ids=["delete_male", "delete_female"],
    )
    def test_delete_student(self, api_client: StudentApiClient, gender: str, status: int):
        allure.dynamic.title(f"Удалить студента ({gender})")
        tag = _uniq(f"del.{gender}")

        payload = (
            StudentBuilder()
            .with_name(f"To Delete {gender}")
            .with_email(f"{tag}@example.com")
            .with_phone(_phone())
            .with_gender(gender)
            .with_status(status)
            .build_create()
        )

        with allure.step("Создать студента для удаления"):
            create_response = api_client.create_student(payload)
            assert create_response.status_code == 200
            create_body = create_response.json()
            assert create_body["status"] == 1
            student_id = create_body["student"]["id"]
            wait_until_student_readable(api_client, student_id)

        with allure.step(f"Удалить студента id={student_id}"):
            delete_response = api_client.delete_student(student_id)

        with allure.step("Проверить контракт ответа DELETE"):
            assert delete_response.status_code == 200
            delete_body = delete_response.json()
            assert delete_body["status"] == 1
            assert delete_body["message"] == "Student deleted successfully"
