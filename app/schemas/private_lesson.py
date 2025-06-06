from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class PrivateLessonBase(BaseModel):
    tutor_id: int
    course_id: int
    start_time: datetime
    end_time: datetime
    price: int

class PrivateLessonOut(PrivateLessonBase):
    id: int

    class Config:
        orm_mode = True

class PrivateLessonCreate(PrivateLessonBase):
    pass

class PrivateLessonUpdate(BaseModel):
    tutor_id: Optional[int]
    course_id: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    price: Optional[int]

    class Config:
        orm_mode = True