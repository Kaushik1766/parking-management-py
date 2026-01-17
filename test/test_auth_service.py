from app.constants import JWT_ALGORITHM
from app.constants import JWT_SECRET
import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock

import bcrypt
import jwt

from app.dto.login import LoginDTO, UserJWT
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

    def testLogin(self):
        valid_user = User(
                    Username="kaushik",
                    Email="kaushik@a.com",
                    OfficeId="asd",
                    PasswordHash=bcrypt.hashpw("pass".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                    Id="adsfasdf"
                )
        cases = {
            "valid_credentials": {
                "input": LoginDTO(
                    email="kaushik@a.com", password="pass"
                ),
                "repo_setup": lambda: setattr(self.mock_user_repo.get_by_email, 'return_value', valid_user),
                "expected_exception": None,
            },
            "invalid_credentials": {
                "input": LoginDTO(
                    email="kaushik@a.com", password="wrongpass"
                ),
                "repo_setup": lambda: setattr(self.mock_user_repo.get_by_email, 'return_value', valid_user),
                "expected_exception": WebException,
            },
            "no_user_found": {
                "input": LoginDTO(
                    email="kaushik@a.com", password="wrongpass"
                ),
                "repo_setup": lambda: setattr(self.mock_user_repo.get_by_email, 'side_effect', WebException(status_code=409, message="User not found", error_code="DB_ERROR")),
                "expected_exception": WebException,
            }
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["repo_setup"]()
                
                if case['expected_exception']:
                    with self.assertRaises(case['expected_exception']) as ctx:
                        token = asyncio.run(self.auth_service.login(case["input"]))
                else:
                    token = asyncio.run(self.auth_service.login(case["input"]))
                    self.assertIsNotNone(token)
                    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                    jwt_user = UserJWT(**payload)
                    
                    self.assertEqual(jwt_user.email, valid_user.email)
                    self.assertEqual(jwt_user.id, valid_user.user_id)
                    self.assertEqual(jwt_user.officeId, valid_user.office_id)
                    expected_role = Roles.CUSTOMER if valid_user.role == Roles.CUSTOMER else Roles.ADMIN
                    self.assertEqual(jwt_user.role, expected_role)
                    self.assertIn("exp", payload)
                    self.assertIn("iat", payload)

    def testRegister(self):
        cases = {
            "valid_registration": {
                "input": RegisterDTO(
                    name="Kaushik", email="kaushik@a.com", password="pass", officeId="office_1"
                ),
                "repo_setup": lambda: setattr(self.mock_user_repo.save_user, 'return_value', None),
                "expected_exception": None,
            },
            "duplicate_email": {
                "input": RegisterDTO(
                    name="Kaushik", email="kaushik@a.com", password="pass", officeId="office_1"
                ),
                "repo_setup": lambda: setattr(self.mock_user_repo.save_user, 'side_effect', WebException(status_code=409, message="User already exists", error_code="DB_ERROR")),
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["repo_setup"]()
                
                if case['expected_exception']:
                    with self.assertRaises(case['expected_exception']) as ctx:
                        asyncio.run(self.auth_service.register(case["input"]))
                else:
                    asyncio.run(self.auth_service.register(case["input"]))
                    self.mock_user_repo.save_user.assert_awaited_once()
                    saved_user = self.mock_user_repo.save_user.await_args.args[0]
                    self.assertEqual(saved_user.email, case["input"].email.lower())
                    self.assertEqual(saved_user.username, case["input"].name)
                    self.assertEqual(saved_user.office_id, case["input"].officeId)
                    self.assertTrue(bcrypt.checkpw(case["input"].password.encode("utf-8"), saved_user.password.encode("utf-8")))
                    self.assertIsNotNone(saved_user.user_id)
