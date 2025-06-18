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
    
    async def test_get_weekly_timeblocks_of_user(self):
        async with SessionLocal() as session:
            db_timeblock_0 = WeeklyTimeblock(
                weekday=Weekday.MONDAY,
                start_hour=time(9, 0),
                end_hour=time(17, 0),
                valid_from=datetime(2023, 10, 1),
                valid_until=datetime(2023, 12, 31),
                user_id=self.tutor.id
            )
            db_timeblock_1 = WeeklyTimeblock(
                weekday=Weekday.TUESDAY,
                start_hour=time(10, 0),
                end_hour=time(18, 0),
                valid_from=datetime(2023, 10, 1),
                valid_until=datetime(2023, 12, 31),
                user_id=self.tutor.id
            )
            session.add_all([db_timeblock_0, db_timeblock_1])
            await session.commit()
            await session.refresh(db_timeblock_0)
            await session.refresh(db_timeblock_1)
        expected_timeblock_0_data = WeeklyTimeblockOut.model_validate(db_timeblock_0)
        expected_timeblock_1_data = WeeklyTimeblockOut.model_validate(db_timeblock_1)

        returned_timeblocks = self.app.get(f"/weekly-timeblocks/{self.tutor.id}").json()

        returned_timeblocks_data = [
            WeeklyTimeblockOut.model_validate(timeblock) for timeblock in returned_timeblocks
        ]
        self.assertEqual(returned_timeblocks_data[0], expected_timeblock_0_data)
        self.assertEqual(returned_timeblocks_data[1], expected_timeblock_1_data)
