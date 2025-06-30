from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReviewBase(BaseModel):
    reservation_id: int
    content: str = Field(..., min_length=1, max_length=1000)
    rating: int = Field(..., ge=1, le=5)

    class Config:
        from_attributes = True


class ReviewCreate(ReviewBase):
    pass


class ReviewOut(ReviewBase):
    id: int
    created_at: datetime


class ReviewUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)

    class Config:
        from_attributes = True


class ReviewExtendedOut(ReviewOut):
    reservation: dict  # Puede ser ReservationOut si se necesita más detalle 