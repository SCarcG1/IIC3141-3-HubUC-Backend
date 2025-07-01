from app.api.routes import get_db
from app.auth.auth_bearer import JWTBearer
from app.crud.review import (
    create_review,
    delete_review,
    does_review_belong_to_user,
    get_all_reviews,
    get_review_by_id,
    get_reviews_by_private_lesson_id,
    get_reviews_by_student_id,
    get_reviews_by_tutor_id,
    update_review,
)
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter()


# CREATE
@router.post(
    "/reviews",
    response_model=ReviewOut,
    dependencies=[Depends(JWTBearer())],
    status_code=status.HTTP_201_CREATED,
)
async def post_review(
    review: ReviewCreate,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Crear una nueva review"""
    # Solo estudiantes pueden crear reviews
    if jwt_payload.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create reviews"
        )
    
    return await create_review(db_session, review)


# READ
@router.get(
    "/reviews",
    response_model=List[ReviewOut],
    dependencies=[Depends(JWTBearer())],
)
async def get_reviews(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener todas las reviews"""
    return await get_all_reviews(db_session)


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewOut,
    dependencies=[Depends(JWTBearer())],
)
async def get_review(
    review_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener una review específica por ID"""
    review = await get_review_by_id(db_session, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review


@router.get(
    "/reviews/tutor/{tutor_id}",
    response_model=List[ReviewOut],
    dependencies=[Depends(JWTBearer())],
)
async def get_tutor_reviews(
    tutor_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener todas las reviews de un tutor específico"""
    return await get_reviews_by_tutor_id(db_session, tutor_id)


@router.get(
    "/reviews/student/{student_id}",
    response_model=List[ReviewOut],
    dependencies=[Depends(JWTBearer())],
)
async def get_student_reviews(
    student_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener todas las reviews de un estudiante específico"""
    return await get_reviews_by_student_id(db_session, student_id)


@router.get(
    "/reviews/lesson/{private_lesson_id}",
    response_model=List[ReviewOut],
    dependencies=[Depends(JWTBearer())],
)
async def get_lesson_reviews(
    private_lesson_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener todas las reviews de una lección privada específica"""
    return await get_reviews_by_private_lesson_id(db_session, private_lesson_id)


@router.get(
    "/reviews/my-reviews",
    response_model=List[ReviewOut],
    dependencies=[Depends(JWTBearer())],
)
async def get_my_reviews(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Obtener las reviews del usuario autenticado"""
    user_id = jwt_payload.get("id") or jwt_payload.get("user_id")
    user_role = jwt_payload.get("role")
    
    if user_role == "student":
        return await get_reviews_by_student_id(db_session, user_id)
    elif user_role == "tutor":
        return await get_reviews_by_tutor_id(db_session, user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and tutors can view reviews"
        )


# UPDATE
@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewOut,
    dependencies=[Depends(JWTBearer())],
)
async def patch_review(
    review_id: int,
    review_update: ReviewUpdate,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Actualizar una review existente"""
    user_id = jwt_payload.get("id") or jwt_payload.get("user_id")
    user_role = jwt_payload.get("role")
    
    # Verificar que el usuario puede modificar esta review
    can_modify = await does_review_belong_to_user(db_session, review_id, user_id, user_role)
    if not can_modify:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own reviews"
        )
    
    updated_review = await update_review(db_session, review_id, review_update)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return updated_review


# DELETE
@router.delete(
    "/reviews/{review_id}",
    dependencies=[Depends(JWTBearer())],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review_endpoint(
    review_id: int,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: dict = Depends(JWTBearer()),
):
    """Eliminar una review"""
    user_id = jwt_payload.get("id") or jwt_payload.get("user_id")
    user_role = jwt_payload.get("role")
    
    # Verificar que el usuario puede eliminar esta review
    can_delete = await does_review_belong_to_user(db_session, review_id, user_id, user_role)
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )
    
    success = await delete_review(db_session, review_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        ) 