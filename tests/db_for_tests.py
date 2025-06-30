from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


db_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
SessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    db_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_for_tests():
    async with SessionLocal() as session:
        yield session
