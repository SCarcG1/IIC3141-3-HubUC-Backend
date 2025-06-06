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

async def delete_private_lesson(db: AsyncSession, lesson_id: int):
    db_lesson = await db.execute(select(PrivateLesson).where(PrivateLesson.id == lesson_id))
    if db_lesson is None:
        return None
    await db.delete(db_lesson)
    await db.commit()
    return db_lesson

async def update_private_lesson(db: AsyncSession, lesson_id: int, lesson: PrivateLessonCreate):
    result = await db.execute(select(PrivateLesson).where(PrivateLesson.id == lesson_id))
    db_lesson = result.scalar_one_or_none()
    if not db_lesson:
        return None

    for key, value in lesson.dict(exclude_unset=True).items():
        setattr(db_lesson, key, value)

    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson

async def get_filtered_private_lessons_paginated(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    course_id: int | None = None,
    tutor_id: int | None = None
):
    filters = []
    if course_id is not None:
        filters.append(PrivateLesson.course_id == course_id)
    if tutor_id is not None:
        filters.append(PrivateLesson.tutor_id == tutor_id)

    query = select(PrivateLesson)
    count_query = select(func.count(PrivateLesson.id))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    lessons = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": lessons
    }
