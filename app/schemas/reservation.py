from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum as PythonEnum

from app.schemas.private_lesson import PrivateLessonExtendedOut
from app.schemas.user import UserOut


class ReservationStatus(str, PythonEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ReservationBase(BaseModel):
    student_id: int
    private_lesson_id: int
    status: ReservationStatus

class ReservationOut(ReservationBase):
    id: int

    class Config:
        orm_mode = True

class ReservationCreate(ReservationBase):
    student_id: int
    private_lesson_id: int
    status: ReservationStatus

class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None

    class Config:
        orm_mode = True

class ReservationExtendedOut(ReservationOut):
    student: UserOut
    private_lesson: PrivateLessonExtendedOut