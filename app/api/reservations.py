from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.reservation import (
    delete_reservation,
    get_all_reservations,
    get_reservation_by_student_id,
    get_reservation_by_tutor_id,
    get_reservation_by_tutor_and_student,
    update_reservation_data_student,
    update_reservation_data_tutor,
    validate_and_create_reservation,
)
from app.schemas.reservation import (
    ReservationCreate,
    ReservationExtendedOut,
    ReservationOut,
    ReservationStatus,
    ReservationUpdate,
)
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


# CREATE


@router.post(
    "/reservations/lesson/{private_lesson_id}",
    dependencies=[Depends(JWTBearer())],
    response_model=ReservationOut,
)
async def post_reservation(
    private_lesson_id: int,
    start_time: datetime,
    end_time: datetime,
    db: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer())
):
    user_id = jwt_payload.get("id") or jwt_payload.get("user_id")
    if jwt_payload["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can create reservations"
        )
    reservation_data = ReservationCreate(
        private_lesson_id=private_lesson_id,
        student_id=user_id,
        status=ReservationStatus.PENDING,
        start_time=start_time,
        end_time=end_time
    )
    return await validate_and_create_reservation(db, reservation_data)


# READ


@router.get("/reservations", response_model=list[ReservationExtendedOut])
async def read_reservations(db: AsyncSession = Depends(get_db)):
    return await get_all_reservations(db)


@router.get(
    "/reservations/student",
    response_model=list[ReservationExtendedOut],
    dependencies=[Depends(JWTBearer())]
)
async def read_students_reservations(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    if payload.get("role") != "student":
        raise HTTPException(status_code=403, detail="Forbidden")
    student_id = payload.get("user_id") or payload.get("id")
    if student_id is None:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    return await get_reservation_by_student_id(db, student_id)


@router.get(
    "/reservations/tutor",
    response_model=list[ReservationExtendedOut],
    dependencies=[Depends(JWTBearer())]
)
async def read_tutors_reservations(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    if payload.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden")
    tutor_id = payload.get("user_id") or payload.get("id")
    if tutor_id is None:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    return await get_reservation_by_tutor_id(db, tutor_id)


@router.get(
    "/reservations/tutor/{tutor_id}/student/{student_id}",
    response_model=list[ReservationExtendedOut],
    dependencies=[Depends(JWTBearer())]
)
async def read_reservation_by_tutor_and_student(
    tutor_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    """Obtener reservas específicas entre un tutor y un estudiante"""
    # Verificar que el usuario autenticado es el tutor o el estudiante
    user_id = payload.get("user_id") or payload.get("id")
    user_role = payload.get("role")

    if user_role == "tutor" and user_id != tutor_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own reservations"
        )
    elif user_role == "student" and user_id != student_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own reservations"
        )
    elif user_role not in ["tutor", "student"]:
        raise HTTPException(
            status_code=403,
            detail="Only tutors and students can view reservations"
        )

    reservations = await get_reservation_by_tutor_and_student(
        db, tutor_id, student_id
    )

    return reservations


# UPDATE


@router.patch(
    "/reservations/tutor/{reservation_id}",
    response_model=ReservationOut,
    dependencies=[Depends(JWTBearer())]
)
async def update_reservation_tutor(
    reservation_id: int,
    reservation: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    tutor: dict = Depends(JWTBearer())
):
    if tutor["role"] != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden")

    user_id = tutor.get("user_id") or tutor.get("id")

    updated = await update_reservation_data_tutor(
        db, reservation_id, reservation, user_id
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found or you are not allowed to update it"
        )
    return updated


@router.patch(
    "/reservations/student/{reservation_id}",
    response_model=ReservationOut,
    dependencies=[Depends(JWTBearer())]
)
async def update_reservation_student(
    reservation_id: int,
    reservation: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    student: dict = Depends(JWTBearer())
):
    if student["role"] != "student":
        raise HTTPException(status_code=403, detail="Forbidden")

    user_id = student.get("user_id") or student.get("id")

    # Different from the other update_reservation,
    # this one ensure no changes to private_lesson_id or status
    updated = await update_reservation_data_student(
        db, reservation_id, reservation, user_id
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found or you are not allowed to update it"
        )
    return updated


# DELETE


@router.delete(
    "/reservations/{reservation_id}",
    dependencies=[Depends(JWTBearer())]
)
async def delete_reservation_endpoint(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    if token["role"] not in ["tutor", "student"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    deleted = await delete_reservation(
        db, reservation_id, token["id"], token["role"]
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"detail": f"Reservation {reservation_id} deleted"}
