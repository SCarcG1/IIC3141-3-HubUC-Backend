from app.database import Base
from app.schemas.reservation import ReservationStatus
from datetime import datetime
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Reservation(Base):
    __tablename__ = "reservation"

    # Primary key:
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign keys:
    private_lesson_id: Mapped[int] = mapped_column(
        ForeignKey("privatelesson.id")
    )
    private_lesson = relationship(
        "PrivateLesson",
        back_populates="reservations"
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=True,
    )
    student = relationship("User", back_populates="reservations")

    # Attributes:
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus))
    start_time: Mapped[datetime] = mapped_column()
    end_time: Mapped[datetime] = mapped_column()
