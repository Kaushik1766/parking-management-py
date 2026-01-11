import unittest
from unittest.mock import AsyncMock, Mock, create_autospec
from fastapi.testclient import TestClient
from app.errors.web_exception import UNAUTHORIZED_ERROR, WebException
from app.main import app
from app.services.auth import AuthService

class TestAuthRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        
        auth_service_mock = AsyncMock(spec=AuthService)
        app.dependency_overrides[AuthService] = lambda: auth_service_mock

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def test_login(self):
        cases = {
            "valid_credentials": {
                "input": {"email": "kaushik@example.com", "password": "123456"},
                "mock_return": "mocked_jwt_token",
                "expected_status": 200,
                "expected_response": {"jwt": "mocked_jwt_token"},
            },
            "invalid_credentials": {
                "input": {"email": "wronguser@example.com", "password": "wrongpass"},
                "mock_return": None,
                "expected_status": 401,
                "expected_response": {"message": "Invalid credentials", "code": 1004},
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case_name=case_name):
                auth_service_mock = app.dependency_overrides[AuthService]()
                if case["mock_return"]:
                    auth_service_mock.login.return_value = case["mock_return"]
                else:
                    auth_service_mock.login.side_effect = WebException(status_code=401, message="Invalid credentials", error_code=UNAUTHORIZED_ERROR)
                
                response = self.client.post("/auth/login", json=case["input"])
                
                assert response.status_code == case["expected_status"]
                assert response.json() == case["expected_response"]

    def test_register(self):
        cases = {
            "valid_registration": {
                "input": {"name": "Kaushik", "email": "kaushik@a.com", "password": "123456", "officeId": "office_1"},
                "signup_error": False,
                "expected_status": 201,
            },
            "invalid_registration": {
                "input": {"name": "", "email": "invalidemail", "password": "123", "officeId": ""},
                "signup_error": True,
                "expected_status": 422,
            },
        }       
        
        for case_name, case in cases.items():
            with self.subTest(case_name=case_name):
                response = self.client.post("/auth/register", json=case["input"])
                if case["signup_error"]:
                    auth_service_mock = app.dependency_overrides[AuthService]()
                    auth_service_mock.register.side_effect = WebException(status_code=422, message="Validation error", error_code=1002)

                assert response.status_code == case["expected_status"]