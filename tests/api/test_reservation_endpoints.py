from app.api.routes import get_db
from app.crud.reservation import create_reservation
from app.database import Base
from app.main import app
from app.models import course, private_lesson, reservation, review, user
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.reservation import (
    ReservationBase,
    ReservationCreate,
    ReservationOut,
    ReservationStatus
)
from app.schemas.user import UserRole
from app.schemas.weekday import Weekday
from app.schemas.weekly_timeblock import WeeklyTimeblockCreate
from datetime import datetime, time
from fastapi.testclient import TestClient
from jose import jwt
from tests.auth_for_tests import get_auth_header_for_tests
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from unittest import IsolatedAsyncioTestCase
import os


app.dependency_overrides[get_db] = get_db_for_tests
SECRET_KEY = os.getenv("JWT_SECRET", "test_secret")  # define esto en tu .env

def generate_token(user_id: int, role: str):
    return jwt.encode({"user_id": user_id, "role": role, "sub": f"{role}@test.com"}, SECRET_KEY, algorithm="HS256")


class TestReservationEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.course = Course(name="Test Course", description="Course desc")
        self.student = User(email="student@test.com", password="pw", name="Student", role="student")
        self.tutor = User(email="tutor@test.com", password="pw", name="Tutor", role="tutor")
        async with SessionLocal() as session:
            session.add_all([self.course, self.student, self.tutor])
            await session.commit()
            await session.refresh(self.course)
            await session.refresh(self.student)
            await session.refresh(self.tutor)
        self.lesson = PrivateLesson(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=10000
        )
        async with SessionLocal() as session:
            session.add(self.lesson)
            await session.commit()
            await session.refresh(self.lesson)
        self.weekly_timeblock = WeeklyTimeblock(
            user_id=self.tutor.id,
            **WeeklyTimeblockCreate(
                weekday=Weekday.MONDAY,
                start_hour=time(9),
                end_hour=time(17),
                valid_from=datetime(2025, 6, 1),
                valid_until=datetime(2025, 6, 30),
            ).model_dump()
        )
        async with SessionLocal() as session:
            session.add(self.weekly_timeblock)
            await session.commit()
            await session.refresh(self.weekly_timeblock)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_post_reservation(self):
        response_body = self.app.post(
            url=f"/reservations/lesson/{self.lesson.id}",
            params={
                "start_time": "2025-06-02T10:00:00",
                "end_time": "2025-06-02T11:00:00"
            },
            headers=get_auth_header_for_tests(
                email=self.student.email,
                role=UserRole.student,
                user_id=self.student.id
            ),
        ).json()
        returned_reservation = ReservationBase.model_validate(response_body)
        expected_reservation = ReservationBase(
            private_lesson_id=self.lesson.id,
            student_id=self.student.id,
            status=ReservationStatus.PENDING,
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        self.assertEqual(returned_reservation, expected_reservation)

    async def test_get_all_reservations_endpoint(self):
        async with SessionLocal() as db_session:
            await create_reservation(
                db_session,
                ReservationCreate(
                    student_id=self.student.id,
                    private_lesson_id=self.lesson.id,
                    status=ReservationStatus.PENDING,
                    start_time=datetime(2025, 6, 2, 10, 0, 0),
                    end_time=datetime(2025, 6, 2, 11, 0, 0)
                ))
            await create_reservation(
                db_session,
                ReservationCreate(
                    student_id=self.student.id,
                    private_lesson_id=self.lesson.id,
                    status=ReservationStatus.PENDING,
                    start_time=datetime(2025, 6, 2, 10, 0, 0),
                    end_time=datetime(2025, 6, 2, 11, 0, 0)
                ))
        resp = self.app.get("/reservations")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    async def test_get_student_reservations_endpoint(self):
        # Usar endpoint POST + GET /reservations/student
        token_s = generate_token(self.student.id, "student")
        self.app.post(f"/reservations/lesson/{self.lesson.id}", headers={"Authorization": f"Bearer {token_s}"})
        resp = self.app.get("/reservations/student", headers={"Authorization": f"Bearer {token_s}"})
        self.assertEqual(resp.status_code, 200)
        arr = resp.json()
        self.assertTrue(all(r["student_id"] == self.student.id for r in arr))

    async def test_get_tutor_reservations_endpoint(self):
        # Crear reserva y luego GET /reservations/tutor
        token_s = generate_token(self.student.id, "student")
        self.app.post(
            url=f"/reservations/lesson/{self.lesson.id}",
            params={
                "start_time": "2025-06-02T10:00:00",
                "end_time": "2025-06-02T11:00:00"
            },
            headers={"Authorization": f"Bearer {token_s}"}
        )
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.get("/reservations/tutor", headers={"Authorization": f"Bearer {token_t}"})
        self.assertEqual(resp.status_code, 200)
        arr = resp.json()
        # cada reserva incluye private_lesson.tutor_id == tutor.id
        self.assertTrue(all(r["private_lesson"]["tutor"]["id"] == self.tutor.id for r in arr))

    async def test_update_reservation_endpoint(self):
        # Crear y actualizar vía PUT
        token_s = generate_token(self.student.id, "student")
        created = self.app.post(
            url=f"/reservations/lesson/{self.lesson.id}",
            params={
                "start_time": "2025-06-02T10:00:00",
                "end_time": "2025-06-02T11:00:00"
            },
            headers={"Authorization": f"Bearer {token_s}"}
        ).json()
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.put(
            f"/reservations/{created['id']}",
            json={"status": "accepted"},
            headers={"Authorization": f"Bearer {token_t}"}
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "accepted")

    async def test_delete_reservation_endpoint(self):
        # Crear + DELETE
        token_s = generate_token(self.student.id, "student")
        created = self.app.post(
            url=f"/reservations/lesson/{self.lesson.id}",
            params={
                "start_time": "2025-06-02T10:00:00",
                "end_time": "2025-06-02T11:00:00"
            },
            headers={"Authorization": f"Bearer {token_s}"}
        ).json()
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.delete(f"/reservations/{created['id']}", headers={"Authorization": f"Bearer {token_t}"})
        self.assertEqual(resp.status_code, 200)
        # Ahora GET /reservations no lo incluye
        allr = self.app.get("/reservations").json()
        self.assertFalse(any(r["id"] == created["id"] for r in allr))
