from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.reservation import Reservation
from app.models.private_lesson import PrivateLesson
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.crud.private_lesson import get_tutors_private_lessons

async def get_all_reservations(db: AsyncSession):
    result = await db.execute(select(Reservation))
    return result.scalars().all()

async def get_reservation_by_id(db: AsyncSession, reservation_id: int):
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    return result.scalar_one_or_none()

async def get_reservation_by_student_id(db: AsyncSession, student_id: int):
    result = await db.execute(select(Reservation).where(Reservation.student_id == student_id))
    return result.scalars().all()

async def get_reservation_by_tutor_id(db: AsyncSession, tutor_id: int):
    result = await db.execute(select(PrivateLesson).where(PrivateLesson.tutor_id == tutor_id))
    tutor_lessons= result.scalars().all()
    tutor_lesson_ids = [lesson.id for lesson in tutor_lessons]

    result = await db.execute(select(Reservation).where(Reservation.private_lesson_id.in_(tutor_lesson_ids)))
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
