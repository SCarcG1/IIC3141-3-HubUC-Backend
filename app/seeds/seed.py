from app.auth.auth_handler import get_password_hash
from app.models.course import Course
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.user import UserRole
from app.schemas.weekday import Weekday
from datetime import datetime, time, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_data(session: AsyncSession):
    now = datetime.now()

    student_data = [
        {
            "email": "jonathan@estudiante.com",
            "password": get_password_hash("jonathan123"),
            "name": "Jonathan Galvan",
            "role": UserRole.student
        },
        {
            "email": "agustina@estudiante.com",
            "password": get_password_hash("agustina123"),
            "name": "Agustina Pérez",
            "role": UserRole.student
        },
        {
            "email": "blanca@estudiante.com",
            "password": get_password_hash("blanca123"),
            "name": "Blanca Rodríguez",
            "role": UserRole.student
        }
    ]
    for s in student_data:
        existing = await session.execute(select(User).where(User.email == s["email"]))
        if not existing.scalar():
            session.add(User(**s))
    await session.commit()
    students = (await session.execute(select(User).where(User.role == UserRole.student))).scalars().all()

    tutor_data = [
        {
            "email": "raquel@tutor.com",
            "password": get_password_hash("raquel123"),
            "name": "Raquel Fernández",
            "role": UserRole.tutor
        },
        {
            "email": "francisco@tutor.com",
            "password": get_password_hash("francisco123"),
            "name": "Francisco López",
            "role": UserRole.tutor
        },
        {
            "email": "carlos@tutor.com",
            "password": get_password_hash("carlos123"),
            "name": "Carlos Martínez",
            "role": UserRole.tutor
        }
    ]

    for t in tutor_data:
        existing = await session.execute(select(User).where(User.email == t["email"]))
        if not existing.scalar():
            session.add(User(**t))
    await session.commit()
    tutors = (await session.execute(select(User).where(User.role == UserRole.tutor))).scalars().all()

    for tutor in tutors:
        for weekday in [Weekday.MONDAY, Weekday.TUESDAY, Weekday.WEDNESDAY, Weekday.THURSDAY, Weekday.FRIDAY]:
            session.add(WeeklyTimeblock(
                user_id=tutor.id,
                weekday=weekday,
                start_hour=time(8, 20),
                end_hour=time(9, 30),
                valid_from=now - timedelta(days=30),
                valid_until=now + timedelta(days=30)
            ))
    await session.commit()

    courses_data = [
        {
            "name": "Álgebra Lineal",
            "description": "Proporcionar al alumno los conceptos principales y la terminología del álgebra lineal que permitan al alumno plantear, resolver y analizar mediante técnicas vectoriales y matriciales problemas que surgen en el ámbito de la ingeniería, como por ejemplo en diseño de estructuras, análisis de señales, sistemas de control, robótica, computación gráfica, física, análisis estadístico y simulaciones.",
        },
        {
            "name": "Cálculo I",
            "description": "El curso se orienta a entregar los conceptos básicos de límites y continuidad de funciones, de la derivada de una función y su interpretación geométrica, en conjunto con los mecanismos y técnicas de derivación, las aplicaciones más relevantes de la derivada a problemas diversos de las matemáticas y la física, la obtención de puntos críticos de una función, la definición de la Integral, el cálculo de integrales mediante primitivas, y las técnicas de integración."
        },
        {
            "name": "Dinámica",
            "description": "El curso de Dinámica tiene como objetivo principal introducir a los estudiantes en el estudio del movimiento de los cuerpos y las fuerzas que lo producen. A través de este curso, se busca que los alumnos comprendan los principios fundamentales de la dinámica, incluyendo las leyes de Newton, el análisis de fuerzas y momentos, y la aplicación de estos conceptos a problemas prácticos en ingeniería."
        },
        {
            "name": "Ecuaciones Diferenciales",
            "description": "El curso de Ecuaciones Diferenciales tiene como objetivo principal introducir a los estudiantes en el estudio de las ecuaciones diferenciales ordinarias y parciales, así como sus aplicaciones en diversas áreas de la ingeniería. A través de este curso, se busca que los alumnos comprendan los conceptos fundamentales de las ecuaciones diferenciales, aprendan a resolverlas y a aplicarlas en problemas prácticos."
        },
        {
            "name": "Introducción a la Programación",
            "description": "El curso de Introducción a la Programación tiene como objetivo principal introducir a los estudiantes en los conceptos fundamentales de la programación y el desarrollo de software. A través de este curso, se busca que los alumnos comprendan los principios básicos de la programación, aprendan a escribir código en un lenguaje de programación específico y desarrollen habilidades para resolver problemas mediante la programación."
        }
    ]

    for course_data in courses_data:
        existing = await session.execute(select(Course).where(Course.name == course_data["name"]))
        if not existing.scalar():
            session.add(Course(**course_data))
    await session.commit()
    courses = (await session.execute(select(Course))).scalars().all()

    lessons = []
    for i, course in enumerate(courses[:2]):
        for tutor in tutors[:2]:
            lesson = PrivateLesson(
                tutor_id=tutor.id,
                course_id=course.id,
                price=10000 + i * 1000,
                description=f"Clase privada sobre {course.name} con {tutor.name}"
            )
            session.add(lesson)
            await session.commit()
            await session.refresh(lesson)
            lessons.append(lesson)

    reservations = []
    for i, lesson in enumerate(lessons):
        for student in students[:2]:
            reservation = Reservation(
                student_id=student.id,
                private_lesson_id=lesson.id,
                status=ReservationStatus.PENDING,
                start_time=datetime(now.year, now.month, now.day, 8, 20) + timedelta(days=1),
                end_time=datetime(now.year, now.month, now.day, 9, 30) + timedelta(days=1),
            )
            session.add(reservation)
            await session.commit()
            await session.refresh(reservation)
            reservations.append(reservation)


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
