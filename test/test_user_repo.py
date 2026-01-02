import pytest
import boto3

# from ..app.repository.user_repo import UserRepository
from app.models.user import User
from app.repository.user_repo import UserRepository


@pytest.fixture
def user_repo():
    return UserRepository(db=boto3.resource("dynamodb"))


async def test_get_by_email(user_repo: UserRepository):
    user = await user_repo.get_by_email("kaushiksaha004@gmail.com")
    print(user)
    assert isinstance(user, User)
