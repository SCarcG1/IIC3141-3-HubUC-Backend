from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.crud.user import create_user, get_user_by_email
from app.auth.auth_handler import verify_password, create_access_token
from app.auth.auth_bearer import JWTBearer
from typing import List

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

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
