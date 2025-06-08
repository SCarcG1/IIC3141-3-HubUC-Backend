from app.crud.reservation import create_reservation, get_reservation_by_id
from app.database import Base
from app.models.user import User
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.schemas.reservation import ReservationCreate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from unittest import IsolatedAsyncioTestCase
from datetime import datetime, timedelta
from app.models import course, private_lesson, reservation, review, user
class TestReservationCrud(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_create_reservation(self):
        course = Course(name="Course", description="Desc")
        student = User(email="student@test.com", password="pw", name="Student", role="student")
        tutor = User(email="tutor@test.com", password="pw", name="Tutor", role="tutor")

        async with AsyncSession(self.engine) as session:
            session.add_all([course, student, tutor])
            await session.commit()
            await session.refresh(course)
            await session.refresh(student)
            await session.refresh(tutor)

        lesson = PrivateLesson(
            tutor_id=tutor.id,
            course_id=course.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            price=10000
        )
        async with AsyncSession(self.engine) as session:
            session.add(lesson)
            await session.commit()
            await session.refresh(lesson)

        reservation_data = ReservationCreate(
            student_id=student.id,
            private_lesson_id=lesson.id,
            status="pending"
        )
        async with AsyncSession(self.engine) as session:
            reservation = await create_reservation(session, reservation_data)

        self.assertIsNotNone(reservation)
        self.assertEqual(reservation.student_id, student.id)
