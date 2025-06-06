from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.private_lesson import PrivateLesson
from app.schemas.private_lesson import PrivateLessonCreate

async def get_all_private_lessons(db: AsyncSession):
    result = await db.execute(select(PrivateLesson))
    return result.scalars().all()

async def get_private_lesson_by_id(db: AsyncSession, lesson_id: int):
    result = await db.execute(select(PrivateLesson).where(PrivateLesson.id == lesson_id))
    return result.scalar_one_or_none()

async def create_private_lesson(db: AsyncSession, lesson: PrivateLessonCreate):
    db_lesson = PrivateLesson(**lesson.dict())
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson
