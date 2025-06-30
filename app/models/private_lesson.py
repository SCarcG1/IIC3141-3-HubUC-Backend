from app.database import Base
from app.schemas.private_lesson import OfferStatus
from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import (
    joinedload,
    Mapped,
    mapped_column,
    relationship,
    selectinload
)
from typing import Optional


class PrivateLesson(Base):
    __tablename__ = "privatelesson"

    # Primary key:

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign keys and their relationships:

    tutor_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    tutor = relationship("User", back_populates="private_lessons")

    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course = relationship("Course", back_populates="private_lessons")

    # Attributes:

    price: Mapped[int] = mapped_column()

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    offer_status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus),
        default=OfferStatus.OPEN
    )

    # Other relationships (the key is in the other model):

    reservations = relationship("Reservation", back_populates="private_lesson")

    # Utility methods:

    @classmethod
    def get_eager_loading_options(
        cls,
        course=True,
        reservations=False,
        tutor=True
    ):
        eager_loading_options = []
        if course:
            eager_loading_options.append(joinedload(cls.course))
        if reservations:
            eager_loading_options.append(selectinload(cls.reservations))
        if tutor:
            eager_loading_options.append(joinedload(cls.tutor))
        return eager_loading_options
