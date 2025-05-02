from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    student = "student"
    tutor = "tutor"
    admin = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
