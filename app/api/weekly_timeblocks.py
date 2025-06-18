from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.weekly_timeblocks import create_weekly_timeblock, read_weekly_timeblocks_of_user
from app.schemas.weekly_timeblock import WeeklyTimeblockCreate, WeeklyTimeblockOut
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
        raise HTTPException(status_code=400, detail="User ID (`id`) not found in JWT payload")
    return await create_weekly_timeblock(db, weekly_timeblock_data, user_id)


# READ


@router.get(
    "/weekly-timeblocks/{user_id}",
    description="Get the weekly timeblocks of a user. "
        + "Returns all weekly timeblocks by default, "
        + "or only those valid on a specific date if `on_date` is provided.",
    response_model=list[WeeklyTimeblockOut]
)
async def get_weekly_timeblocks_of_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    on_date: date = None
):
    return await read_weekly_timeblocks_of_user(db, user_id, on_date)


# UPDATE


# DELETE
