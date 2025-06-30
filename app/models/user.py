from app.database import Base
from enum import Enum as PythonEnum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional


class UserRole(str, PythonEnum):
    student = "student"
    tutor = "tutor"
    admin = "admin"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student)

    private_lessons = relationship("PrivateLesson", back_populates="tutor")
    reservations = relationship("Reservation", back_populates="student")
    weekly_timeblocks = relationship("WeeklyTimeblock", back_populates="user")
