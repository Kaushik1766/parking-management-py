from fastapi import APIRouter, Depends

from app.dto.login import LoginDTO
from app.dto.register import RegisterDTO
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login")
async def login(request: LoginDTO, auth_service: AuthService = Depends(AuthService)):
    auth_service.login(request)
    return {
        "msg": "Login successful",
    }


@router.post("/register")
async def register(request: RegisterDTO):
    print(request)
    pass
