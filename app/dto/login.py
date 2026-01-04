from pydantic import BaseModel, EmailStr, Field


class LoginDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=2, max_length=10)


class JwtDTO(BaseModel):
    jwt: str
