from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.private_lesson import PrivateLessonCRUD
from app.schemas.private_lesson import (
    PrivateLessonCreate,
    PrivateLessonExtendedOut,
    PrivateLessonOut,
    PrivateLessonPage,
    PrivateLessonUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional


router = APIRouter()


# CREATE


@router.post(
    "/private-lessons",
    response_model=PrivateLessonOut,
    dependencies=[Depends(JWTBearer())]
)
async def post_lesson(
    lesson: PrivateLessonCreate,
    db_session: AsyncSession = Depends(get_db)
):
    crud = PrivateLessonCRUD(db_session)
    return await crud.create(lesson)


# READ


@router.get(
    "/private-lessons",
    response_model=List[PrivateLessonExtendedOut]
)
async def read_all_private_lessons(
    db_session: AsyncSession = Depends(get_db),
    include_closed_lessons: bool = False
):
    crud = PrivateLessonCRUD(db_session)
    if include_closed_lessons:
        return await crud.read_all()
    return await crud.read_open_lessons()


@router.get("/private-lessons/search", response_model=PrivateLessonPage)
async def search_private_lessons(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    course_id: Optional[int] = None,
    tutor_id: Optional[int] = None,
    include_closed_lessons: bool = False,
    db_session: AsyncSession = Depends(get_db)
):
    crud = PrivateLessonCRUD(db_session)
    return await crud.read_page(
        page, page_size, course_id, tutor_id, include_closed_lessons
    )


@router.get(
    "/private-lessons/{lesson_id}",
    response_model=PrivateLessonExtendedOut
)
async def read_private_lesson_by_id(
    lesson_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    crud = PrivateLessonCRUD(db_session)
    lesson = await crud.read_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return lesson


# UPDATE


@router.patch(
    "/private-lessons/{lesson_id}",
    response_model=PrivateLessonOut,
    dependencies=[Depends(JWTBearer())]
)
async def update_lesson(
    lesson_id: int,
    lesson: PrivateLessonUpdate,
    db_session: AsyncSession = Depends(get_db)
):
    crud = PrivateLessonCRUD(db_session)
    updated = await crud.update(lesson_id, lesson)
    if not updated:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return updated


# DELETE


@router.delete(
    path="/private-lessons/{lesson_id}",
    description=(
        "This endpoint doesn't actually delete the lesson; "
        "it sets its offer status to \"closed\" so it "
        "won't be available for booking anymore."
    ),
    response_model=PrivateLessonOut,
)
async def close_lesson(
    lesson_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer())
):
    crud = PrivateLessonCRUD(db_session)
    user_id = jwt_payload.get("id")
    if not await crud.does_private_lesson_belong_to_user(lesson_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Lesson {lesson_id} does not belong to user {user_id}"
        )
    lesson = await crud.close(lesson_id)
    return lesson
