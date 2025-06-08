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
