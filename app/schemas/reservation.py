from app.schemas.private_lesson import PrivateLessonExtendedOut
from app.schemas.user import UserOut
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class ReservationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ReservationBase(BaseModel):
    private_lesson_id: int | None = None
    student_id: int | None = None
    status: ReservationStatus
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True


class ReservationCreate(ReservationBase):
    pass


class ReservationOut(ReservationBase):
    id: int


class ReservationExtendedOut(ReservationOut):
    student: UserOut | None = None
    private_lesson: PrivateLessonExtendedOut | None = None


class ReservationUpdate(BaseModel):
    private_lesson_id: Optional[int] = None
    student_id: Optional[int] = None
    status: Optional[ReservationStatus] = None

    class Config:
        from_attributes = True
