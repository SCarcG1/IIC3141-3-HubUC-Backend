from fastapi import FastAPI
from app.api.routes import router
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Agregar direccion de producción o descomentar linea de abajo
    # allow_origins=["*"],  # Descomentar para permitir todas las direcciones
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(router)
