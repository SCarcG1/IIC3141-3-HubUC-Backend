from app.api.routes import get_db
from app.crud.user import UserCRUD
from app.crud.private_lesson import PrivateLessonCRUD
from app.database import Base
from app.main import app
from app.models.course import Course
from app.models.user import User
from app.schemas.private_lesson import (
    OfferStatus,
    PrivateLessonBase,
    PrivateLessonCreate,
    PrivateLessonOut,
    PrivateLessonPage
)
from app.schemas.user import UserCreate, UserRole
from fastapi.testclient import TestClient
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
        lesson_data = {
            "course_id": self.course.id,
            "price": 10000,
            "tutor_id": self.tutor.id,
            "description": "This is a test private lesson."
        }
        supposedly_created_lesson = self.app.post(
            url="/private-lessons/",
            json=lesson_data,
            headers=get_auth_header_for_tests(
                email=self.tutor.email,
                role=self.tutor.role,
                user_id=self.tutor.id
            )
        ).json()
        supposed_lesson_id: int = supposedly_created_lesson["id"]
        async with SessionLocal() as session:
            crud = PrivateLessonCRUD(session)
            db_lesson = await crud.read_by_id(supposed_lesson_id)
        db_lesson = PrivateLessonBase.model_validate(db_lesson)
        expected_lesson = PrivateLessonBase.model_validate(lesson_data)
        self.assertEqual(db_lesson, expected_lesson)

    async def test_get_all_private_lessons(self):
        open_lesson_data = PrivateLessonCreate(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=10000,
            offer_status=OfferStatus.OPEN
        )
        closed_lesson_data = PrivateLessonCreate(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=20000,
            offer_status=OfferStatus.CLOSED
        )
        expected_lessons = []
        async with SessionLocal() as session:
            crud = PrivateLessonCRUD(session)
            for _ in range(2):
                lesson = await crud.create(open_lesson_data)
                expected_lessons.append(lesson)
                lesson = await crud.create(closed_lesson_data)
                expected_lessons.append(lesson)
        expected_lessons = [
            PrivateLessonBase.model_validate(lesson)
            for lesson in expected_lessons
        ]
        retrieved_lessons: list[dict] = self.app.get(
            "/private-lessons",
            params={"include_closed_private_lessons": True}
        ).json()
        retrieved_lessons = [
            PrivateLessonBase.model_validate(lesson)
            for lesson in retrieved_lessons
        ]
        self.assertEqual(retrieved_lessons, expected_lessons)

    async def test_get_private_lesson_by_id(self):
        lesson_data = PrivateLessonCreate(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=15000,
            description="Test lesson"
        )
        async with SessionLocal() as session:
            crud = PrivateLessonCRUD(session)
            expected_lesson = await crud.create(lesson_data)
        expected_lesson = PrivateLessonOut.model_validate(expected_lesson)
        retrieved_lesson = self.app.get(
            f"/private-lessons/{expected_lesson.id}"
        ).json()
        retrieved_lesson = PrivateLessonOut.model_validate(retrieved_lesson)
        self.assertEqual(retrieved_lesson, expected_lesson)

    async def test_get_by_tutor_id(self):
        # Arrange: create two tutors, and a lesson for each tutor.
        async with SessionLocal() as session:
            user_crud = UserCRUD(session)
            tutor_1 = await user_crud.create(UserCreate(
                email="tutor_1@example.com",
                name="Tutor One",
                password="password123",
                role=UserRole.tutor
            ))
            tutor_2 = await user_crud.create(UserCreate(
                email="tutor_2@example.com",
                name="Tutor Two",
                password="password123",
                role=UserRole.tutor
            ))
            lesson_crud = PrivateLessonCRUD(session)
            lesson_1 = await lesson_crud.create(PrivateLessonCreate(
                tutor_id=tutor_1.id,
                course_id=self.course.id,
                price=12000,
                description="Lesson by Tutor One"
            ))
            await lesson_crud.create(PrivateLessonCreate(
                tutor_id=tutor_2.id,
                course_id=self.course.id,
                price=15000,
                description="Lesson by Tutor Two"
            ))
        # In "act", we will retrieve lessons only for tutor_1, so:
        expected_lessons = [PrivateLessonOut.model_validate(lesson_1)]
        # Act: retrieve lessons of tutor_1.
        retrieved_page = self.app.get(
            url="/private-lessons/search",
            params={"tutor_id": tutor_1.id}
        ).json()
        # Assert:
        retrieved_page = PrivateLessonPage.model_validate(retrieved_page)
        retrieved_lessons = retrieved_page.results
        self.assertEqual(retrieved_lessons, expected_lessons)

    async def test_get_by_course_id(self):
        pass

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
        patch = self.app.patch(
            f"/private-lessons/{created['id']}",
            json=upd_payload,
            headers=headers
        )
        self.assertEqual(patch.status_code, 200)
        updated = patch.json()
        self.assertEqual(updated["price"], 9500)
        self.assertEqual(updated["description"], "Modificada")

    async def test_delete_private_lesson(self):
        lesson_data = PrivateLessonCreate(
            tutor_id=self.tutor.id,
            course_id=self.course.id,
            price=10000,
            offer_status=OfferStatus.OPEN
        )
        async with SessionLocal() as db_session:
            crud = PrivateLessonCRUD(db_session)
            lesson = await crud.create(lesson_data)
        lesson = self.app.delete(
            url=f"/private-lessons/{lesson.id}",
            headers=get_auth_header_for_tests(
                email=self.tutor.email,
                role=self.tutor.role,
                user_id=self.tutor.id
            )
        ).json()
        lesson = PrivateLessonOut.model_validate(lesson)
        self.assertEqual(lesson.offer_status, OfferStatus.CLOSED)
