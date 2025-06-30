from app.models.review import Review
from app.models.reservation import Reservation
from app.schemas.review import ReviewCreate, ReviewUpdate
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional


async def create_review(db: AsyncSession, review_data: ReviewCreate) -> Review:
    """Crear una nueva review"""
    # Verificar que la reservación existe
    reservation = await db.get(Reservation, review_data.reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=404,
            detail=f"Reservation with ID {review_data.reservation_id} not found"
        )
    
    # Verificar que no existe ya una review para esta reservación
    existing_review = await db.execute(
        select(Review).where(Review.reservation_id == review_data.reservation_id)
    )
    if existing_review.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A review already exists for this reservation"
        )
    
    review = Review(**review_data.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def get_review_by_id(db: AsyncSession, review_id: int) -> Optional[Review]:
    """Obtener una review por ID"""
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.reservation),
        )
    )
    return result.scalar_one_or_none()


async def get_all_reviews(db: AsyncSession) -> List[Review]:
    """Obtener todas las reviews"""
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.reservation),
        )
    )
    return result.scalars().all()


async def get_reviews_by_tutor_id(db: AsyncSession, tutor_id: int) -> List[Review]:
    """Obtener todas las reviews de un tutor específico"""
    from app.models.private_lesson import PrivateLesson
    result = await db.execute(
        select(Review)
        .join(Reservation)
        .join(PrivateLesson)
        .where(PrivateLesson.tutor_id == tutor_id)
        .options(
            selectinload(Review.reservation),
        )
    )
    return result.scalars().all()


async def get_reviews_by_student_id(db: AsyncSession, student_id: int) -> List[Review]:
    """Obtener todas las reviews de un estudiante específico"""
    result = await db.execute(
        select(Review)
        .join(Reservation)
        .where(Reservation.student_id == student_id)
        .options(
            selectinload(Review.reservation),
        )
    )
    return result.scalars().all()


async def get_reviews_by_private_lesson_id(db: AsyncSession, private_lesson_id: int) -> List[Review]:
    """Obtener todas las reviews de una lección privada específica"""
    result = await db.execute(
        select(Review)
        .join(Reservation)
        .where(Reservation.private_lesson_id == private_lesson_id)
        .options(
            selectinload(Review.reservation),
        )
    )
    return result.scalars().all()


async def update_review(db: AsyncSession, review_id: int, review_data: ReviewUpdate) -> Optional[Review]:
    """Actualizar una review existente"""
    review = await db.get(Review, review_id)
    if not review:
        return None
    
    update_data = review_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    
    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, review_id: int) -> bool:
    """Eliminar una review"""
    review = await db.get(Review, review_id)
    if not review:
        return False
    
    await db.delete(review)
    await db.commit()
    return True


async def does_review_belong_to_user(db: AsyncSession, review_id: int, user_id: int, user_role: str) -> bool:
    """Verificar si una review pertenece a un usuario específico"""
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.reservation),
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        return False
    
    if user_role == "student":
        return review.reservation.student_id == user_id
    elif user_role == "tutor":
        # Para verificar si es tutor, necesitamos hacer una consulta adicional
        from app.models.private_lesson import PrivateLesson
        private_lesson_result = await db.execute(
            select(PrivateLesson)
            .where(PrivateLesson.id == review.reservation.private_lesson_id)
        )
        private_lesson = private_lesson_result.scalar_one_or_none()
        return private_lesson and private_lesson.tutor_id == user_id
    
    return False 