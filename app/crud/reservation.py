from app.crud.private_lesson import get_private_lesson_by_id
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.utilities.availability import AvailabilityService
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def validate_reservation(
    db_session: AsyncSession,
    reservation_data: ReservationCreate
):
    # Validate that private lesson exists:
    private_lesson = await get_private_lesson_by_id(db_session, reservation_data.private_lesson_id)
    if not private_lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Private lesson with ID {reservation_data.private_lesson_id} not found"
        )

    # Validate that the private lesson is not closed:
    if private_lesson.offer_status == OfferStatus.CLOSED:
        raise HTTPException(
            status_code=400,
            detail="Cannot create reservation for a closed private lesson"
        )

    # Validate that the tutor is available at the requested time:
    availability_service = AvailabilityService(db_session)
    if not await availability_service.is_user_available_on_datetime_range(
        user_id=private_lesson.tutor_id,
        from_datetime=reservation_data.start_time,
        to_datetime=reservation_data.end_time
    ):
        raise HTTPException(
            status_code=400,
            detail="Tutor is not available at the requested time"
        )

    # Validate that there is no other reservation
    # for the same student at the same time,
    # where there is a reservation that was accepted:
    student_reservations = await db_session.execute(
        select(Reservation).where(
            Reservation.student_id == reservation_data.student_id,
            Reservation.start_time < reservation_data.end_time,
            Reservation.end_time > reservation_data.start_time,
            Reservation.status == "accepted"
        )
    )
    if student_reservations.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="You already have an accepted reservation at this time"
        )

    # PENDING: Descomentar en caso de que se quiera validar que el estudiante no esté ya inscrito en la lección privada:
    # # Validate that the student is not already enrolled in the private lesson:
    # student_reservations = await db_session.execute(
    #     select(Reservation).where(
    #         Reservation.private_lesson_id == reservation_data.private_lesson_id,
    #         Reservation.student_id == reservation_data.student_id
    #     )
    # )
    # if student_reservations.scalars().first():
    #     raise HTTPException(
    #         status_code=400,
    #         detail="You are already enrolled in this private lesson"
    #     )


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


async def get_reservation_by_tutor_and_student(db: AsyncSession, tutor_id: int, student_id: int):
    """Obtener una reserva específica entre un tutor y un estudiante"""
    query = (
        select(Reservation)
        .join(PrivateLesson, Reservation.private_lesson_id == PrivateLesson.id)
        .where(
            PrivateLesson.tutor_id == tutor_id,
            Reservation.student_id == student_id
        )
        .options(
            selectinload(Reservation.student),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.course),
            selectinload(Reservation.private_lesson).joinedload(PrivateLesson.tutor),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


async def update_reservation_data_tutor(
    db: AsyncSession,
    reservation_id: int,
    reservation_data: ReservationUpdate,
    user_id: int
):
    reservation = await get_reservation_by_id(db, reservation_id)
    if reservation is None:
        return None

    # Ensure that the tutor_id of the reservation
    # matches the user_id in the update
    private_lesson: PrivateLesson = reservation.private_lesson
    if private_lesson.tutor_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update reservations for your own lessons"
        )

    # Don't allow changing the student ID
    # if the reservation is being updated by a tutor
    if (
        reservation_data.student_id and
        reservation.student_id != reservation_data.student_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot change the student of the reservation"
        )

    # Only allow updating the status
    # if the change is to 'accepted' or 'rejected'
    if (
        reservation_data.status and
        reservation_data.status not in ['accepted', 'rejected']
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only change the status to 'accepted' or 'rejected'"
        )

    for field, value in reservation_data.model_dump().items():
        if value is not None:
            setattr(reservation, field, value)

    await db.commit()
    await db.refresh(reservation)
    return reservation


async def update_reservation_data_student(db: AsyncSession, reservation_id: int, reservation: ReservationUpdate, user_id: int):
    db_reservation = await get_reservation_by_id(db, reservation_id)
    if db_reservation is None:
        return None

    # Ensure that the student_id of db_reservation matches the student_id in the reservation update
    if db_reservation.student_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only update your own reservations")

    # Don't allow changing the private lesson ID if the reservation is being updated by a student
    if ('private_lesson_id' in reservation.model_dump() and db_reservation.private_lesson_id != reservation.private_lesson_id):
        raise HTTPException(status_code=400, detail="Forbidden: You cannot change the private lesson or status")

    # Only allow updating the status if the change is to 'rejected'
    if 'status' in reservation.model_dump() and reservation.status != 'rejected':
        raise HTTPException(status_code=400, detail="Forbidden: You can only change the status to 'rejected' to cancel the reservation")

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
