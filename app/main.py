from fastapi import FastAPI, HTTPException, Request
from starlette.responses import JSONResponse

from app.routers import auth
from app.dependencies import lifespan
from app.errors.web_exception import WebException

app = FastAPI(lifespan=lifespan)

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(WebException)
def http_exception_handler(request: Request, exc: WebException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "code": exc.error_code},
    )

app.include_router(auth.router, prefix="/auth")
