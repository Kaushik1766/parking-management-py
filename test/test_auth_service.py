import jwt
import bcrypt
from unittest.mock import AsyncMock
from app.repository.user_repo import UserRepository
from app.services.auth import AuthService
from app.models.user import User
import unittest
class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = AsyncMock(UserRepository)
        self.auth_service = AuthService(repo=self.mock_user_repo)

    def test_login(self):
        cases = {
            "valid_credentials": {
                "req": {"email": "kaushik@a.com", "password": "123456"},
                "mock_return": ,
                "expect_exception": False,
                "expected_result": jwt.encode(
                    {
                        "email": "
                )
            },
            "valid_credentials": {
                "req": {"email": "kaushik@a.com", "password": "123456"},
                "mock_return": User(
                    Email="kaushik@a.com",
                    Username="Kaushik",
                    PasswordHash=bcrypt.hashpw("123456".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                    OfficeId="office_1",
                    Role=Roles.CUSTOMER,
                    Id="user_1",
                ),
                "expect_exception": False,
            },
        }

