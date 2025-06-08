from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.user import User
from app.schemas.course import CourseOut
from app.schemas.private_lesson import PrivateLessonExtendedOut
from app.schemas.user import UserOut
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select
from tests.auth_for_tests import get_auth_header_for_tests
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
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

    async def test_get_all_private_lessons(self):
        db_private_lessons = await self.__add_example_private_lessons_to_the_db(2)
        response_body = self.app.get("/private-lessons/").json()
        for i in range(len(db_private_lessons)):
            expected_private_lesson = db_private_lessons[i]
            actual_private_lesson = PrivateLessonExtendedOut.model_validate(response_body[i])
            self.assertEqual(actual_private_lesson.id, expected_private_lesson.id)
            self.assertEqual(actual_private_lesson.course_id, expected_private_lesson.course_id)
            self.assertEqual(actual_private_lesson.end_time, expected_private_lesson.end_time)
            self.assertEqual(actual_private_lesson.price, expected_private_lesson.price)
            self.assertEqual(actual_private_lesson.start_time, expected_private_lesson.start_time)
            self.assertEqual(actual_private_lesson.tutor_id, expected_private_lesson.tutor_id)

    async def __add_example_private_lessons_to_the_db(self, number_of_lessons_to_add: int):
        private_lessons = [
            PrivateLesson(
                course_id=self.example_course.id,
                end_time=datetime(2023, 10, 1, 11, 0, 0),
                price=10000,
                start_time=datetime(2023, 10, 1, 10, 0, 0),
                tutor_id=self.example_tutor.id,
            ) for _ in range(number_of_lessons_to_add)
        ]
        async with SessionLocal() as session:
            session.add_all(private_lessons)
            await session.commit()
            for lesson in private_lessons:
                await session.refresh(lesson)
        return private_lessons

    async def test_that_post_private_lesson_creates_the_lesson_in_the_db(self):
        private_lesson_json = {
            "course_id": self.example_course.id,
            "end_time": "2023-10-01T11:00:00",
            "price": 10000,
            "start_time": "2023-10-01T10:00:00",
            "tutor_id": self.example_tutor.id,
        }
        self.app.post(
            url="/private-lessons/",
            json=private_lesson_json,
            headers=get_auth_header_for_tests(
                email=self.example_tutor.email,
                role=self.example_tutor.role,
                user_id=self.example_tutor.id
            )
        ).json()
        query = select(PrivateLesson)
        async with SessionLocal() as session:
            result = await session.execute(query)
        db_private_lesson = result.scalars().one_or_none()
        self.assertEqual(db_private_lesson.course_id, private_lesson_json["course_id"])
        self.assertEqual(db_private_lesson.end_time, datetime.fromisoformat(private_lesson_json["end_time"]))
        self.assertEqual(db_private_lesson.price, private_lesson_json["price"])
        self.assertEqual(db_private_lesson.start_time, datetime.fromisoformat(private_lesson_json["start_time"]))
        self.assertEqual(db_private_lesson.tutor_id, private_lesson_json["tutor_id"])
