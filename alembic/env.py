from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database import Base, async_session
import os

from app.models import course, private_lesson, reservation, review, user

from app.seeds.seed import seed_data

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = os.getenv("DATABASE_URL")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy.ext.asyncio import create_async_engine
    url = os.getenv("DATABASE_URL")
    connectable = create_async_engine(url, future=True)

    async def run():
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda conn: context.configure(
                    connection=conn, target_metadata=target_metadata
                )
            )
            await connection.run_sync(lambda conn: context.configure(connection=conn, target_metadata=target_metadata))
            await connection.run_sync(lambda _: context.run_migrations())

        async with async_session() as session:
            await seed_data(session)

    import asyncio
    asyncio.run(run())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
