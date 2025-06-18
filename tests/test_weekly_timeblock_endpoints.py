from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekday import Weekday
from app.schemas.weekly_timeblock import WeeklyTimeblockBase, WeeklyTimeblockOut
from datetime import datetime, time
from fastapi.testclient import TestClient
from sqlalchemy import select
from tests.auth_for_tests import get_auth_header_for_tests
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from unittest import IsolatedAsyncioTestCase


app.dependency_overrides[get_db] = get_db_for_tests


class TestWeeklyTimeblockEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        self.tutor = User(
            email="tutor@example.com",
            password="tutor_password",
            name="Tutor User",
            role="tutor"
        )
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            session.add_all([self.tutor])
            await session.commit()
            await session.refresh(self.tutor)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_post_weekly_timeblock(self):
        weekly_timeblock_json_data = {
            "weekday": "Monday",
            "start_hour": "09:00",
            "end_hour": "17:00",
            "valid_from": "2023-10-01",
            "valid_until": "2023-12-31",
            "user_id": self.tutor.id
        }
        expected_weekly_timeblock_data = WeeklyTimeblockBase.model_validate(weekly_timeblock_json_data)

        self.app.post(
            url="/weekly-timeblocks",
            json=weekly_timeblock_json_data,
            headers=get_auth_header_for_tests(
                self.tutor.email,
                self.tutor.password,
                self.tutor.id
            )
        )

        async with SessionLocal() as session:
            result = await session.execute(select(WeeklyTimeblock))
        db_timeblock = result.scalars().first()
        db_timeblock_data = WeeklyTimeblockBase.model_validate(db_timeblock)
        self.assertEqual(db_timeblock_data, expected_weekly_timeblock_data)

    # async def test_post_weekly_timeblock_without_jwt(self):
    #     self.assertTrue(False)

    # async def test_post_weekly_timeblock_with_invalid_jwt(self):
    #     self.assertTrue(False)
    
    async def test_get_all_weekly_timeblocks_of_user(self):
        db_timeblocks = await self.__add_timeblocks_to_the_database()
        expected_timeblock_data = [
            WeeklyTimeblockOut.model_validate(timeblock) for timeblock in db_timeblocks
        ]

        returned_timeblocks = self.app.get(f"/weekly-timeblocks/{self.tutor.id}").json()

        returned_timeblock_data = [
            WeeklyTimeblockOut.model_validate(timeblock) for timeblock in returned_timeblocks
        ]
        self.assertEqual(returned_timeblock_data, expected_timeblock_data)

    async def __add_timeblocks_to_the_database(self):
        timeblocks = [
            WeeklyTimeblock(
                weekday=Weekday.MONDAY,
                start_hour=time(9, 0),
                end_hour=time(17, 0),
                valid_from=datetime(2025, 6, 1),
                valid_until=datetime(2025, 6, 30),
                user_id=self.tutor.id
            ),
            WeeklyTimeblock(
                weekday=Weekday.TUESDAY,
                start_hour=time(10, 0),
                end_hour=time(18, 0),
                valid_from=datetime(2025, 6, 2),
                valid_until=datetime(2025, 6, 29),
                user_id=self.tutor.id
            )
        ]
        async with SessionLocal() as session:
            session.add_all(timeblocks)
            await session.commit()
            for timeblock in timeblocks:
                await session.refresh(timeblock)
        return timeblocks

    async def test_get_weekly_timeblocks_of_user_with_on_date_filter(self):
        db_timeblocks = await self.__add_timeblocks_to_the_database()
        # Only the first timeblock will match the on_date filter:
        expected_timeblock_data = [WeeklyTimeblockOut.model_validate(db_timeblocks[0])]

        returned_timeblocks = self.app.get(
            f"/weekly-timeblocks/{self.tutor.id}?on_date=2025-06-02",  # A valid Monday
        ).json()

        returned_timeblocks_data = [
            WeeklyTimeblockOut.model_validate(timeblock) for timeblock in returned_timeblocks
        ]
        self.assertEqual(returned_timeblocks_data, expected_timeblock_data)

