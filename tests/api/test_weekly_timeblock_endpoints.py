from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.user import User, UserRole
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.reservation import ReservationStatus
from app.schemas.single_timeblock import SingleTimeblock
from app.schemas.weekday import Weekday
from app.schemas.weekly_timeblock import (
    WeeklyTimeblockBase,
    WeeklyTimeblockOut
)
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
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.tutor = User(
            email="tutor@example.com",
            password="tutor_password",
            name="Tutor User",
            role="tutor"
        )
        async with SessionLocal() as session:
            session.add_all([self.tutor])
            await session.commit()
            await session.refresh(self.tutor)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_post_weekly_timeblock(self):
        # Arrange:
        weekly_timeblock_json_data = {
            "weekday": "Monday",
            "start_hour": "09:00",
            "end_hour": "17:00",
            "valid_from": "2023-10-01",
            "valid_until": "2023-12-31",
            "user_id": self.tutor.id
        }
        # Act:
        self.app.post(
            url="/weekly-timeblocks",
            json=weekly_timeblock_json_data,
            headers=get_auth_header_for_tests(
                self.tutor.email,
                self.tutor.password,
                self.tutor.id
            )
        )
        # Assert:
        async with SessionLocal() as session:
            result = await session.execute(select(WeeklyTimeblock))
        db_timeblock = result.scalars().first()
        db_timeblock_data = WeeklyTimeblockBase.model_validate(db_timeblock)
        expected_weekly_timeblock_data = WeeklyTimeblockBase.model_validate(
            weekly_timeblock_json_data
        )
        self.assertEqual(db_timeblock_data, expected_weekly_timeblock_data)

    async def test_get_all_weekly_timeblocks_of_user(self):
        # Arrange:
        db_timeblocks = await self.__add_timeblocks_to_the_database()
        # Act:
        returned_timeblocks = self.app.get(
            f"/weekly-timeblocks/{self.tutor.id}"
        ).json()
        # Assert:
        returned_timeblock_data = [
            WeeklyTimeblockOut.model_validate(timeblock)
            for timeblock in returned_timeblocks
        ]
        expected_timeblock_data = [
            WeeklyTimeblockOut.model_validate(timeblock)
            for timeblock in db_timeblocks
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
        # Arrange:
        db_timeblocks = await self.__add_timeblocks_to_the_database()
        # Act:
        returned_timeblocks = self.app.get(
            f"/weekly-timeblocks/{self.tutor.id}?on_date=2025-06-02",
        ).json()  # A valid Monday
        # Assert: only the first timeblock will match the on_date filter.
        returned_timeblocks_data = [
            WeeklyTimeblockOut.model_validate(timeblock)
            for timeblock in returned_timeblocks
        ]
        expected_timeblock_data = [
            WeeklyTimeblockOut.model_validate(db_timeblocks[0])
        ]
        self.assertEqual(returned_timeblocks_data, expected_timeblock_data)

    async def test_delete_weekly_timeblock(self):
        # Arrange:
        db_timeblocks = await self.__add_timeblocks_to_the_database()
        # Act:
        timeblock_id_to_delete = db_timeblocks[0].id
        self.app.delete(
            f"/weekly-timeblocks/{timeblock_id_to_delete}",
            headers=get_auth_header_for_tests(
                self.tutor.email,
                self.tutor.password,
                self.tutor.id
            )
        )
        # Assert: the timeblock should be deleted from the database.
        async with SessionLocal() as session:
            remaining_timeblocks = (await session.execute(
                select(WeeklyTimeblock)
            )).scalars().all()
        self.assertEqual(len(remaining_timeblocks), len(db_timeblocks) - 1)
        self.assertNotIn(
            timeblock_id_to_delete,
            [tb.id for tb in remaining_timeblocks]
        )


class TestTimeblockEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.course = self.app.post(
            "/courses",
            json={
                "name": "Course",
                "description": "Description.",
            }
        ).json()
        self.tutor = self.app.post(
            "/register",
            json={
                "email": "tutor@example.com",
                "name": "Tutor",
                "password": "password",
                "role": UserRole.tutor
            }
        ).json()
        self.tutor_token = self.app.post(
            "/login",
            json={
                "email": self.tutor["email"],
                "password": "password"
            }
        ).json()["access_token"]
        self.lesson = self.app.post(
            "/private-lessons",
            headers={"Authorization": f"Bearer {self.tutor_token}"},
            json={
                "course_id": self.course["id"],
                "tutor_id": self.tutor["id"],
                "price": 100,
                "description": "Description.",
            }
        ).json()
        self.weekly_timeblocks = [
            self.app.post(
                "/weekly-timeblocks",
                headers={"Authorization": f"Bearer {self.tutor_token}"},
                json={
                    "weekday": Weekday.MONDAY,
                    "start_hour": "10:00",
                    "end_hour": "11:00",
                    "valid_from": "2025-07-01",
                    "valid_until": "2025-07-31",
                }
            ).json(),
            self.app.post(
                "/weekly-timeblocks",
                headers={"Authorization": f"Bearer {self.tutor_token}"},
                json={
                    "weekday": Weekday.MONDAY,
                    "start_hour": "11:00",
                    "end_hour": "12:00",
                    "valid_from": "2025-07-01",
                    "valid_until": "2025-07-31",
                }
            ).json(),
        ]
        self.student = self.app.post(
            "/register",
            json={
                "email": "student@example.com",
                "name": "Student",
                "password": "password",
                "role": UserRole.student
            }
        ).json()
        self.student_token = self.app.post(
            "/login",
            json={
                "email": self.student["email"],
                "password": "password"
            }
        ).json()["access_token"]

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_when_there_are_no_accepted_reservations(self):
        # ACT:
        blocks = self.app.get(
            f"/timeblocks/{self.tutor['id']}",
            params={"on_date": "2025-07-14"}
        ).json()
        # ASSERT: all timeblocks should be returned for the given date.
        blocks = [
            SingleTimeblock.model_validate(b)
            for b in blocks
        ]
        for block in blocks:
            block.weekday_index = None
        expected_blocks = [
            SingleTimeblock.model_validate(b)
            for b in self.weekly_timeblocks
        ]
        self.assertEqual(blocks, expected_blocks)

    async def test_when_there_are_accepted_reservations(self):
        # ARRANGE: create and accept a reservation
        # that overlaps with the first timeblock.
        reservation = self.app.post(
            f"/reservations/lesson/{self.lesson['id']}",
            headers={"Authorization": f"Bearer {self.student_token}"},
            params={
                "start_time": "2025-07-14T10:00:00",
                "end_time": "2025-07-14T11:00:00",
            }
        ).json()
        self.app.patch(
            f"/reservations/tutor/{reservation['id']}",
            headers={"Authorization": f"Bearer {self.tutor_token}"},
            json={"status": ReservationStatus.ACCEPTED}
        )
        # ACT:
        blocks = self.app.get(
            f"/timeblocks/{self.tutor['id']}",
            params={"on_date": "2025-07-14"}
        ).json()
        print("DELETE LATER:", blocks)
        # ASSERT: only the second block should have been returned,
        # as there is a reservation during the first one.
        blocks = [
            SingleTimeblock.model_validate(b)
            for b in blocks
        ]
        for block in blocks:
            block.weekday_index = None
        expected_blocks = [
            SingleTimeblock.model_validate(self.weekly_timeblocks[1])
        ]
        self.assertEqual(blocks, expected_blocks)
