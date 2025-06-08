from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.user import User
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation, ReservationStatus
from app.auth.auth_handler import get_password_hash

async def seed_data(session: AsyncSession):
    users_data = [
        {"email": "admin@example.com", "name": "Admin", "password": "admin123", "role": "admin"},
        {"email": "tutor1@example.com", "name": "Tutor Uno", "password": "tutor123", "role": "tutor"},
        {"email": "student1@example.com", "name": "Estudiante Uno", "password": "student123", "role": "student"},
        {"email": "student2@example.com", "name": "Estudiante Dos", "password": "student456", "role": "student"},
    ]

    for user_data in users_data:
        existing = await session.execute(select(User).where(User.email == user_data["email"]))
        if not existing.scalar():
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                password=get_password_hash(user_data["password"]),
                role=user_data["role"]
            )
            session.add(user)

    await session.commit()

    courses_data = [
        {"name": "Matemáticas", "description": "Curso básico de álgebra y aritmética"},
        {"name": "Física", "description": "Introducción a la mecánica y electricidad"},
        {"name": "Química", "description": "Reacciones, elementos y compuestos"},
        {"name": "Programación", "description": "Aprende Python desde cero"},
    ]

    for course_data in courses_data:
        existing = await session.execute(select(Course).where(Course.name == course_data["name"]))
        if not existing.scalar():
            session.add(Course(**course_data))

    await session.commit()

    tutor = (await session.execute(select(User).where(User.email == "tutor1@example.com"))).scalar_one()
    courses = (await session.execute(select(Course))).scalars().all()

    existing_lessons = (await session.execute(select(PrivateLesson))).scalars().all()
    if not existing_lessons:
        now = datetime.utcnow()
        for i, course in enumerate(courses):
            lesson = PrivateLesson(
                tutor_id=tutor.id,
                course_id=course.id,
                start_time=now + timedelta(days=i),
                end_time=now + timedelta(days=i, hours=1),
                price=10000 + i * 1000,
                description=f"Clase Privada sobre {course.name} con {tutor.name}"
            )
            session.add(lesson)

        await session.commit()

    student1 = (await session.execute(select(User).where(User.email == "student1@example.com"))).scalar_one()
    student2 = (await session.execute(select(User).where(User.email == "student2@example.com"))).scalar_one()
    lessons = (await session.execute(select(PrivateLesson))).scalars().all()

    existing_reservations = (await session.execute(select(Reservation))).scalars().all()
    if not existing_reservations:
        for i, lesson in enumerate(lessons[:2]):
            session.add(Reservation(
                student_id=student1.id,
                private_lesson_id=lesson.id,
                status=ReservationStatus.ACCEPTED
            ))

        for i, lesson in enumerate(lessons[2:]):
            session.add(Reservation(
                student_id=student2.id,
                private_lesson_id=lesson.id,
                status=ReservationStatus.PENDING
            ))

        await session.commit()