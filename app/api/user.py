from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.user import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    get_full_data_of_user,
    get_all_users_by_role,
    get_tutor_of_private_lesson,
    get_student_of_reservation,
    update_user
)
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional

router = APIRouter()

@router.get("/users", response_model=List[UserOut])
async def read_all_users(db: AsyncSession = Depends(get_db)):
    users = await get_all_users(db)
    if not users:
        raise HTTPException(status_code=404, detail="No Users found")
    return users

@router.get("/users/{user_id}", response_model=UserOut)
async def read_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/email/{email}", response_model=UserOut)
async def read_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/full-data/{user_id}", response_model=UserOut)
async def read_full_data_of_user(user_id: int, user_role: str, db: AsyncSession = Depends(get_db)):
    user = await get_full_data_of_user(db, user_id, user_role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/role/{role}", response_model=List[UserOut])
async def read_all_users_by_role(role: str, db: AsyncSession = Depends(get_db)):
    if role not in ['tutor', 'student', 'admin']:
        raise HTTPException(status_code=400, detail="Invalid role specified")
    
    users = await get_all_users_by_role(db, role)
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found with role {role}")
    
    return users

@router.get("/users/{lesson_id}/tutor", response_model=UserOut)
async def read_tutor_of_private_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    tutor = await get_tutor_of_private_lesson(db, lesson_id)
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found for the given private lesson")
    return tutor

@router.get("/users/{reservation_id}/student", response_model=UserOut)
async def read_student_of_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    student = await get_student_of_reservation(db, reservation_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found for the given reservation")
    return student

@router.patch("/users/{user_id}", response_model=UserOut, dependencies=[Depends(JWTBearer())])
async def update_user_endpoint(user_id: int, user_update: UserCreate, db: AsyncSession = Depends(get_db), jwt_payload: dict = Depends(JWTBearer())):
    if jwt_payload.get("role") != "admin" and jwt_payload.get("id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    updated_user = await update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user