from app.crud.private_lesson import get_private_lesson_by_id
from app.crud.weekly_timeblocks import read_weekly_timeblocks_of_user
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.utilities.weekly_timeblocks import are_start_time_and_end_time_inside_connected_timeblocks
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def validate_reservation(db_session: AsyncSession, reservation_data: ReservationCreate):
    # Validate that private lesson exists:
    private_lesson = await get_private_lesson_by_id(db_session, reservation_data.private_lesson_id)
    if not private_lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Private lesson with ID {reservation_data.private_lesson_id} not found"
        )
    # Validate that the reservation is being made in available time blocks:
    weekly_timeblocks = await read_weekly_timeblocks_of_user(db_session, private_lesson.tutor_id)
    if not are_start_time_and_end_time_inside_connected_timeblocks(
        reservation_data.start_time,
        reservation_data.end_time,
        weekly_timeblocks
    ):
        raise HTTPException(
            status_code=400,
            detail="Reservation start and end times are not within the tutor's available time blocks"
        )
    # Validate that the reservation does not overlap with existing reservations:
    # PENDIENTE


async def create_reservation(db: AsyncSession, reservation_data: ReservationCreate):
    reservation = Reservation(**reservation_data.model_dump())
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation


async def validate_and_create_reservation(
    db_session: AsyncSession,
    reservation_data: ReservationCreate
):
    await validate_reservation(db_session, reservation_data)
    reservation = await create_reservation(db_session, reservation_data)
    return reservation


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


async def update_reservation(db: AsyncSession, reservation_id: int, reservation: ReservationUpdate):
    db_reservation = await get_reservation_by_id(db, reservation_id)
    if db_reservation is None:
        return None
    for field, value in reservation.model_dump().items():
        setattr(db_reservation, field, value)
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

async def update_reservation_data_student(db: AsyncSession, reservation_id: int, reservation: ReservationUpdate):
    db_reservation = await get_reservation_by_id(db, reservation_id)
    if db_reservation is None:
        return None
    
    # Ensure that the student_id of db_reservation matches the student_id in the reservation update
    if db_reservation.student_id != reservation.student_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only update your own reservations")
    
    # Don't allow changing the private lesson ID, or status if the reservation is being updated by a student
    if ('private_lesson_id' in reservation.model_dump() and db_reservation.private_lesson_id != reservation.private_lesson_id) or \
       ('status' in reservation.model_dump() and db_reservation.status != reservation.status):
        raise HTTPException(status_code=400, detail="Forbidden: You cannot change the private lesson or status")

    for field, value in reservation.model_dump().items():
        setattr(db_reservation, field, value)
    
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

async def delete_reservation(db: AsyncSession, reservation_id: int, user_id: int, user_role: str):
    if user_role == "student":
        query = select(Reservation).where(Reservation.id == reservation_id, Reservation.student_id == user_id)
    elif user_role == "tutor":
        lesson_ids = (
            await db.execute(
                select(PrivateLesson.id).where(PrivateLesson.tutor_id == user_id)
            )
        ).scalars().all()
        query = select(Reservation).where(Reservation.id == reservation_id, Reservation.private_lesson_id.in_(lesson_ids))
    else:
        return None
    db_reservation = (await db.execute(query)).scalar_one_or_none()
    if db_reservation is None:
        return None
    await db.delete(db_reservation)
    await db.commit()
    return True
