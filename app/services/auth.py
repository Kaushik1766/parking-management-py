from app.utils.secrets_utils import get_jwt_secret
import json
from botocore.exceptions import ClientError
from app.constants import SECRET_NAME
from app.constants import REGION_NAME
import boto3
from app.constants import JWT_ALGORITHM
import uuid
import datetime
import jwt
import bcrypt
from typing import Annotated

from fastapi import Depends

from app.dto.register import RegisterDTO
from app.errors.web_exception import UNAUTHORIZED_ERROR, WebException
from app.models.roles import Roles
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.repository.office_repo import OfficeRepository
from app.dto.login import LoginDTO
from app.utils.singleton import singleton

class AuthService:
    def __init__(
        self,
        repo: Annotated[UserRepository, Depends(UserRepository)],
        office_repo: Annotated[OfficeRepository, Depends(OfficeRepository)],
    ):
        self.repo = repo
        self.office_repo = office_repo

    async def login(self, req: LoginDTO) -> str:
        user = await self.repo.get_by_email(req.email.lower())

        if not bcrypt.checkpw(
            req.password.encode("utf-8"), user.password.encode("utf-8")
        ):
            raise WebException(status_code=401, message="Invalid credentials", error_code=UNAUTHORIZED_ERROR)

        token = jwt.encode(
            {
                "email": user.email,
                "id": user.user_id,
                "role": 0 if user.role == Roles.CUSTOMER else 1,
                "officeId": user.office_id,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
                "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            },
            get_jwt_secret(),
            algorithm=JWT_ALGORITHM,
        )
        return token

    async def register(self, req: RegisterDTO):
        await self.office_repo.get_office_by_id(req.officeId)

        hashed_password = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt())

        await self.repo.save_user(
            User(
                Username=req.name,
                PasswordHash=hashed_password.decode("utf-8"),
                Email=req.email.lower(),
                OfficeId=req.officeId,
                Id=str(uuid.uuid4()),
            )
        )
