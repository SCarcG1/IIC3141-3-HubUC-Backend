from app.crud.user import UserCRUD
from app.crud.weekly_timeblocks import read_weekly_timeblocks_of_user
from app.models.private_lesson import PrivateLesson
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import ReservationStatus
from app.schemas.user import UserRole
from app.schemas.single_timeblock import SingleTimeblock
from app.utilities.weekly_timeblocks import (
    are_start_time_and_end_time_inside_connected_timeblocks
)
from datetime import date, datetime
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class AvailabilityService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.user_crud = UserCRUD(db_session)

    async def get_available_single_timeblocks_of_user(
        self,
        user_id: int,
        on_date: date
    ):
        weekly_timeblocks = await read_weekly_timeblocks_of_user(
            self.db_session, user_id, on_date
        )
        blocks = SingleTimeblock.from_weekly_timeblocks(weekly_timeblocks)
        available_blocks = []
        for block in blocks:
            if await self.is_user_available_on_datetime_range(
                user_id=user_id,
                from_datetime=datetime.combine(on_date, block.start_hour),
                to_datetime=datetime.combine(on_date, block.end_hour),
            ):
                available_blocks.append(block)
        return available_blocks

    async def is_user_available_on_datetime_range(
        self,
        user_id: int,
        from_datetime: datetime,
        to_datetime: datetime
    ):
        user: User = await self.user_crud.read_by_id(user_id)
        if user.role == UserRole.tutor:
            return await self.__is_tutor_available_on_datetime_range(
                user_id,
                from_datetime,
                to_datetime,
            )
        return await self.__is_student_available_on_datetime_range(
            user_id,
            from_datetime,
            to_datetime,
        )

    async def __is_tutor_available_on_datetime_range(
        self,
        user_id: int,
        from_datetime: datetime,
        to_datetime: datetime
    ):
        user: User = await self.user_crud.read_full_data_by_id(
            user_id, UserRole.tutor
        )
        # If the tutor has no valid WeeklyTimeblocks that cover the whole
        # range, then the tutor is not available.
        if not are_start_time_and_end_time_inside_connected_timeblocks(
            from_datetime,
            to_datetime,
            user.weekly_timeblocks
        ):
            return False
        # If the tutor has an accepted reservation in any time within the
        # range, then the tutor is not available.
        lessons: list[PrivateLesson] = user.private_lessons
        for lesson in lessons:
            reservations = await self.db_session.execute(
                select(Reservation).where(
                    Reservation.private_lesson_id == lesson.id,
                    Reservation.status == ReservationStatus.ACCEPTED,
                    or_(
                        and_(
                            from_datetime <= Reservation.start_time,
                            Reservation.start_time < to_datetime,
                            to_datetime <= Reservation.end_time
                        ),
                        and_(
                            Reservation.start_time <= from_datetime,
                            to_datetime <= Reservation.end_time
                        ),
                        and_(
                            Reservation.start_time <= from_datetime,
                            from_datetime < Reservation.end_time,
                            Reservation.end_time <= to_datetime
                        )
                    )
                )
            )
            reservations = reservations.scalars().all()
            if len(reservations) > 0:
                return False
        # Otherwise, the tutor is available.
        return True

    async def __is_student_available_on_datetime_range(
        self,
        user_id: int,
        from_datetime: datetime,
        to_datetime: datetime,
    ):
        # If the student has an accepted reservation in any time within the
        # range, they are not available.
        reservations = await self.db_session.execute(
            select(Reservation).where(
                Reservation.student_id == user_id,
                Reservation.status == ReservationStatus.ACCEPTED,
                or_(
                    and_(
                        from_datetime <= Reservation.start_time,
                        Reservation.start_time < to_datetime,
                        to_datetime <= Reservation.end_time
                    ),
                    and_(
                        Reservation.start_time <= from_datetime,
                        to_datetime <= Reservation.end_time
                    ),
                    and_(
                        Reservation.start_time <= from_datetime,
                        from_datetime < Reservation.end_time,
                        Reservation.end_time <= to_datetime
                    )
                )
            )
        )
        if reservations.scalars().first():
            return False
        # Otherwise, the student is available.
        return True
