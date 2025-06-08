from app.database import Base
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import joinedload, Mapped, mapped_column, relationship, selectinload


class PrivateLesson(Base):
    __tablename__ = "privatelesson"

    id: Mapped[int] = mapped_column(primary_key=True)

    tutor_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    tutor = relationship("User", back_populates="private_lessons")

    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course = relationship("Course", back_populates="private_lessons")

    start_time: Mapped[datetime] = mapped_column(DateTime)

    end_time: Mapped[datetime] = mapped_column(DateTime)

    price: Mapped[int] = mapped_column()

    reservations = relationship("Reservation", back_populates="private_lesson")

    @classmethod
    def get_eager_loading_options(cls, course = True, reservations = False, tutor = True):
        """
        Returns a list of options that can be passed to SQLAlchemy's `options()` method,
        which will eagerly load the related entities for this model,
        so that they can be accessed with, for example, `lesson.tutor` or `lesson.course`.

        Warning: if you want to replicate this method for other models,
        consider that `joinedload` is preferred for many-to-one relationships,
        while `selectinload` is preferred for one-to-many relationships.
        """
        eager_loading_options = []
        if course:
            eager_loading_options.append(joinedload(cls.course))
        if reservations:
            eager_loading_options.append(selectinload(cls.reservations))
        if tutor:
            eager_loading_options.append(joinedload(cls.tutor))
        return eager_loading_options
