from app.models.private_lesson import PrivateLesson
from app.schemas.private_lesson import PrivateLessonCreate
from sqlalchemy.ext.asyncio import AsyncSession


async def create_private_lesson(db_session: AsyncSession, lesson_data: PrivateLessonCreate):
    db_lesson = PrivateLesson(**lesson_data.model_dump())
    db_session.add(db_lesson)
    await db_session.commit()
    await db_session.refresh(db_lesson)
    return db_lesson
