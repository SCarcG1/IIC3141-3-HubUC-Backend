from app.crud.private_lesson import create_private_lesson
from app.database import Base
from app.models.course import Course
from app.models.user import User
from app.schemas.private_lesson import PrivateLessonCreate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from unittest import IsolatedAsyncioTestCase



class TestPrivateLessonCrud(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine('sqlite+aiosqlite:///:memory:')
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def asyncTearDown(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_create_private_lesson(self):
        course = Course(
            name="Test Course",
            description="Course description."
        )
        tutor = User(
            email="tutor@example.com",
            password="password",
            name="Tutor Name",
            role="tutor"
        )
        async with AsyncSession(self.engine) as session:
            session.add_all([course, tutor])
            await session.commit()
            await session.refresh(course)
            await session.refresh(tutor)
        lesson_data = PrivateLessonCreate(
            tutor_id=tutor.id,
            course_id=course.id,
            start_time="2023-10-01T10:00:00",
            end_time="2023-10-01T11:00:00",
            price=10000
        )
        created_lesson = None
        async with AsyncSession(self.engine) as session:
            created_lesson = await create_private_lesson(session, lesson_data)
        self.assertIsNotNone(created_lesson)
