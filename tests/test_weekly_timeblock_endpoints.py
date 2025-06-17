from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekly_timeblock import WeeklyTimeblockOut
from datetime import datetime
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
        expected_weekday = "Monday"
        expected_start_hour = 9
        expected_end_hour = 17
        expected_valid_from = datetime(2023, 10, 1, 0, 0, 0)
        expected_valid_until = datetime(2023, 12, 31, 23, 59, 59)
        expected_user_id = self.tutor.id

        self.app.post(
            url="/weekly-timeblocks",
            json={
                "weekday": expected_weekday,
                "start_hour": expected_start_hour,
                "end_hour": expected_end_hour,
                "valid_from": expected_valid_from.isoformat(),
                "valid_until": expected_valid_until.isoformat(),
            },
            headers=get_auth_header_for_tests(
                self.tutor.email,
                self.tutor.password,
                self.tutor.id
            )
        )

        query = select(WeeklyTimeblock)
        async with SessionLocal() as session:
            result = await session.execute(query)
        db_timeblock = result.scalars().first()
        self.assertEqual(db_timeblock.weekday, expected_weekday)
        self.assertEqual(db_timeblock.start_hour, expected_start_hour)
        self.assertEqual(db_timeblock.end_hour, expected_end_hour)
        self.assertEqual(db_timeblock.valid_from, expected_valid_from)
        self.assertEqual(db_timeblock.valid_until, expected_valid_until)
        self.assertEqual(db_timeblock.user_id, expected_user_id)

    # async def test_post_weekly_timeblock_without_jwt(self):
    #     self.assertTrue(False)

    # async def test_post_weekly_timeblock_with_invalid_jwt(self):
    #     self.assertTrue(False)
    
    async def test_get_weekly_timeblocks_of_user(self):
        async with SessionLocal() as session:
            db_timeblock_0 = WeeklyTimeblock(
                weekday="Monday",
                start_hour=9,
                end_hour=17,
                valid_from=datetime(2023, 10, 1, 0, 0, 0),
                valid_until=datetime(2023, 12, 31, 23, 59, 59),
                user_id=self.tutor.id
            )
            db_timeblock_1 = WeeklyTimeblock(
                weekday="Tuesday",
                start_hour=10,
                end_hour=18,
                valid_from=datetime(2023, 10, 1, 0, 0, 0),
                valid_until=datetime(2023, 12, 31, 23, 59, 59),
                user_id=self.tutor.id
            )
            session.add_all([db_timeblock_0, db_timeblock_1])
            await session.commit()
            await session.refresh(db_timeblock_0)
            await session.refresh(db_timeblock_1)
        expected_timeblock_0 = WeeklyTimeblockOut.model_validate(db_timeblock_0)
        expected_timeblock_1 = WeeklyTimeblockOut.model_validate(db_timeblock_1)

        returned_timeblocks = self.app.get(f"/weekly-timeblocks/{self.tutor.id}").json()

        returned_timeblocks = [WeeklyTimeblockOut.model_validate(timeblock) for timeblock in returned_timeblocks]
        self.assertEqual(returned_timeblocks[0], expected_timeblock_0)
        self.assertEqual(returned_timeblocks[1], expected_timeblock_1)
