from app.crud.user import create_user
from app.crud.weekly_timeblocks import create_weekly_timeblock
from app.database import Base
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.user import UserCreate, UserRole
from app.schemas.weekday import Weekday
from app.schemas.weekly_timeblock import WeeklyTimeblockCreate
from app.utilities.weekly_timeblocks import (
    does_weekly_timeblock_contain_date_time,
)
from datetime import datetime, time
from tests.db_for_tests import db_engine, SessionLocal
from unittest import IsolatedAsyncioTestCase


class TestDoesWeeklyTimeblockContainDatetime(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            self.tutor = await create_user(
                session,
                UserCreate(
                    email="tutor@example.com",
                    name="Tutor User",
                    password="tutor_password",
                    role=UserRole.tutor
                )
            )
            self.weekly_timeblock = await create_weekly_timeblock(
                session,
                WeeklyTimeblockCreate(
                    weekday=Weekday.MONDAY,
                    start_hour=time(9),
                    end_hour=time(17),
                    valid_from=datetime(2025, 6, 1, 0, 0),
                    valid_until=datetime(2025, 6, 30, 23, 59)
                ),
                user_id=self.tutor.id
            )

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def test_when_weekly_timeblock_does_contain_datetime(self):
        date_time = datetime(2025, 6, 2, 9, 0)
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertTrue(result)
    
    async def test_when_weekly_timeblock_does_not_contain_datetime_because_of_valid_from(self):
        date_time = datetime(2025, 5, 26, 9, 0)  # A Monday, but before valid_from
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
    
    async def test_when_weekly_timeblock_does_not_contain_datetime_because_of_weekday(self):
        date_time = datetime(2025, 6, 3, 9, 0)  # Inside valid range, but a Tuesday
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
    
    async def test_when_weekly_timeblock_does_not_contain_datetime_because_of_start_hour(self):
        date_time = datetime(2025, 6, 2, 8, 59)  # A Monday, but before start_hour
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)

    async def test_when_weekly_timeblock_does_not_contain_datetime_because_of_end_hour(self):
        date_time = datetime(2025, 6, 2, 17, 1)  # A Monday, but after end_hour
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)

    async def test_when_weekly_timeblock_does_not_contain_datetime_because_of_valid_until(self):
        date_time = datetime(2025, 7, 1, 0, 0)  # A Monday, but after valid_until 
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
