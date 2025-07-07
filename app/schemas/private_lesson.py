from app.schemas.course import CourseOut
from app.schemas.user import UserOut
from pydantic import BaseModel
from typing import Optional


class PrivateLessonBase(BaseModel):
    tutor_id: int | None
    course_id: int
    price: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PrivateLessonOut(PrivateLessonBase):
    id: int


class PrivateLessonExtendedOut(PrivateLessonOut):
    course: CourseOut
    tutor: UserOut | None


class PrivateLessonCreate(PrivateLessonBase):
    pass


class PrivateLessonUpdate(BaseModel):
    tutor_id: Optional[int] = None
    course_id: Optional[int] = None
    price: Optional[int] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PrivateLessonPage(BaseModel):
    page: int
    page_size: int
    results: list[PrivateLessonOut]
    total: int
