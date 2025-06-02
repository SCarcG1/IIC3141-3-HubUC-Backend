from app.database import Base
from enum import Enum as PythonEnum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student)

    private_classes = relationship("privateclass", back_populates="tutor")
    reservations = relationship("reservation", back_populates="student")
