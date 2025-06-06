from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import SessionLocal
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.crud.user import create_user, get_user_by_email
from app.auth.auth_handler import verify_password, create_access_token
from app.auth.auth_bearer import JWTBearer
from app.crud.private_lesson import get_all_private_lessons, get_private_lesson_by_id, create_private_lesson, delete_private_lesson, update_private_lesson
from app.schemas.private_lesson import PrivateLessonOut, PrivateLessonCreate, PrivateLessonUpdate
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut
from app.crud.course import get_all_courses, get_course_by_id, create_course, update_course, delete_course

from app.api.chat import manager  # <-- nuestro chat manager

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
    token = create_access_token({"sub": db_user.email, "role": db_user.role})
    return {"access_token": token}

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

######## Private Lessons Routes ########
@router.get("/private-lessons", response_model=List[PrivateLessonOut])
async def read_all_private_lessons(db: AsyncSession = Depends(get_db)):
    return await get_all_private_lessons(db)

@router.get("/private-lessons/{lesson_id}", response_model=PrivateLessonOut)
async def read_private_lesson_by_id(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await get_private_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return lesson

@router.post("/private-lessons", response_model=PrivateLessonOut, dependencies=[Depends(JWTBearer())])
async def create_lesson(lesson: PrivateLessonCreate, db: AsyncSession = Depends(get_db)):
    return await create_private_lesson(db, lesson)

@router.delete("/private-lessons/{lesson_id}", dependencies=[Depends(JWTBearer())])
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_private_lesson(db, lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return {"detail": f"Private lesson {lesson_id} deleted"}

@router.patch("/private-lessons/{lesson_id}", response_model=PrivateLessonOut, dependencies=[Depends(JWTBearer())])
async def update_lesson(lesson_id: int, lesson: PrivateLessonUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_private_lesson(db, lesson_id, lesson)
    if not updated:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return updated

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
