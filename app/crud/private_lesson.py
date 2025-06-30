from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.schemas.private_lesson import OfferStatus, PrivateLessonCreate
from app.schemas.reservation import ReservationStatus
from datetime import datetime
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_private_lessons(db: AsyncSession):
    eager_loading_options = PrivateLesson.get_eager_loading_options(
        course=True,
        reservations=False,
        tutor=True
    )
    query = select(PrivateLesson).options(*eager_loading_options)
    result = await db.execute(query)
    private_lessons = result.scalars().all()
    return private_lessons


async def get_private_lesson_by_id(db: AsyncSession, lesson_id: int):
    query = (
        select(PrivateLesson)
        .where(PrivateLesson.id == lesson_id)
        .options(*PrivateLesson.get_eager_loading_options(
            course=True, tutor=True, reservations=False)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tutors_private_lessons(db: AsyncSession, tutor_id: int):
    result = await db.execute(
        select(PrivateLesson).where(PrivateLesson.tutor_id == tutor_id)
    )
    return result.scalars().all()


async def create_private_lesson(db: AsyncSession, lesson: PrivateLessonCreate):
    db_lesson = PrivateLesson(
        tutor_id=lesson.tutor_id,
        course_id=lesson.course_id,
        price=lesson.price,
        description=lesson.description
    )
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson


async def update_private_lesson(
    db: AsyncSession,
    lesson_id: int,
    lesson: PrivateLessonCreate
):
    result = await db.execute(
        select(PrivateLesson).where(PrivateLesson.id == lesson_id)
    )
    db_lesson = result.scalar_one_or_none()
    if not db_lesson:
        return None

    for key, value in lesson.model_dump(exclude_unset=True).items():
        setattr(db_lesson, key, value)

    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson


async def get_filtered_private_lessons_paginated(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    course_id: int | None = None,
    tutor_id: int | None = None,
    include_closed_lessons: bool = False
):
    filters = []
    if course_id is not None:
        filters.append(PrivateLesson.course_id == course_id)
    if tutor_id is not None:
        filters.append(PrivateLesson.tutor_id == tutor_id)
    if not include_closed_lessons:
        filters.append(PrivateLesson.offer_status != OfferStatus.CLOSED)

    query = select(PrivateLesson).options(
        *PrivateLesson.get_eager_loading_options(course=True, tutor=True)
    )
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


class PrivateLessonCRUD:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    # CREATE

    async def create(self, lesson_data: PrivateLessonCreate):
        return await create_private_lesson(self.db_session, lesson_data)

    # READ

    async def read_all(self):
        eager_loading_options = PrivateLesson.get_eager_loading_options(
            course=True,
            reservations=False,
            tutor=True
        )
        query = select(PrivateLesson).options(*eager_loading_options)
        result = await self.db_session.execute(query)
        private_lessons = result.scalars().all()
        return private_lessons

    async def read_open_lessons(self):
        eager_loading_options = PrivateLesson.get_eager_loading_options(
            course=True,
            reservations=False,
            tutor=True
        )
        query = select(
            PrivateLesson
        ).where(
            PrivateLesson.offer_status == OfferStatus.OPEN
        ).options(
            *eager_loading_options
        )
        result = await self.db_session.execute(query)
        private_lessons = result.scalars().all()
        return private_lessons

    async def read_by_id(self, lesson_id: int):
        return await get_private_lesson_by_id(self.db_session, lesson_id)

    async def read_by_tutor_id(self, tutor_id: int):
        return await get_tutors_private_lessons(self.db_session, tutor_id)

    async def read_page(
        self,
        page=1,
        page_size=10,
        course_id: int | None = None,
        tutor_id: int | None = None,
        include_closed_lessons: bool = False
    ):
        return await get_filtered_private_lessons_paginated(
            self.db_session, page, page_size, course_id, tutor_id,
            include_closed_lessons
        )

    # UPDATE

    async def update(self, lesson_id: int, lesson_data: PrivateLessonCreate):
        return await update_private_lesson(
            self.db_session,
            lesson_id,
            lesson_data
        )

    # DELETE

    async def close(self, lesson_id: int):
        '''
        For a private lesson, "delete" means to close the lesson offer.
        Thus, `close()` is used as the `DELETE` of the private lessons' CRUD.
        '''
        lesson = await self.db_session.get(PrivateLesson, lesson_id)
        lesson.offer_status = OfferStatus.CLOSED
        await self.db_session.commit()
        await self.db_session.refresh(lesson)
        return lesson

    # Utility methods

    async def does_private_lesson_belong_to_user(
        self,
        lesson_id: int,
        user_id: int
    ):
        lesson = await self.db_session.get(PrivateLesson, lesson_id)
        if not lesson:
            return False
        return lesson.tutor_id == user_id

    async def does_private_lesson_have_upcoming_reservations(
        self,
        lesson_id: int
    ):
        query = select(Reservation).where(
            Reservation.private_lesson_id == lesson_id,
            Reservation.start_time > datetime.now(),
            Reservation.status == ReservationStatus.ACCEPTED,
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None
