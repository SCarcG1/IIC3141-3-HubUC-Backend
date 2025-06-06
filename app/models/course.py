from app.database import Base
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)

    private_lessons = relationship("privatelesson", back_populates="course")
