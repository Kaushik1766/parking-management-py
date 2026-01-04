from pydantic import BaseModel, EmailStr, Field


class RegisterDTO(BaseModel):
    email: EmailStr
    name: str = Field(min_length=3, max_length=10)
    officeId: str
    password: str = Field(min_length=3, max_length=10)


class RegisterResponseDTO(BaseModel):
    message: str
