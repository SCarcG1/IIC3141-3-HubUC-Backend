from app.schemas.course import CourseOut
from app.schemas.user import UserOut
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
        from_attributes = True
        orm_mode = True


class PrivateLessonExtendedOut(PrivateLessonOut):
    course: CourseOut
    tutor: UserOut


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

class PrivateLessonPage(BaseModel):
    page: int
    page_size: int
    results: list[PrivateLessonOut]
    total: int
