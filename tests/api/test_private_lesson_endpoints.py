from app.api.routes import get_db
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.user import User
from app.schemas.private_lesson import PrivateLessonBase, PrivateLessonOut, PrivateLessonPage
from fastapi.testclient import TestClient
from sqlalchemy import select
from tests.auth_for_tests import get_auth_header_for_tests
from tests.db_for_tests import db_engine, get_db_for_tests, SessionLocal
from unittest import IsolatedAsyncioTestCase


app.dependency_overrides[get_db] = get_db_for_tests


class TestPrivateLessonEndpoints(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestClient(app)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.course = Course(
            name="Test Course",
            description="This is a test course.",
        )
        self.student = User(
            email="student@example.com",
            password="student_password",
            name="Student User",
            role="student"
        )
        self.tutor = User(
            email="tutor@example.com",
            password="tutor_password",
            name="Tutor User",
            role="tutor"
        )
        async with SessionLocal() as session:
            session.add_all([self.course, self.student, self.tutor])
            await session.commit()
            await session.refresh(self.course)
            await session.refresh(self.student)
            await session.refresh(self.tutor)

    async def asyncTearDown(self):
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_that_post_private_lesson_creates_the_lesson_in_the_db(self):
        private_lesson_json = {
            "course_id": self.course.id,
            "price": 10000,
            "tutor_id": self.tutor.id,
            "description": "This is a test private lesson."
        }
        self.app.post(
            url="/private-lessons/",
            json=private_lesson_json,
            headers=get_auth_header_for_tests(
                email=self.tutor.email,
                role=self.tutor.role,
                user_id=self.tutor.id
            )
        ).json()
        async with SessionLocal() as session:
            db_private_lesson = (await session.execute(select(PrivateLesson))).scalar_one()
        db_private_lesson = PrivateLessonBase.model_validate(db_private_lesson)
        expected_private_lesson = PrivateLessonBase.model_validate(private_lesson_json)
        self.assertEqual(db_private_lesson, expected_private_lesson)

    async def test_get_all_private_lessons(self):
        db_private_lessons = await self.__add_example_private_lessons_to_the_db(2)
        response_body = self.app.get("/private-lessons/").json()
        for i in range(len(db_private_lessons)):
            expected_private_lesson = PrivateLessonBase.model_validate(db_private_lessons[i])
            actual_private_lesson = PrivateLessonBase.model_validate(response_body[i])
            self.assertEqual(expected_private_lesson, actual_private_lesson)

    async def __add_example_private_lessons_to_the_db(self, number_of_lessons_to_add: int):
        private_lessons = [
            PrivateLesson(
                course_id=self.course.id,
                tutor_id=self.tutor.id,
                price=1 + i,
                description=f"Clase Privada sobre {self.course.name} con {self.tutor.name}",
            ) for i in range(number_of_lessons_to_add)
        ]
        async with SessionLocal() as session:
            session.add_all(private_lessons)
            await session.commit()
            for lesson in private_lessons:
                await session.refresh(lesson)
        return private_lessons

    async def test_get_private_lesson_by_id(self):
        expected_private_lesson = (await self.__add_example_private_lessons_to_the_db(1))[0]
        response_body = self.app.get(f"/private-lessons/{expected_private_lesson.id}").json()
        actual_private_lesson = PrivateLessonOut.model_validate(response_body)
        self.assertEqual(actual_private_lesson.id, expected_private_lesson.id)
        self.assertEqual(actual_private_lesson.course_id, expected_private_lesson.course_id)
        self.assertEqual(actual_private_lesson.price, expected_private_lesson.price)
        self.assertEqual(actual_private_lesson.tutor_id, expected_private_lesson.tutor_id)
        self.assertEqual(actual_private_lesson.description, expected_private_lesson.description)

    async def test_search_private_lessons(self):
        expected_total = 20
        await self.__add_example_private_lessons_to_the_db(expected_total)
        expected_page = 1
        expected_page_size = 10
        response_body = self.app.get(
            f"/private-lessons/search"
            + f"?page={expected_page}"
            + f"&page_size={expected_page_size}"
            + f"&course_id={self.course.id}"
            + f"&tutor_id={self.tutor.id}"
        ).json()
        response_body = PrivateLessonPage.model_validate(response_body)
        self.assertEqual(response_body.page, expected_page)
        self.assertEqual(response_body.page_size, expected_page_size)
        self.assertEqual(len(response_body.results), expected_page_size)
        self.assertEqual(response_body.total, expected_total)

    async def test_update_private_lesson_endpoint(self):
        payload = {
            "course_id": self.course.id,
            "tutor_id": self.tutor.id,
            "price": 9000,
            "description": "Inicial"
        }
        headers = get_auth_header_for_tests(
            email=self.tutor.email,
            role=self.tutor.role,
            user_id=self.tutor.id
        )
        post = self.app.post("/private-lessons", json=payload, headers=headers)
        created = post.json()
        upd_payload = {"price": 9500, "description": "Modificada"}
        patch = self.app.patch(f"/private-lessons/{created['id']}", json=upd_payload, headers=headers)
        self.assertEqual(patch.status_code, 200)
        updated = patch.json()
        self.assertEqual(updated["price"], 9500)
        self.assertEqual(updated["description"], "Modificada")

    async def test_delete_private_lesson_endpoint(self):
        payload = {
            "course_id": self.course.id,
            "tutor_id": self.tutor.id,
            "price": 11000,
            "description": "A borrar"
        }
        headers = get_auth_header_for_tests(
            email=self.tutor.email,
            role=self.tutor.role,
            user_id=self.tutor.id
        )
        created = self.app.post("/private-lessons", json=payload, headers=headers).json()
        delete = self.app.delete(f"/private-lessons/{created['id']}", headers=headers)
        self.assertEqual(delete.status_code, 200)
        get = self.app.get(f"/private-lessons/{created['id']}")
        self.assertEqual(get.status_code, 404)