import asyncio
import unittest
from unittest.mock import AsyncMock

import bcrypt
import jwt

from app.dto.login import LoginDTO
from app.dto.register import RegisterDTO
from app.errors.web_exception import UNAUTHORIZED_ERROR, WebException
from app.models.roles import Roles
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.services.auth import AuthService


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = AsyncMock(UserRepository)
        self.auth_service = AuthService(repo=self.mock_user_repo)
        # singleton wrapper preserves first init; force mock wiring each time
        self.auth_service.repo = self.mock_user_repo

    def test_login_returns_token_for_valid_credentials(self):
        password = "secret123"
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            Username="Kaushik",
            PasswordHash=hashed_password,
            Email="kaushik@example.com",
            OfficeId="office_1",
            Role=Roles.CUSTOMER,
            Id="user_1",
        )
        self.mock_user_repo.get_by_email.return_value = user

        token = asyncio.run(self.auth_service.login(LoginDTO(email="KAUSHIK@example.com", password=password)))

        self.mock_user_repo.get_by_email.assert_awaited_once_with("kaushik@example.com")
        payload = jwt.decode(token, "asdfasasdfasdf", algorithms=["HS256"])
        self.assertEqual(payload["email"], user.email)
        self.assertEqual(payload["id"], user.user_id)
        self.assertEqual(payload["officeId"], user.office_id)
        self.assertEqual(payload["role"], 0)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_login_raises_for_invalid_credentials(self):
        user = User(
            Username="Kaushik",
            PasswordHash=bcrypt.hashpw("correct".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            Email="kaushik@example.com",
            OfficeId="office_1",
            Role=Roles.CUSTOMER,
            Id="user_1",
        )
        self.mock_user_repo.get_by_email.return_value = user

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.auth_service.login(LoginDTO(email="kaushik@example.com", password="wrong")))

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.error_code, UNAUTHORIZED_ERROR)
        self.assertEqual(ctx.exception.message, "Invalid credentials")

    def test_register_hashes_password_and_saves_user(self):
        request = RegisterDTO(name="Kaushik", email="USER@example.com", password="secret123", officeId="office_1")

        asyncio.run(self.auth_service.register(request))

        self.mock_user_repo.save_user.assert_awaited_once()
        saved_user = self.mock_user_repo.save_user.await_args.args[0]
        self.assertEqual(saved_user.email, "user@example.com")
        self.assertEqual(saved_user.username, "Kaushik")
        self.assertEqual(saved_user.office_id, "office_1")
        self.assertTrue(bcrypt.checkpw(request.password.encode("utf-8"), saved_user.password.encode("utf-8")))
        self.assertIsNotNone(saved_user.user_id)

