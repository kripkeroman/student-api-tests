from __future__ import annotations

from typing import Any

import allure
import requests

from api.base_client import BaseApiClient
from api.models import StudentPayload, UpdateStudentPayload


class StudentApiClient(BaseApiClient):

    @allure.step("GET /student — получить список студентов")
    def get_students(self) -> requests.Response:
        return self.request("GET", "/student")

    @allure.step("POST /student — создать студента")
    def create_student(self, payload: StudentPayload | dict[str, Any]) -> requests.Response:
        body = payload.to_dict() if isinstance(payload, StudentPayload) else payload
        return self.request("POST", "/student", json=body)

    @allure.step("GET /student/{student_id} — получить студента id={student_id}")
    def get_student(self, student_id: int) -> requests.Response:
        return self.request("GET", f"/student/{student_id}")

    @allure.step("PUT /student/{student_id} — обновить студента id={student_id}")
    def update_student(
        self,
        student_id: int,
        payload: UpdateStudentPayload | dict[str, Any],
    ) -> requests.Response:
        body = payload.to_dict() if isinstance(payload, UpdateStudentPayload) else payload
        return self.request("PUT", f"/student/{student_id}", json=body)

    @allure.step("DELETE /student/{student_id} — удалить студента id={student_id}")
    def delete_student(self, student_id: int) -> requests.Response:
        return self.request("DELETE", f"/student/{student_id}")
