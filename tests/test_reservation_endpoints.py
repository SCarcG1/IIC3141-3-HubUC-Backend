from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.user import User
from datetime import datetime, timedelta
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from fastapi.testclient import TestClient
from jose import jwt
import os
from unittest import IsolatedAsyncioTestCase
from app.models import course, private_lesson, reservation, review, user


app.dependency_overrides[get_db] = get_db_for_tests
SECRET_KEY = os.getenv("JWT_SECRET", "test_secret")  # define esto en tu .env

def generate_token(user_id: int, role: str):
    return jwt.encode({"user_id": user_id, "role": role, "sub": f"{role}@test.com"}, SECRET_KEY, algorithm="HS256")


class TestReservationEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        self.course = Course(name="Test Course", description="Course desc")
        self.student = User(email="student@test.com", password="pw", name="Student", role="student")
        self.tutor = User(email="tutor@test.com", password="pw", name="Tutor", role="tutor")

        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with SessionLocal() as session:
            session.add_all([self.course, self.student, self.tutor])
            await session.commit()
            await session.refresh(self.course)
            await session.refresh(self.student)
            await session.refresh(self.tutor)

        self.lesson = PrivateLesson(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            price=10000
        )
        async with SessionLocal() as session:
            session.add(self.lesson)
            await session.commit()
            await session.refresh(self.lesson)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_create_reservation_endpoint(self):
        token = generate_token(user_id=self.student.id, role="student")
        response = self.app.post(
            f"/reservations/lesson/{self.lesson.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["student_id"] == self.student.id
        assert body["private_lesson_id"] == self.lesson.id
        assert body["status"] == "pending"

    async def test_get_all_reservations_endpoint(self):
        # Generar dos reservas por CRUD
        from app.crud.reservation import create_reservation
        from app.schemas.reservation import ReservationCreate
        async with SessionLocal() as s:
            await create_reservation(s, ReservationCreate(student_id=self.student.id, private_lesson_id=self.lesson.id,
                                                          status="pending"))
            await create_reservation(s, ReservationCreate(student_id=self.student.id, private_lesson_id=self.lesson.id,
                                                          status="pending"))
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
        self.app.post(f"/reservations/lesson/{self.lesson.id}", headers={"Authorization": f"Bearer {token_s}"})
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.get("/reservations/tutor", headers={"Authorization": f"Bearer {token_t}"})
        self.assertEqual(resp.status_code, 200)
        arr = resp.json()
        # cada reserva incluye private_lesson.tutor_id == tutor.id
        self.assertTrue(all(r["private_lesson"]["tutor"]["id"] == self.tutor.id for r in arr))

    async def test_update_reservation_endpoint(self):
        # Crear y actualizar vía PUT
        token_s = generate_token(self.student.id, "student")
        created = self.app.post(f"/reservations/lesson/{self.lesson.id}",
                                headers={"Authorization": f"Bearer {token_s}"}).json()
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.put(f"/reservations/{created['id']}", json={"status": "accepted"},
                            headers={"Authorization": f"Bearer {token_t}"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "accepted")

    async def test_delete_reservation_endpoint(self):
        # Crear + DELETE
        token_s = generate_token(self.student.id, "student")
        created = self.app.post(f"/reservations/lesson/{self.lesson.id}",
                                headers={"Authorization": f"Bearer {token_s}"}).json()
        token_t = generate_token(self.tutor.id, "tutor")
        resp = self.app.delete(f"/reservations/{created['id']}", headers={"Authorization": f"Bearer {token_t}"})
        self.assertEqual(resp.status_code, 200)
        # Ahora GET /reservations no lo incluye
        allr = self.app.get("/reservations").json()
        self.assertFalse(any(r["id"] == created["id"] for r in allr))
