from fastapi import FastAPI
from app.api.routes import router
from app.database import init_db, SessionLocal
from app.seeds.seed import seed_data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    # Ejecutar seeds después de inicializar la DB
    from sqlalchemy import text
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT to_regclass('public.\"user\"')"))
        if result.scalar():
            await seed_data(session)
        else:
            print("⏭️ Tabla 'user' no existe. Omitiendo seeds en startup.")

@app.get("/")
def read_root():
    return {"message": "FastAPI + PostgreSQL on Render"}

app.include_router(router)
