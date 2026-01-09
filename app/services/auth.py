import uuid
import datetime
import jwt
import bcrypt
from typing import Annotated

from fastapi import Depends, HTTPException

from app.dto.register import RegisterDTO
from app.models.roles import Roles
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.dto.login import LoginDTO
from app.utils.singleton import singleton

@singleton
class AuthService:
    def __init__(self, repo: Annotated[UserRepository, Depends(UserRepository)]):
        self.repo = repo

    async def login(self, req: LoginDTO) -> str:
        user = await self.repo.get_by_email(req.email.lower())

        if not bcrypt.checkpw(
            req.password.encode("utf-8"), user.password.encode("utf-8")
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = jwt.encode(
            {
                "email": user.email,
                "id": user.user_id,
                "role": 0 if user.role == Roles.CUSTOMER else 1,
                "officeId": user.office_id,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
                "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            },
            "asdfasasdfasdf",
            algorithm="HS256",
        )
        return token

    async def register(self, req: RegisterDTO):
        hashed_password = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt())

        res = await self.repo.save_user(
            User(
                Username=req.name,
                PasswordHash=hashed_password.decode("utf-8"),
                Email=req.email.lower(),
                OfficeId=req.officeId,
                Id=str(uuid.uuid4()),
            )
        )
