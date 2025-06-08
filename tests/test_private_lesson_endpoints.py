from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.user import User
from app.schemas.course import CourseOut
from app.schemas.user import UserOut
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

    async def test_get_all_private_lessons(self):
        private_lessons = await self.__add_example_private_lessons_to_the_db(2)
        response_body = self.app.get("/private-lessons/").json()

        example_course_out = CourseOut.model_validate(self.example_course).model_dump()
        example_tutor_out = UserOut.model_validate(self.example_tutor).model_dump()
        expected_response_body = [
            {
                "course": example_course_out,
                "course_id": private_lessons[0].course_id,
                "end_time": private_lessons[0].end_time.isoformat(),
                "id": private_lessons[0].id,
                "price": private_lessons[0].price,
                "start_time": private_lessons[0].start_time.isoformat(),
                "tutor_id": private_lessons[0].tutor_id,
                "tutor": example_tutor_out
            },
            {
                "course": example_course_out,
                "course_id": private_lessons[1].course_id,
                "end_time": private_lessons[1].end_time.isoformat(),
                "id": private_lessons[1].id,
                "price": private_lessons[1].price,
                "start_time": private_lessons[1].start_time.isoformat(),
                "tutor_id": private_lessons[1].tutor_id,
                "tutor": example_tutor_out
            }
        ]

        self.assertEqual(response_body, expected_response_body)
    
    async def __add_example_private_lessons_to_the_db(self, number_of_lessons_to_add: int = 1):
        private_lessons = [PrivateLesson(
                course_id=self.example_course.id,
                end_time=datetime(2023, 10, 1, 11, 0),
                price=1 + i,
                start_time=datetime(2023, 10, 1, 10, 0),
                tutor_id=self.example_tutor.id,
            )  for i in range(number_of_lessons_to_add)]
        async with SessionLocal() as session:
            session.add_all(private_lessons)
            await session.commit()
            for lesson in private_lessons:
                await session.refresh(lesson)
        return private_lessons
