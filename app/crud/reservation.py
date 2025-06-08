from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from app.models.reservation import Reservation
from app.models.private_lesson import PrivateLesson
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.crud.private_lesson import get_tutors_private_lessons

async def get_all_reservations(db: AsyncSession):
    query = (
        select(Reservation)
        .options(
            selectinload(Reservation.student),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.course),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.tutor),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_reservation_by_id(db: AsyncSession, reservation_id: int):
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    return result.scalar_one_or_none()

async def get_reservation_by_student_id(db: AsyncSession, student_id: int):
    query = (
        select(Reservation)
        .where(Reservation.student_id == student_id)
        .options(
            selectinload(Reservation.student),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.course),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.tutor),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_reservation_by_tutor_id(db: AsyncSession, tutor_id: int):
    lesson_ids = (
        await db.execute(
            select(PrivateLesson.id).where(PrivateLesson.tutor_id == tutor_id)
        )
    ).scalars().all()

    query = (
        select(Reservation)
        .where(Reservation.private_lesson_id.in_(lesson_ids))
        .options(
            selectinload(Reservation.student),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.course),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.tutor),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_reservation(db: AsyncSession, reservation: ReservationCreate):
    db_reservation = Reservation(
        student_id=reservation.student_id,
        private_lesson_id=reservation.private_lesson_id,
        status=reservation.status
    )

    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

async def update_reservation(db: AsyncSession, reservation_id: int, reservation: ReservationUpdate):
    db_reservation = await get_reservation_by_id(db, reservation_id)
    if db_reservation is None:
        return None
    for field, value in reservation.dict().items():
        setattr(db_reservation, field, value)
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

async def delete_reservation(db: AsyncSession, reservation_id: int):
    db_reservation = await get_reservation_by_id(db, reservation_id)
    if db_reservation is None:
        return None
    await db.delete(db_reservation)
    await db.commit()
    return True
