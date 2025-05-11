from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    import app.models.user

    max_retries = 10
    retry_delay = 2  # segundos

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Conexión a la base de datos exitosa.")
            break
        except Exception as e:
            print(f"⏳ Intento {attempt} de conexión fallido: {e}")
            if attempt == max_retries:
                print("❌ No se pudo conectar a la base de datos después de varios intentos.")
                raise
            await asyncio.sleep(retry_delay)
