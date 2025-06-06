from datetime import datetime
from pydantic import BaseModel

class PrivateLessonCreate(BaseModel):
    tutor_id: int
    course_id: int
    start_time: datetime
    end_time: datetime
    price: int
