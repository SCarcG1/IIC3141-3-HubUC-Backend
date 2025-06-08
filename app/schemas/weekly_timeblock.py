from app.schemas.weekday import Weekday
from datetime import datetime
from pydantic import BaseModel


class WeeklyTimeblockBase(BaseModel):
    weekday: Weekday
    start_hour: int
    end_hour: int
    valid_from: datetime
    valid_until: datetime


class WeeklyTimeblockCreate(WeeklyTimeblockBase):
    pass


class WeeklyTimeblockOut(WeeklyTimeblockBase):
    id: int
