from app.crud.reservation import (
    create_reservation,
    get_reservation_by_id,
    update_reservation,
    delete_reservation
)
from app.database import Base
from app.models.user import User
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from unittest import IsolatedAsyncioTestCase
from datetime import datetime, timedelta

class TestReservationCrud(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def setup_dependencies(self):
        # Crear student, tutor, course y private lesson de prueba
        student = User(
            email="student@example.com",
            password="password",
            name="Student Name",
            role="student"
        )
        tutor = User(
            email="tutor@example.com",
            password="password",
            name="Tutor Name",
            role="tutor"
        )
        course = Course(
            name="Test Course",
            description="Course for testing"
        )
        async with AsyncSession(self.engine) as session:
            session.add_all([student, tutor, course])
            await session.commit()
            await session.refresh(student)
            await session.refresh(tutor)
            await session.refresh(course)

            lesson = PrivateLesson(
                tutor_id=tutor.id,
                course_id=course.id,
                price=5000,
                description=None
            )
            session.add(lesson)
            await session.commit()
            await session.refresh(lesson)
            await session.refresh(student)
            await session.refresh(tutor)
        return student, lesson

    async def test_create_reservation(self):
        student, lesson = await self.setup_dependencies()
        data = ReservationCreate(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending",
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        async with AsyncSession(self.engine) as session:
            res = await create_reservation(session, data)
        self.assertIsNotNone(res)
        self.assertEqual(res.student_id, student.id)
        self.assertEqual(res.private_lesson_id, lesson.id)
        self.assertEqual(res.status.value, data.status)

    async def test_get_reservation_by_id(self):
        student, lesson = await self.setup_dependencies()
        data = ReservationCreate(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending",
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        async with AsyncSession(self.engine) as session:
            created = await create_reservation(session, data)
        async with AsyncSession(self.engine) as session:
            fetched = await get_reservation_by_id(session, created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, created.id)

    async def test_update_reservation(self):
        student, lesson = await self.setup_dependencies()
        data = ReservationCreate(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending",
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        async with AsyncSession(self.engine) as session:
            created = await create_reservation(session, data)
        upd = ReservationUpdate(status="accepted")
        async with AsyncSession(self.engine) as session:
            updated = await update_reservation(session, created.id, upd)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status.value, "accepted")

    async def test_get_reservation_by_id_not_found(self):
        async with AsyncSession(self.engine) as session:
            result = await get_reservation_by_id(session, reservation_id=999)
        self.assertIsNone(result)

    async def test_update_reservation_not_found(self):
        upd = ReservationUpdate(status="accepted")
        async with AsyncSession(self.engine) as session:
            result = await update_reservation(session, reservation_id=999, reservation=upd)
        self.assertIsNone(result)

    async def test_update_reservation_no_changes(self):
        student, lesson = await self.setup_dependencies()
        data = ReservationCreate(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending",
            start_time=datetime(2025, 6, 2, 10, 0, 0),
            end_time=datetime(2025, 6, 2, 11, 0, 0)
        )
        async with AsyncSession(self.engine) as session:
            created = await create_reservation(session, data)
            result = await update_reservation(session, created.id, ReservationUpdate(status="pending"))
        self.assertIsNotNone(result)
        self.assertEqual(result.status.value, "pending")
