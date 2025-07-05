from app.api.routes import get_db
from app.crud.course import (
  get_all_courses,
  get_course_by_id,
  create_course,
  update_course,
  delete_course
)
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.get("/courses", response_model=list[CourseOut])
async def read_courses(db: AsyncSession = Depends(get_db)):
    return await get_all_courses(db)


@router.get("/courses/{course_id}", response_model=CourseOut)
async def read_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/courses", response_model=CourseOut)
async def create_new_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db)
):
    return await create_course(db, course)


@router.put("/courses/{course_id}", response_model=CourseOut)
async def update_existing_course(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated = await update_course(db, course_id, course)
    if not updated:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated


@router.delete("/courses/{course_id}")
async def delete_existing_course(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted = await delete_course(db, course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"detail": f"Course {course_id} deleted"}
