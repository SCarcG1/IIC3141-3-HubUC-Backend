from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.user import UserCRUD
from app.crud.weekly_timeblocks import (
    create_weekly_timeblock,
    read_weekly_timeblocks_of_user,
    remove_weekly_timeblock_that_belongs_to_user
)
from app.schemas.single_timeblock import SingleTimeblock
from app.schemas.weekly_timeblock import (
    WeeklyTimeblockCreate,
    WeeklyTimeblockOut
)
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


# CREATE


@router.post("/weekly-timeblocks", response_model=WeeklyTimeblockOut)
async def post_weekly_timeblock(
    weekly_timeblock_data: WeeklyTimeblockCreate,
    jwt_payload: dict = Depends(JWTBearer()),
    db: AsyncSession = Depends(get_db)
):
    user_id = jwt_payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="User ID (`id`) not found in JWT payload"
        )
    return await create_weekly_timeblock(db, weekly_timeblock_data, user_id)


# READ


@router.get(
    "/weekly-timeblocks/{user_id}",
    description=(
        "Get the weekly timeblocks of a user. "
        "Returns all weekly timeblocks by default, "
        "or only those valid on a specific date if `on_date` is provided."
    ),
    response_model=list[WeeklyTimeblockOut]
)
async def get_weekly_timeblocks_of_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    on_date: date = None
):
    return await read_weekly_timeblocks_of_user(db, user_id, on_date)


@router.get(
    "/timeblocks/{user_id}",
    description=(
        "Get the individual, available timeblocks of a user. "
        "Unlike the weekly version, the on_date parameter is required "
        "in this endpoint, as sending all of the individual timeblocks "
        "would be too much data."
    ),
    response_model=list[SingleTimeblock]
)
async def get_available_timeblocks_of_user(
    user_id: int,
    on_date: date,
    db_session: AsyncSession = Depends(get_db),
):
    weekly_timeblocks = await read_weekly_timeblocks_of_user(
        db_session,
        user_id,
        on_date
    )
    blocks = SingleTimeblock.from_weekly_timeblocks(weekly_timeblocks)
    user_crud = UserCRUD(db_session)
    available_blocks = []
    for block in blocks:
        if await user_crud.is_user_available_on_datetime_range(
            user_id,
            block.start_time,
            block.end_time
        ):
            available_blocks.append(block)
    return available_blocks


# DELETE


@router.delete("/weekly-timeblocks/{weekly_timeblock_id}")
async def delete_weekly_timeblock(
    weekly_timeblock_id: int,
    jwt_payload: dict = Depends(JWTBearer()),
    db_session: AsyncSession = Depends(get_db)
):
    user_id = jwt_payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="User ID not found in JWT payload"
        )
    return await remove_weekly_timeblock_that_belongs_to_user(
        db_session,
        weekly_timeblock_id,
        user_id
    )
