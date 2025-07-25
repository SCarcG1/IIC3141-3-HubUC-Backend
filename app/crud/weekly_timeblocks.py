from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekly_timeblock import (
    WeeklyTimeblockCreate,
    WeeklyTimeblockOut
)
from app.utilities.weekly_timeblocks import map_int_weekday_to_enum_weekday
from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_weekly_timeblock(
    db: AsyncSession,
    weekly_timeblock_data: WeeklyTimeblockCreate,
    user_id: int
) -> WeeklyTimeblockOut:
    valid_from = datetime(
        weekly_timeblock_data.valid_from.year,
        weekly_timeblock_data.valid_from.month,
        weekly_timeblock_data.valid_from.day,
        0, 0, 0
    )
    valid_until = datetime(
        weekly_timeblock_data.valid_until.year,
        weekly_timeblock_data.valid_until.month,
        weekly_timeblock_data.valid_until.day,
        23, 59, 59
    )
    weekly_timeblock = WeeklyTimeblock(
        user_id=user_id,
        weekday=weekly_timeblock_data.weekday,
        start_hour=weekly_timeblock_data.start_hour,
        end_hour=weekly_timeblock_data.end_hour,
        valid_from=valid_from,
        valid_until=valid_until
    )
    db.add(weekly_timeblock)
    await db.commit()
    await db.refresh(weekly_timeblock)
    return weekly_timeblock


async def read_weekly_timeblocks_of_user(
    db: AsyncSession,
    user_id: int,
    on_date: date = None,
) -> list[WeeklyTimeblockOut]:
    query = select(WeeklyTimeblock).where(WeeklyTimeblock.user_id == user_id)
    if on_date:
        weekday = map_int_weekday_to_enum_weekday(on_date.weekday())
        on_date = datetime(on_date.year, on_date.month, on_date.day)
        query = query.where(
            WeeklyTimeblock.weekday == weekday,
            WeeklyTimeblock.valid_from <= on_date,
            WeeklyTimeblock.valid_until >= on_date
        )
    result = await db.execute(query)
    return result.scalars().all()


async def remove_weekly_timeblock_that_belongs_to_user(
    db_session: AsyncSession,
    weekly_timeblock_id: int,
    user_id: int,
):
    weekly_timeblock = await db_session.get(
        WeeklyTimeblock,
        weekly_timeblock_id
    )
    if not weekly_timeblock:
        raise HTTPException(
            status_code=404,
            detail=f"Weekly timeblock with ID {weekly_timeblock_id} not found."
        )
    if weekly_timeblock.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Weekly timeblock ID {weekly_timeblock_id} "
                f"does not belong to user ID {user_id}."
            )
        )
    await db_session.delete(weekly_timeblock)
    await db_session.commit()
