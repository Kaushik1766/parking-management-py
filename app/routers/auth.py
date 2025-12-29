from fastapi import APIRouter, Request

from app.dto.login import LoginDTO
from app.dto.register import RegisterDTO


router = APIRouter()


@router.post("/login")
async def login(request: LoginDTO):
    print(request)
    pass


@router.post("/register")
async def register(request: RegisterDTO):
    print(request)
    pass
