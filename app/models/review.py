from app.database import Base
from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)

    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservation.id"))
    reservation = relationship("Reservation")

    content: Mapped[str] = mapped_column(Text)
    
    rating: Mapped[int] = mapped_column()
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
