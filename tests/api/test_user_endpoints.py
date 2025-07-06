from app.auth.auth_handler import decode_token
from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.schemas.course import CourseCreate
from app.schemas.private_lesson import OfferStatus, PrivateLessonCreate
from app.schemas.reservation import ReservationStatus
from app.schemas.user import UserCreate, UserLogin, UserRole
from app.utilities.weekdays import map_int_weekday_to_enum_weekday
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from tests.db_for_tests import db_engine, get_db_for_tests
from unittest import IsolatedAsyncioTestCase


app.dependency_overrides[get_db] = get_db_for_tests


class TestDeleteTutor(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await super().asyncSetUp()
        self.course = self.app.post(
            url="/courses",
            json=CourseCreate(
                name="Course",
                description="Description."
            ).model_dump()
        ).json()
        self.tutor = self.app.post(
            url="/register",
            json=UserCreate(
                email="tutor@example.com",
                name="Tutor",
                number="+56912345678",
                password="password",
                role=UserRole.tutor
            ).model_dump()
        ).json()
        self.tutor_token = self.app.post(
            url="/login",
            json=UserLogin(
                email="tutor@example.com",
                password="password"
            ).model_dump()
        ).json()["access_token"]
        self.student = self.app.post(
            url="/register",
            json=UserCreate(
                email="student@example.com",
                name="Student",
                number="+56987654321",
                password="password",
                role=UserRole.student
            ).model_dump()
        ).json()
        self.student_token = self.app.post(
            url="/login",
            json=UserLogin(
                email="student@example.com",
                password="password"
            ).model_dump()
        ).json()["access_token"]
        self.lesson = self.app.post(
            url="/private-lessons",
            headers={"Authorization": f"Bearer {self.tutor_token}"},
            json=PrivateLessonCreate(
                tutor_id=decode_token(self.tutor_token)["id"],
                course_id=self.course["id"],
                price=10000,
                description="Description.",
                offer_status=OfferStatus.OPEN
            ).model_dump()
        ).json()
        yesterday = datetime.today() - timedelta(days=1)
        yesterday = datetime(yesterday.year, yesterday.month, yesterday.day)
        self.weekly_timeblock = self.app.post(
            url="/weekly-timeblocks",
            headers={"Authorization": f"Bearer {self.tutor_token}"},
            json={
                "weekday": map_int_weekday_to_enum_weekday(
                    yesterday.weekday()
                ),
                "start_hour": "09:00",
                "end_hour": "17:00",
                "valid_from": (yesterday - timedelta(days=30)).isoformat(),
                "valid_until": (yesterday + timedelta(days=30)).isoformat()
            }
        ).json()
        reservation = self.app.post(
            f"/reservations/lesson/{self.lesson['id']}",
            headers={"Authorization": f"Bearer {self.student_token}"},
            params={
                "start_time": datetime(
                    yesterday.year, yesterday.month, yesterday.day, 10
                ).isoformat(),
                "end_time": datetime(
                    yesterday.year, yesterday.month, yesterday.day, 11
                ).isoformat()
            }
        ).json()
        self.completed_reservation = self.app.patch(
            url=f"/reservations/tutor/{reservation['id']}",
            headers={"Authorization": f"Bearer {self.tutor_token}"},
            json={
                "private_lesson_id": None,
                "student_id": None,
                "status": ReservationStatus.ACCEPTED
            }
        ).json()
        next_week = yesterday + timedelta(days=7)
        self.uncompleted_reservation = self.app.post(
            f"/reservations/lesson/{self.lesson['id']}",
            headers={"Authorization": f"Bearer {self.student_token}"},
            params={
                "start_time": datetime(
                    next_week.year, next_week.month, next_week.day, 12
                ).isoformat(),
                "end_time": datetime(
                    next_week.year, next_week.month, next_week.day, 13
                ).isoformat()
            }
        ).json()
        self.review = self.app.post(
            "/reviews",
            headers={"Authorization": f"Bearer {self.student_token}"},
            json={
                "reservation_id": self.completed_reservation["id"],
                "content": "Content.",
                "rating": 5,
            }
        ).json()

    def act(self):
        return self.app.delete(
            f"/users/{self.tutor['id']}",
            headers={"Authorization": f"Bearer {self.tutor_token}"}
        )

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def test_that_course_remains_unchanged(self):
        self.act()
        course_after = self.app.get(f"/courses/{self.course['id']}").json()
        self.assertEqual(self.course, course_after)

    def test_that_tutor_does_not_exist(self):
        self.act()
        status_code = self.app.get(f"/users/{self.tutor['id']}").status_code
        self.assertEqual(status_code, status.HTTP_404_NOT_FOUND)

    def test_that_student_remains_unchanged(self):
        self.act()
        student_after = self.app.get(f"/users/{self.student['id']}").json()
        self.assertEqual(self.student, student_after)

    def test_that_private_lesson_gets_closed(self):
        self.act()
        lesson_after = self.app.get(
            f"/private-lessons/{self.lesson['id']}"
        ).json()
        self.assertEqual(
            lesson_after["offer_status"],
            OfferStatus.CLOSED
        )

    def test_that_weekly_timeblock_does_not_exist(self):
        self.act()
        weekly_timeblocks_after = self.app.get(
            f"/weekly-timeblocks/{self.tutor['id']}"
        ).json()
        self.assertEqual(len(weekly_timeblocks_after), 0)

    def test_that_completed_reservation_remains_unchanged_except_for_tutor_id(
        self
    ):
        self.act()
        reservations_after = self.app.get(
            url="/reservations/student",
            headers={"Authorization": f"Bearer {self.student_token}"},
        ).json()
        completed_reservation_after = reservations_after[0]
        self.assertEqual(
            self.completed_reservation["status"],
            completed_reservation_after["status"]
        )

    def test_that_uncompleted_reservation_gets_rejected(self):
        '''
        A reservation is "uncompleted" when either it's "pending"
        or it hasn't started yet.
        '''
        self.act()
        reservations_after = self.app.get(
            url="/reservations/student",
            headers={"Authorization": f"Bearer {self.student_token}"},
        ).json()
        uncompleted_reservation_after = reservations_after[1]
        self.assertEqual(
            uncompleted_reservation_after["status"],
            ReservationStatus.REJECTED
        )

    def test_that_review_gets_deleted(self):
        self.act()
        status_code = self.app.get(
            url=f"/reviews/{self.review['id']}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        ).status_code
        self.assertEqual(status_code, status.HTTP_404_NOT_FOUND)
