from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Gender = Literal["male", "female"]
StudentStatus = Literal[0, 1]


@dataclass
class StudentPayload:
    name: str
    email: str
    phone_no: str
    gender: Gender
    status: StudentStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UpdateStudentPayload:
    name: str
    email: str
    gender: Gender
    status: StudentStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
