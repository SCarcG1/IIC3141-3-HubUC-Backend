from app.schemas.weekday import Weekday
from datetime import datetime, time
from pydantic import BaseModel


class WeeklyTimeblockBase(BaseModel):
    weekday: Weekday
    start_hour: time
    end_hour: time
    valid_from: datetime
    valid_until: datetime

    class Config:
        from_attributes = True


class WeeklyTimeblockCreate(WeeklyTimeblockBase):
    pass


class WeeklyTimeblockOut(WeeklyTimeblockBase):
    id: int
