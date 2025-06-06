from app.database import Base
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PrivateLesson(Base):
    __tablename__ = "privatelesson"

    id: Mapped[int] = mapped_column(primary_key=True)

    tutor_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    tutor = relationship("user", back_populates="private_lessons")

    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course = relationship("course", back_populates="private_lessons")

    start_time: Mapped[datetime] = mapped_column(DateTime)
    
    end_time: Mapped[datetime] = mapped_column(DateTime)
    
    price: Mapped[int] = mapped_column()

    reservations = relationship("reservation", back_populates="private_lesson")
