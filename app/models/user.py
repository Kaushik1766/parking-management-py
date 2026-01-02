from dataclasses import dataclass, fields

from dataclasses import field

# from app.models.roles import Roles


@dataclass
class User:
    # username: str
    # password: str
    # email: str
    # role: Roles
    # office_id: str
    user_id: str = field(metadata={"dynamodb_name": "UUID"})


# dc = {"UUID": "adfa"}

u = User(user_id="adfa")
print(fields(u)[0])
# print(u)
