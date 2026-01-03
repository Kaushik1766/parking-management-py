import bcrypt
from typing import Annotated

from fastapi import Depends

from app.repository.user_repo import UserRepository
from app.dto.login import LoginDTO


class AuthService:
    def __init__(self, repo: Annotated[UserRepository, Depends(UserRepository)]):
        self.repo = repo

    async def login(self, req: LoginDTO):
        user = await self.repo.get_by_email(req.email)
