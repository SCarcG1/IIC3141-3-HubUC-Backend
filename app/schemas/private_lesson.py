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
    description: Optional[str] = None


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
    tutor_id: Optional[int] = None
    course_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    price: Optional[int] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class PrivateLessonPage(BaseModel):
    page: int
    page_size: int
    results: list[PrivateLessonOut]
    total: int
