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
    private_lesson_id: int
    student_id: int
    status: ReservationStatus
    start_time: datetime
    end_time: datetime


class ReservationCreate(ReservationBase):
    pass


class ReservationOut(ReservationBase):
    id: int

    class Config:
        orm_mode = True


class ReservationExtendedOut(ReservationOut):
    student: UserOut
    private_lesson: PrivateLessonExtendedOut


class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None

    class Config:
        orm_mode = True
