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
    start = lesson.start_time.replace(tzinfo=None)
    end = lesson.end_time.replace(tzinfo=None)

    db_lesson = PrivateLesson(
        tutor_id=lesson.tutor_id,
        course_id=lesson.course_id,
        start_time=start,
        end_time=end,
        price=lesson.price
    )
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson
