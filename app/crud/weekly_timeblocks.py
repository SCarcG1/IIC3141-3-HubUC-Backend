from app.models.weekly_timeblock import WeeklyTimeblock
from app.schemas.weekly_timeblock import WeeklyTimeblockCreate, WeeklyTimeblockOut
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_weekly_timeblock(
    db: AsyncSession,
    weekly_timeblock_data: WeeklyTimeblockCreate,
    user_id: int
) -> WeeklyTimeblockOut:
    weekly_timeblock = WeeklyTimeblock(**weekly_timeblock_data.model_dump(), user_id=user_id)
    db.add(weekly_timeblock)
    await db.commit()
    await db.refresh(weekly_timeblock)
    return weekly_timeblock


async def read_all_weekly_timeblocks_of_user(db: AsyncSession, user_id: int) -> list[WeeklyTimeblockOut]:
    query = select(WeeklyTimeblock).where(WeeklyTimeblock.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()
