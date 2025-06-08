from app.crud.private_lesson import (
    create_private_lesson,
    get_private_lesson_by_id,
    update_private_lesson,
    delete_private_lesson
)
from app.database import Base
from app.models.course import Course
from app.models.user import User
from app.schemas.private_lesson import PrivateLessonCreate, PrivateLessonUpdate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from unittest import IsolatedAsyncioTestCase
from app.models import course, private_lesson, reservation, review, user



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
            price=10000,
            description="A private lesson for testing"
        )
        created_lesson = None
        async with AsyncSession(self.engine) as session:
            created_lesson = await create_private_lesson(session, lesson_data)
        self.assertIsNotNone(created_lesson)

        async def test_get_private_lesson_by_id(self):
            # Arrange: crear y persistir Course y Tutor
            course = Course(
                name="Test Course GetById",
                description="Course description."
            )
            tutor = User(
                email="tutor2@example.com",
                password="password",
                name="Tutor2 Name",
                role="tutor"
            )
            async with AsyncSession(self.engine) as session:
                session.add_all([course, tutor])
                await session.commit()
                await session.refresh(course)
                await session.refresh(tutor)
            # Act: crear la lección y luego obtenerla por ID
            lesson_data = PrivateLessonCreate(
                tutor_id=tutor.id,
                course_id=course.id,
                start_time="2023-10-02T10:00:00",
                end_time="2023-10-02T11:00:00",
                price=20000,
                description="Desc prueba"
            )
            async with AsyncSession(self.engine) as session:
                created = await create_private_lesson(session, lesson_data)
            async with AsyncSession(self.engine) as session:
                fetched = await get_private_lesson_by_id(session, created.id)
            # Assert
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.id, created.id)

        async def test_update_private_lesson(self):
            # Arrange: crear y persistir Course y Tutor
            course = Course(
                name="Test Course Update",
                description="Course description."
            )
            tutor = User(
                email="tutor3@example.com",
                password="password",
                name="Tutor3 Name",
                role="tutor"
            )
            async with AsyncSession(self.engine) as session:
                session.add_all([course, tutor])
                await session.commit()
                await session.refresh(course)
                await session.refresh(tutor)
            # Crear la lección original
            lesson_data = PrivateLessonCreate(
                tutor_id=tutor.id,
                course_id=course.id,
                start_time="2023-10-03T10:00:00",
                end_time="2023-10-03T11:00:00",
                price=15000,
                description="Original"
            )
            async with AsyncSession(self.engine) as session:
                created = await create_private_lesson(session, lesson_data)
            # Act: actualizar precio y descripción
            upd = PrivateLessonUpdate(price=18000, description="Actualizada")
            async with AsyncSession(self.engine) as session:
                updated = await update_private_lesson(session, created.id, upd)
            # Assert
            self.assertIsNotNone(updated)
            self.assertEqual(updated.price, 18000)
            self.assertEqual(updated.description, "Actualizada")

        async def test_delete_private_lesson(self):
            # Arrange: crear y persistir Course y Tutor
            course = Course(
                name="Test Course Delete",
                description="Course description."
            )
            tutor = User(
                email="tutor4@example.com",
                password="password",
                name="Tutor4 Name",
                role="tutor"
            )
            async with AsyncSession(self.engine) as session:
                session.add_all([course, tutor])
                await session.commit()
                await session.refresh(course)
                await session.refresh(tutor)
            # Crear la lección a borrar
            lesson_data = PrivateLessonCreate(
                tutor_id=tutor.id,
                course_id=course.id,
                start_time="2023-10-04T10:00:00",
                end_time="2023-10-04T11:00:00",
                price=12000,
                description="Para borrar"
            )
            async with AsyncSession(self.engine) as session:
                created = await create_private_lesson(session, lesson_data)
            # Act: borrar
            async with AsyncSession(self.engine) as session:
                ok = await delete_private_lesson(session, created.id)
            # Assert: eliminado correctamente
            self.assertTrue(ok)
            async with AsyncSession(self.engine) as session:
                fetched = await get_private_lesson_by_id(session, created.id)
            self.assertIsNone(fetched)

