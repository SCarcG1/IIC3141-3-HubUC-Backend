from app.database import Base
from app.schemas.weekday import Weekday
from datetime import datetime
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class WeeklyTimeblock(Base):
    __tablename__ = "weeklytimeblock"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user = relationship("User", back_populates="weekly_timeblocks")

    weekday: Mapped[Weekday] = mapped_column(Enum(Weekday))
    start_hour: Mapped[int] = mapped_column()
    end_hour: Mapped[int] = mapped_column()
    valid_from: Mapped[datetime] = mapped_column()
    valid_until: Mapped[datetime] = mapped_column()
