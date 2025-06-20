from app.auth.auth_handler import get_password_hash
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.schemas.user import UserRole
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_data(session: AsyncSession):
    students = await add_students(session, 2)
    tutors = await add_tutors(session, 2)

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

    courses = (await session.execute(select(Course))).scalars().all()
    existing_lessons = (await session.execute(select(PrivateLesson))).scalars().all()
    if not existing_lessons:
        for i, course in enumerate(courses):
            for tutor in tutors:
                lesson = PrivateLesson(
                    tutor_id=tutor.id,
                    course_id=course.id,
                    price=10000 + i * 1000,
                    description=f"Clase privada sobre {course.name} con {tutor.name}"
                )
                session.add(lesson)
        await session.commit()

    lessons = (await session.execute(select(PrivateLesson))).scalars().all()
    existing_reservations = (await session.execute(select(Reservation))).scalars().all()
    if not existing_reservations:
        for i, lesson in enumerate(lessons[:2]):
            session.add(Reservation(
                student_id=students[0].id,
                private_lesson_id=lesson.id,
                status=ReservationStatus.PENDING,
                start_time=datetime(2025, 6, 2, 10, 0, 0),
                end_time=datetime(2025, 6, 2, 11, 0, 0),
            ))
        for i, lesson in enumerate(lessons[2:]):
            session.add(Reservation(
                student_id=students[1].id,
                private_lesson_id=lesson.id,
                status=ReservationStatus.PENDING,
                start_time=datetime(2025, 6, 3, 10, 0, 0),
                end_time=datetime(2025, 6, 3, 11, 0, 0),
            ))
        await session.commit()


async def add_students(db_session: AsyncSession, number_of_students: int) -> list[User]:
    students = []
    for i in range(number_of_students):
        new_user = User(
            email=f"student{i}@example.com",
            name=f"Estudiante {i}",
            password=get_password_hash(f"student{i}"),
            role=UserRole.student
        )
        exists = (await db_session.execute(select(User).where(User.email == new_user.email))).scalar()
        if not exists:
            students.append(new_user)
    db_session.add_all(students)
    await db_session.commit()
    for student in students:
        await db_session.refresh(student)
    return students


async def add_tutors(db_session: AsyncSession, number_of_tutors: int) -> list[User]:
    tutors = []
    for i in range(number_of_tutors):
        new_user = User(
            email=f"tutor{i}@example.com",
            name=f"Tutor {i}",
            password=get_password_hash(f"tutor{i}"),
            role=UserRole.tutor
        )
        exists = (await db_session.execute(select(User).where(User.email == new_user.email))).scalar()
        if not exists:
            tutors.append(new_user)
    db_session.add_all(tutors)
    await db_session.commit()
    for tutor in tutors:
        await db_session.refresh(tutor)
    return tutors
