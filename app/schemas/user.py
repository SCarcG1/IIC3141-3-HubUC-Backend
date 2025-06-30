from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    student = "student"
    tutor = "tutor"
    admin = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    number: Optional[str] = None
    password: str
    role: UserRole

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    number: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    number: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True