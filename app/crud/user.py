from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.auth.auth_handler import get_password_hash

async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        email=user.email,
        name=user.name,
        password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_full_data_of_user(db: AsyncSession, user_id: int, user_role: str):
    if user_role not in ['tutor', 'student']:
        raise ValueError("Invalid user role. Must be 'tutor' or 'student'.")
    
    if user_role == 'tutor':
        query = (
            select(User)
            .where(User.id == user_id, User.role == 'tutor')
            .options(selectinload(User.private_lessons), selectinload(User.weekly_timeblocks))
        )
    elif user_role == 'student':
        query = (
            select(User)
            .where(User.id == user_id, User.role == 'student')
            .options(selectinload(User.reservations), selectinload(User.weekly_timeblocks))
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_all_users_by_role(db: AsyncSession, role: str):
    result = await db.execute(select(User).where(User.role == role))
    return result.scalars().all()

async def get_tutor_of_private_lesson(db: AsyncSession, lesson_id: int):
    query = (
        select(User)
        .join(User.private_lessons)
        .where(User.role == 'tutor', User.private_lessons.any(id=lesson_id))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_student_of_reservation(db: AsyncSession, reservation_id: int):
    query = (
        select(User)
        .join(User.reservations)
        .where(User.role == 'student', User.reservations.any(id=reservation_id))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None

    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.password is not None:
        db_user.password = get_password_hash(user_update.password)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


class UserCRUD:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, user_data: UserCreate):
        return await create_user(self.db_session, user_data)

    async def read_all(self):
        return await get_all_users(self.db_session)

    async def read_by_email(self, email: str):
        return await get_user_by_email(self.db_session, email)

    async def read_by_id(self, user_id: int):
        return await get_user_by_id(self.db_session, user_id)

    async def read_full_data_by_id(self, user_id: int, user_role: str):
        return await get_full_data_of_user(self.db_session, user_id, user_role)

    async def read_by_role(self, role: str):
        return await get_all_users_by_role(self.db_session, role)

    async def update(self, user_id: int, user_data: UserUpdate):
        return await update_user(self.db_session, user_id, user_data)
