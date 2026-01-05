from dataclasses import dataclass, field, asdict

from pydantic import BaseModel, Field

from app.models.roles import Roles
from app.utils.alias_deserializer import alias_init

# @alias_init
# @dataclass
class User(BaseModel):
    username: str = Field(alias="Username")
    password: str = Field(alias="PasswordHash")
    email: str = Field(alias="Email")
    office_id: str = Field(alias="OfficeId")
    user_id: str = Field(alias="Id")
    role: Roles = Field(default=Roles.CUSTOMER, alias="Role")
