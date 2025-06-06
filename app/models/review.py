from app.database import Base
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)

    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservation.id"))
    reservation = relationship("Reservation", back_populates="review")
    
    content: Mapped[str] = mapped_column(Text)
    
    rating: Mapped[int] = mapped_column()
