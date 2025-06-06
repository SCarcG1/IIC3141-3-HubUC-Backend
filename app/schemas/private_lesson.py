from pydantic import BaseModel
from datetime import datetime

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
