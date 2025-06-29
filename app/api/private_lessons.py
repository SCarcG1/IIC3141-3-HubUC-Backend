from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.private_lesson import (
    create_private_lesson,
    delete_private_lesson,
    get_all_private_lessons,
    get_filtered_private_lessons_paginated,
    get_private_lesson_by_id,
    update_private_lesson,
)
from app.schemas.private_lesson import (
    PrivateLessonCreate,
    PrivateLessonExtendedOut,
    PrivateLessonOut,
    PrivateLessonPage,
    PrivateLessonUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional

router = APIRouter()

@router.post("/private-lessons", response_model=PrivateLessonOut, dependencies=[Depends(JWTBearer())])
async def create_lesson(lesson: PrivateLessonCreate, db: AsyncSession = Depends(get_db)):
    return await create_private_lesson(db, lesson)

@router.get("/private-lessons", response_model=List[PrivateLessonExtendedOut])
async def read_all_private_lessons(db: AsyncSession = Depends(get_db)):
    return await get_all_private_lessons(db)

@router.get("/private-lessons/search", response_model=PrivateLessonPage)
async def search_private_lessons(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    course_id: Optional[int] = None,
    tutor_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    return await get_filtered_private_lessons_paginated(
        db=db,
        page=page,
        page_size=page_size,
        course_id=course_id,
        tutor_id=tutor_id
    )

@router.get("/private-lessons/{lesson_id}", response_model=PrivateLessonExtendedOut)
async def read_private_lesson_by_id(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await get_private_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return lesson

@router.patch("/private-lessons/{lesson_id}", response_model=PrivateLessonOut, dependencies=[Depends(JWTBearer())])
async def update_lesson(lesson_id: int, lesson: PrivateLessonUpdate, db: AsyncSession = Depends(get_db), tutor: dict = Depends(JWTBearer())):
    # Ensure that the user is a tutor
    if tutor.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden: You must be a tutor to update lessons")
    
    # Ensure that the tutor is the one updating the reservation
    if lesson.tutor_id is not None and lesson.tutor_id != (tutor.get("user_id") or tutor.get("id")):
        raise HTTPException(status_code=403, detail="Forbidden: You can only update your own lessons")
    
    # Ensure the lesson sent has the tutor_id
    if lesson.tutor_id is None:
        lesson.tutor_id = tutor.get("user_id") or tutor.get("id")

    updated = await update_private_lesson(db, lesson_id, lesson)
    if not updated:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return updated

@router.delete("/private-lessons/{lesson_id}", dependencies=[Depends(JWTBearer())])
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db), tutor: dict = Depends(JWTBearer())):
    # Ensure that the user is a tutor
    if tutor.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Forbidden: You must be a tutor to delete lessons")
    deleted = await delete_private_lesson(db, lesson_id, tutor["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Private lesson not found")
    return {"detail": f"Private lesson {lesson_id} deleted"}
