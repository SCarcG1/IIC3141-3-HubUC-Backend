from app.database import Base
from enum import Enum as PythonEnum
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ReservationStatus(str, PythonEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Reservation(Base):
    __tablename__ = "reservation"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    student = relationship("user", back_populates="reservations")

    private_class_id: Mapped[int] = mapped_column(ForeignKey("privateclass.id"))
    private_class = relationship("privateclass", back_populates="reservations")

    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus))
