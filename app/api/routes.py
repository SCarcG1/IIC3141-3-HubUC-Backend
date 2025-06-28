from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import SessionLocal
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.crud.user import create_user, get_user_by_email, get_user_by_id
from app.auth.auth_handler import verify_password, create_access_token
from app.auth.auth_bearer import JWTBearer
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut
from app.crud.course import get_all_courses, get_course_by_id, create_course, update_course, delete_course
from app.schemas.reservation import (
    ReservationCreate,
    ReservationExtendedOut,
    ReservationOut,
    ReservationStatus,
    ReservationUpdate,
)
from app.crud.reservation import (
    delete_reservation,
    get_all_reservations,
    get_reservation_by_student_id,
    get_reservation_by_tutor_id,
    update_reservation,
    update_reservation_data_student,
    validate_and_create_reservation,
)
from app.api.chat import manager
from datetime import datetime

router = APIRouter()

# ————— Helpers DB —————
async def get_db():
    async with SessionLocal() as session:
        yield session

# ————— RUTAS HTTP —————

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db, user)


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email, "role": db_user.role, "id": db_user.id})
    return {
        "access_token": token,
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role
        }
    }

@router.get("/protected-route")
async def protected(data=Depends(JWTBearer())):
    return {"message": f"Hello {data['sub']} with role {data['role']}"}

# ————— RUTA WEBSOCKET —————

@router.websocket("/ws/chat/{username}")
async def websocket_chat(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            payload = await websocket.receive_json()
            text = payload.get("message", "").strip()
            if text:
                await manager.broadcast({
                    "system": False,
                    "username": username,
                    "message": text
                })
    except WebSocketDisconnect:
        left = manager.disconnect(websocket)
        await manager.broadcast({
            "system": True,
            "message": f"❌ {left} ha salido del chat"
        })

######## Course Routes ########
@router.get("/courses", response_model=List[CourseOut])
async def read_courses(db: AsyncSession = Depends(get_db)):
    return await get_all_courses(db)

@router.get("/courses/{course_id}", response_model=CourseOut)
async def read_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/courses", response_model=CourseOut)
async def create_new_course(course: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await create_course(db, course)

@router.put("/courses/{course_id}", response_model=CourseOut)
async def update_existing_course(course_id: int, course: CourseUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_course(db, course_id, course)
    if not updated:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated

@router.delete("/courses/{course_id}")
async def delete_existing_course(course_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_course(db, course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"detail": f"Course {course_id} deleted"}

######## Reservation Routes ########

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
    if jwt_payload["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can create reservations")
    reservation_data = ReservationCreate(
        private_lesson_id=private_lesson_id,
        student_id = jwt_payload.get("id") or jwt_payload.get("user_id"),
        status=ReservationStatus.PENDING,
        start_time=start_time,
        end_time=end_time
    )
    return await validate_and_create_reservation(db, reservation_data)

# READ

@router.get("/reservations", response_model=List[ReservationExtendedOut])
async def read_reservations(db: AsyncSession = Depends(get_db)):
    return await get_all_reservations(db)

@router.get("/reservations/student", response_model=List[ReservationExtendedOut], dependencies=[Depends(JWTBearer())]
)
async def read_students_reservations(db: AsyncSession = Depends(get_db), payload: dict = Depends(JWTBearer())
):
    if payload.get("role") != "student":
        raise HTTPException(status_code=403, detail="Forbidden")
    student_id = payload.get("user_id") or payload.get("id")
    if student_id is None:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    return await get_reservation_by_student_id(db, student_id)


@router.get("/reservations/tutor", response_model=List[ReservationExtendedOut], dependencies=[Depends(JWTBearer())]
)
async def read_tutors_reservations(db: AsyncSession = Depends(get_db),payload: dict = Depends(JWTBearer())
):
    if payload.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden")
    tutor_id = payload.get("user_id") or payload.get("id")
    if tutor_id is None:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    return await get_reservation_by_tutor_id(db, tutor_id)

# UPDATE

@router.put("/reservations/{reservation_id}", response_model=ReservationOut, dependencies=[Depends(JWTBearer())])
async def create_new_reservation(reservation_id: int, reservation: ReservationUpdate, db: AsyncSession = Depends(get_db), tutor: dict = Depends(JWTBearer())):
    if tutor["role"] != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Ensure that the tutor is the one updating the reservation
    if reservation.tutor_id is not None and reservation.tutor_id != (tutor.get("user_id") or tutor.get("id")):
        raise HTTPException(status_code=403, detail="Forbidden: You can only update your own reservations")
    
    # Ensure the reservation sent has the tutor_id
    if reservation.tutor_id is None:
        reservation.tutor_id = tutor.get("user_id") or tutor.get("id")
    
    updated = await update_reservation(db, reservation_id, reservation)
    if not updated:
        raise HTTPException(status_code=404, detail="Reservation not found or you are not allowed to update it")
    return updated

@router.patch("/reservations/{reservation_id}/student", response_model=ReservationOut, dependencies=[Depends(JWTBearer())])
async def update_reservation_student(reservation_id: int, reservation: ReservationUpdate, db: AsyncSession = Depends(get_db), student: dict = Depends(JWTBearer())):
    if student["role"] != "student":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Ensure that the student is the one updating the reservation
    if reservation.student_id is not None and reservation.student_id != (student.get("user_id") or student.get("id")):
        raise HTTPException(status_code=403, detail="Forbidden: You can only update your own reservations")
    
    # Ensure the reservation sent has the student_id
    if reservation.student_id is None:
        reservation.student_id = student.get("user_id") or student.get("id")

    updated = await update_reservation_data_student(db, reservation_id, reservation) # Different from the other update_reservation, this one ensure no changes to private_lesson_id or status
    if not updated:
        raise HTTPException(status_code=404, detail="Reservation not found or you are not allowed to update it")
    return updated

# DELETE

@router.delete("/reservations/{reservation_id}", dependencies=[Depends(JWTBearer())])
async def delete_reservation_endpoint(reservation_id: int, db: AsyncSession = Depends(get_db), token: dict = Depends(JWTBearer())):
    if token["role"] not in ["tutor", "student"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    deleted = await delete_reservation(db, reservation_id, token["id"], token["role"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"detail": f"Reservation {reservation_id} deleted"}

