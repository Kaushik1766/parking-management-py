from dataclasses import dataclass, field

from app.models.roles import Roles
from app.utils.alias_deserializer import alias_init


@alias_init
@dataclass
class User:
    username: str = field(metadata={"alias": "Username"})
    password: str = field(metadata={"alias": "PasswordHash"})
    email: str = field(metadata={"alias": "Email"})
    office_id: str = field(metadata={"alias": "OfficeId"})
    user_id: str = field(metadata={"alias": "Id"})
    role: Roles = field(default=Roles.CUSTOMER, metadata={"alias": "Role"})
