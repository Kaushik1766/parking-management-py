from fastapi import FastAPI
from app.routers import auth
from app.dependencies import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/auth")
