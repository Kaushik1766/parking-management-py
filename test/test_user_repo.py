import pytest
import boto3

# from ..app.repository.user_repo import UserRepository
from app.models.user import User
from app.repository.user_repo import UserRepository


@pytest.fixture
def user_repo():
    return UserRepository(db=boto3.resource("dynamodb"))


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
