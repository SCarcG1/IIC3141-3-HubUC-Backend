from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models import course, private_lesson, reservation, review, user
from app.models.user import User
from datetime import datetime
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase


app.dependency_overrides[get_db] = get_db_for_tests


class TestPrivateLessonEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        self.example_course = Course(
            name="Test Course",
            description="This is a test course.",
        )
        self.example_student = User(
            email="student@example.com",
            password="student_password",
            name="Student User",
            role="student"
        )
        self.example_tutor = User(
            email="tutor@example.com",
            password="tutor_password",
            name="Tutor User",
            role="tutor"
        )
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            session.add_all([self.example_course, self.example_student, self.example_tutor])
            await session.commit()
            await session.refresh(self.example_course)
            await session.refresh(self.example_student)
            await session.refresh(self.example_tutor)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_getting_all_private_lessons(self):
        private_lesson_1 = PrivateLesson(
            tutor_id=self.example_tutor.id,
            course_id=self.example_course.id,
            start_time=datetime(2023, 10, 1, 10, 0),
            end_time=datetime(2023, 10, 1, 11, 0),
            price=1,
        )
        private_lesson_2 = PrivateLesson(
            tutor_id=self.example_tutor.id,
            course_id=self.example_course.id,
            start_time=datetime(2023, 10, 2, 10, 0),
            end_time=datetime(2023, 10, 2, 11, 0),
            price=2,
        )
        async with SessionLocal() as session:
            session.add_all((private_lesson_1, private_lesson_2))
            await session.commit()
            await session.refresh(private_lesson_1)
            await session.refresh(private_lesson_2)
        response_body = self.app.get("/private-lessons/").json()
        expected_response_body = [
            {
                "id": private_lesson_1.id,
                "tutor_id": private_lesson_1.tutor_id,
                "course_id": private_lesson_1.course_id,
                "start_time": private_lesson_1.start_time.isoformat(),
                "end_time": private_lesson_1.end_time.isoformat(),
                "price": private_lesson_1.price,
            },
            {
                "id": private_lesson_2.id,
                "tutor_id": private_lesson_2.tutor_id,
                "course_id": private_lesson_2.course_id,
                "start_time": private_lesson_2.start_time.isoformat(),
                "end_time": private_lesson_2.end_time.isoformat(),
                "price": private_lesson_2.price,
            }
        ]
        self.assertEqual(response_body, expected_response_body)
