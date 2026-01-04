from fastapi import APIRouter, Depends, Response, status

from app.dto.login import JwtDTO, LoginDTO
from app.dto.register import RegisterDTO
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login")
async def login(request: LoginDTO, auth_service: AuthService = Depends(AuthService)):
    token = await auth_service.login(request)
    return JwtDTO(jwt=token)


@router.post("/register")
async def register(request: RegisterDTO, auth: AuthService = Depends(AuthService)):
    await auth.register(request)
    return Response(status_code=status.HTTP_201_CREATED)
