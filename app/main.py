from fastapi import FastAPI, HTTPException, Request
from fastapi import status
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse

from app.routers import auth_router, vehicle_router, building_router, office_router, parking_router, billing_router
from app.dependencies import lifespan
from app.errors.web_exception import VALIDATION_ERROR, WebException, UNEXPECTED_ERROR
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": UNEXPECTED_ERROR},
    )

# @app.exception_handler(Exception)
# def exception_handler(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"message": "Internal Server Error", "code": UNEXPECTED_ERROR},
#     )

@app.exception_handler(WebException)
def web_exception_handler(request: Request, exc: WebException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "code": exc.error_code},
    )

@app.exception_handler(ValidationException)
def validation_exception_handler(request: Request, exc: ValidationException):
    print(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": str(exc), "code": VALIDATION_ERROR},
    )

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(vehicle_router.router, prefix="/vehicles", tags=["vehicles"])
app.include_router(building_router.router, prefix="/buildings", tags=["buildings"])
app.include_router(office_router.router, prefix="/offices",tags=["offices"])
app.include_router(parking_router.router, prefix="/parkings", tags=["parkings"])
app.include_router(billing_router.router)