from app.database import Base
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekday import Weekday
from app.utilities.weekly_timeblocks import (
    does_weekly_timeblock_contain_date_time,
)
from datetime import datetime
from tests.db_for_tests import db_engine, SessionLocal
from unittest import IsolatedAsyncioTestCase


class TestDoesWeeklyTimeblockContainDatetime(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        tutor = User(
            email="",
            password="",
            name="Test Tutor",
            role="tutor",
        )
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            session.add(tutor)
            await session.commit()
            await session.refresh(tutor)
        self.weekly_timeblock = WeeklyTimeblock(
            user_id=tutor.id,
            valid_from=datetime(2025, 6, 2, 0, 0, 0),
            weekday=Weekday.MONDAY,
            start_hour=9,
            end_hour=17,
            valid_until=datetime(2025, 6, 15, 23, 59, 59),
        )

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def test_when_weekly_timeblock_does_contain_datetime(self):
        date_time = datetime(2025, 6, 9, 10, 0, 0)  # A Monday
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertTrue(result)
    
    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_valid_from_date(self):
        date_time = datetime(2025, 5, 26)  # A Monday, but before valid_from
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)

    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_weekday(self):
        date_time = datetime(2025, 6, 10, 10, 0, 0)  # Inside valid dates, but a Tuesday
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)

    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_start_hour(self):
        date_time = datetime(2025, 6, 9, 8, 59, 59)  # A valid Monday, but before start_hour
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)

    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_end_hour(self):
        date_time = datetime(2025, 6, 9, 18, 0, 0) # A valid Monday, but after end_hour
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
    
    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_end_hour_edge_case(self):
        date_time = datetime(2025, 6, 9, 17, 0, 1)  # A valid Monday, but a second after end_hour
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
    
    def test_when_weekly_timeblock_does_not_contain_datetime_due_to_valid_until_date(self):
        date_time = datetime(2025, 6, 16, 0, 0, 0)  # A Monday, but after valid_until
        result = does_weekly_timeblock_contain_date_time(self.weekly_timeblock, date_time)
        self.assertFalse(result)
