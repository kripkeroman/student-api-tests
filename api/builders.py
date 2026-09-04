from __future__ import annotations

from api.models import Gender, StudentPayload, StudentStatus, UpdateStudentPayload


class StudentBuilder:

    def __init__(self) -> None:
        self._name = "Ivan Ivanov"
        self._email = "ivan@example.com"
        self._phone_no = "+79990001122"
        self._gender: Gender = "male"
        self._status: StudentStatus = 1

    def with_name(self, name: str) -> StudentBuilder:
        self._name = name
        return self

    def with_email(self, email: str) -> StudentBuilder:
        self._email = email
        return self

    def with_phone(self, phone_no: str) -> StudentBuilder:
        self._phone_no = phone_no
        return self

    def with_gender(self, gender: Gender) -> StudentBuilder:
        self._gender = gender
        return self

    def with_status(self, status: StudentStatus) -> StudentBuilder:
        self._status = status
        return self

    def build_create(self) -> StudentPayload:
        return StudentPayload(
            name=self._name,
            email=self._email,
            phone_no=self._phone_no,
            gender=self._gender,
            status=self._status,
        )

    def build_update(self) -> UpdateStudentPayload:
        return UpdateStudentPayload(
            name=self._name,
            email=self._email,
            gender=self._gender,
            status=self._status,
        )
