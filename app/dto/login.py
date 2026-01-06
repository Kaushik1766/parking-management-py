from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.roles import Roles


class LoginDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=2, max_length=10)


class JwtDTO(BaseModel):
    jwt: str

class UserJWT(BaseModel):
    email: str
    id: str
    role: Roles
    officeId: str
    exp: int
    iat: int

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, int):
            return Roles.CUSTOMER if v == 0 else Roles.ADMIN
        else:
            return v
