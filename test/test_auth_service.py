import bcrypt
import jwt
import unittest
from unittest.mock import AsyncMock

from app.dto.login import LoginDTO
from app.dto.register import RegisterDTO
from app.errors.web_exception import WebException
from app.models.roles import Roles
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.services.auth import AuthService


class TestAuthService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_user_repo = AsyncMock(spec=UserRepository)
        self.auth_service = AuthService(repo=self.mock_user_repo)
        self.auth_service.repo = self.mock_user_repo

    async def test_login_returns_token_for_valid_credentials(self):
        password = "123456"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            Email="kaushik@a.com",
            Username="Kaushik",
            PasswordHash=hashed,
            OfficeId="office_1",
            Role=Roles.CUSTOMER,
            Id="user_1",
        )
        self.mock_user_repo.get_by_email.return_value = user

        token = await self.auth_service.login(LoginDTO(email=user.email, password=password))

        payload = jwt.decode(token, "asdfasasdfasdf", algorithms=["HS256"])
        self.assertEqual(payload["email"], user.email)
        self.assertEqual(payload["id"], user.user_id)
        self.assertEqual(payload["role"], 0)
        self.assertEqual(payload["officeId"], user.office_id)

    async def test_login_raises_on_invalid_password(self):
        hashed = bcrypt.hashpw(b"correct", bcrypt.gensalt()).decode("utf-8")
        user = User(
            Email="kaushik@a.com",
            Username="Kaushik",
            PasswordHash=hashed,
            OfficeId="office_1",
            Role=Roles.CUSTOMER,
            Id="user_1",
        )
        self.mock_user_repo.get_by_email.return_value = user

        with self.assertRaises(WebException):
            await self.auth_service.login(LoginDTO(email=user.email, password="wrong"))

    async def test_register_hashes_password_and_calls_repo(self):
        req = RegisterDTO(email="New@Email.com", name="New User", officeId="office_1", password="pass123")

        await self.auth_service.register(req)

        self.mock_user_repo.save_user.assert_awaited_once()
        saved_user = self.mock_user_repo.save_user.await_args.args[0]
        self.assertEqual(saved_user.email, req.email.lower())
        self.assertEqual(saved_user.username, req.name)
        self.assertEqual(saved_user.office_id, req.officeId)
        self.assertNotEqual(saved_user.password, req.password)
        self.assertTrue(bcrypt.checkpw(req.password.encode("utf-8"), saved_user.password.encode("utf-8")))
