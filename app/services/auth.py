from typing import Annotated

from fastapi import Depends

from app.repository.user_repo import UserRepository
from app.dto.login import LoginDTO


class AuthService:
    def __init__(self, repo: Annotated[UserRepository, Depends(UserRepository)]):
        self.repo = repo

    def login(self, req: LoginDTO):
        print(req)
        print(self.repo)
