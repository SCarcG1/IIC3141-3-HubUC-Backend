from app.database import Base
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PrivateClass(Base):
    __tablename__ = "privateclass"

    id: Mapped[int] = mapped_column(primary_key=True)

    tutor_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    tutor = relationship("user", back_populates="private_classes")

    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course = relationship("course", back_populates="private_classes")

    start_time: Mapped[datetime] = mapped_column(DateTime)
    
    end_time: Mapped[datetime] = mapped_column(DateTime)
    
    price: Mapped[int] = mapped_column()

    reservations = relationship("reservation", back_populates="private_class")
