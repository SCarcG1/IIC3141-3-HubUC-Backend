from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate

async def get_all_courses(db: AsyncSession):
    result = await db.execute(select(Course))
    return result.scalars().all()

async def get_course_by_id(db: AsyncSession, course_id: int):
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()

async def create_course(db: AsyncSession, course: CourseCreate):
    db_course = Course(**course.dict())
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course

async def update_course(db: AsyncSession, course_id: int, course: CourseUpdate):
    db_course = await get_course_by_id(db, course_id)
    if db_course is None:
        return None
    for field, value in course.dict().items():
        setattr(db_course, field, value)
    await db.commit()
    await db.refresh(db_course)
    return db_course

async def delete_course(db: AsyncSession, course_id: int):
    db_course = await get_course_by_id(db, course_id)
    if db_course is None:
        return None
    await db.delete(db_course)
    await db.commit()
    return db_course
