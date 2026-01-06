import pytest
import boto3

from app.constants import TABLE
from app.models.roles import Roles
# from ..app.repository.user_repo import UserRepository
from app.models.user import User
from app.repository.user_repo import UserRepository


@pytest.fixture
def user_repo():
    created_items = []
    db = db=boto3.resource("dynamodb")
    repo = UserRepository(db)
    repo._created_items = created_items
    yield repo

    for item in created_items:
        res = db.Table(TABLE).delete_item(Key=item)


@pytest.mark.parametrize(
    ("email", "expected"),
    [("kaushiksaha004@gmail.com", User), ("doesnotexist@gmail.com", Exception)],
)
async def test_get_by_email(user_repo: UserRepository, email: str, expected: type):
    if expected is Exception:
        with pytest.raises(Exception):
            user = await user_repo.get_by_email(email)
    else:
        user = await user_repo.get_by_email(email)
        assert isinstance(user, expected)

@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("kaushik@new.com", User),
        ("kaushik@c.com", Exception),
    ]
)
async def test_save_user(user_repo: UserRepository, email: str, expected: type):
    id = "afdsfasd"
    if expected is Exception:
        with pytest.raises(Exception):
            await user_repo.save_user(User(
                Email=email,
                OfficeId="58f7f1a9-8a88-4075-8f13-400d8d573d1d",
                Username="kaushik",
                PasswordHash="",
                Role=Roles.CUSTOMER,
                Id=id
            ))
    else:
        await user_repo.save_user(User(
            Email=email,
            OfficeId="58f7f1a9-8a88-4075-8f13-400d8d573d1d",
            Username="kaushik",
            PasswordHash="",
            Role=Roles.CUSTOMER,
            Id=id
        ))

        user = await user_repo.get_by_email(email)
        user_repo._created_items.append({"PK":f"USER#{id}","SK":"PROFILE"})
        user_repo._created_items.append({"PK":f"USER","SK":email})
        assert isinstance(user, expected), user.email == email
