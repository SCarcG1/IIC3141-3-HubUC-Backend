from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.crud.private_lesson import PrivateLessonCRUD
from app.models.user import User
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.reservation import ReservationStatus
from app.schemas.user import UserCreate, UserUpdate
from app.auth.auth_handler import get_password_hash
from datetime import datetime


async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        email=user.email,
        name=user.name,
        number=user.number,
        password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_full_data_of_user(
    db: AsyncSession,
    user_id: int,
    user_role: str
):
    if user_role not in ['tutor', 'student']:
        raise ValueError("Invalid user role. Must be 'tutor' or 'student'.")

    if user_role == 'tutor':
        query = (
            select(User)
            .where(User.id == user_id, User.role == 'tutor')
            .options(
                selectinload(User.private_lessons),
                selectinload(User.weekly_timeblocks)
            )
        )
    elif user_role == 'student':
        query = (
            select(User)
            .where(User.id == user_id, User.role == 'student')
            .options(
                selectinload(User.reservations),
                selectinload(User.weekly_timeblocks)
            )
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_all_users_by_role(db: AsyncSession, role: str):
    result = await db.execute(select(User).where(User.role == role))
    return result.scalars().all()


async def get_tutor_of_private_lesson(db: AsyncSession, lesson_id: int):
    query = (
        select(User)
        .join(User.private_lessons)
        .where(User.role == 'tutor', User.private_lessons.any(id=lesson_id))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_student_of_reservation(db: AsyncSession, reservation_id: int):
    query = (
        select(User)
        .join(User.reservations)
        .where(
            User.role == 'student',
            User.reservations.any(id=reservation_id)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None

    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.number is not None:
        db_user.number = user_update.number
    if user_update.password is not None:
        db_user.password = get_password_hash(user_update.password)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int):
    """
    Elimina un usuario y todas sus relaciones asociadas.

    Esta función maneja la eliminación en cascada de:
    - Private lessons (si es tutor)
    - Reservations (si es estudiante o tutor)
    - Reviews (relacionadas con las reservations)
    - Weekly timeblocks
    """
    # Obtener el usuario con todas sus relaciones
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    # Eliminar weekly timeblocks del usuario
    weekly_timeblocks = await db.execute(
        select(WeeklyTimeblock).where(WeeklyTimeblock.user_id == user_id)
    )
    for timeblock in weekly_timeblocks.scalars().all():
        await db.delete(timeblock)

    if user.role == "tutor":
        # Si es tutor, eliminar sus private lessons
        # y todas las reservations asociadas
        private_lesson_crud = PrivateLessonCRUD(db)
        private_lessons = await private_lesson_crud.read_by_tutor_id(user_id)
        for lesson in private_lessons:
            # Eliminar reviews de las reservations de esta lesson
            lesson_reservations = await db.execute(
                select(Reservation).where(
                    Reservation.private_lesson_id == lesson.id
                )
            )
            for reservation in lesson_reservations.scalars().all():
                # Eliminar reviews de esta reservation
                reviews = await db.execute(
                    select(Review).where(
                        Review.reservation_id == reservation.id
                    )
                )
                for review in reviews.scalars().all():
                    await db.delete(review)
                # Si la reservación aún no se ha llevado a cabo,
                # se rechaza:
                if (
                    reservation.status == ReservationStatus.PENDING or
                    reservation.start_time > datetime.now()
                ):
                    reservation.status = ReservationStatus.REJECTED
                    db.add(reservation)
            # Eliminar la private lesson
            await private_lesson_crud.delete(lesson.id)

    elif user.role == "student":
        # Si es estudiante, eliminar las reviews asociadas a sus reservaciones:
        reservations = await db.execute(
            select(Reservation).where(Reservation.student_id == user_id)
        )
        for reservation in reservations.scalars().all():
            # Eliminar reviews de esta reservation
            reviews = await db.execute(
                select(Review).where(Review.reservation_id == reservation.id)
            )
            for review in reviews.scalars().all():
                await db.delete(review)
            # Si la reservación aún no se ha llevado a cabo,
            # se rechaza automáticamente:
            if (
                reservation.status == ReservationStatus.PENDING or
                reservation.start_time > datetime.now()
            ):
                reservation.status = ReservationStatus.REJECTED
                db.add(reservation)

    # Finalmente, eliminar el usuario
    await db.delete(user)
    await db.commit()

    return True


class UserCRUD:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, user_data: UserCreate):
        return await create_user(self.db_session, user_data)

    async def read_all(self):
        return await get_all_users(self.db_session)

    async def read_by_email(self, email: str):
        return await get_user_by_email(self.db_session, email)

    async def read_by_id(self, user_id: int):
        return await get_user_by_id(self.db_session, user_id)

    async def read_full_data_by_id(self, user_id: int, user_role: str):
        return await get_full_data_of_user(self.db_session, user_id, user_role)

    async def read_by_role(self, role: str):
        return await get_all_users_by_role(self.db_session, role)

    async def update(self, user_id: int, user_data: UserUpdate):
        return await update_user(self.db_session, user_id, user_data)

    async def delete(self, user_id: int):
        return await delete_user(self.db_session, user_id)
