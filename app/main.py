import json

from fastapi import FastAPI, HTTPException, Request
from starlette.responses import Response, JSONResponse

from app.routers import auth
from app.dependencies import lifespan

app = FastAPI(lifespan=lifespan)

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
app.include_router(auth.router, prefix="/auth")
