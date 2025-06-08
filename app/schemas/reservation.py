from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum as PythonEnum

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