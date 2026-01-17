import time
import jwt
import unittest
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient

from app.constants import BILL_NOT_GENERATED_MESSAGE, JWT_SECRET
from app.errors.web_exception import DB_ERROR, WebException
from app.main import app
from app.models.roles import Roles
from app.services.billing import BillingService


class TestBillingRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.billing_service_mock = AsyncMock(spec=BillingService)
        app.dependency_overrides[BillingService] = lambda: self.billing_service_mock

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def _auth_headers(self):
        now = int(time.time())
        token = jwt.encode(
            {
                "email": "user@example.com",
                "id": "user_1",
                "role": Roles.CUSTOMER.value,
                "officeId": "office_1",
                "exp": now + 3600,
                "iat": now,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_get_bill(self):
        cases = {
            "bill_generated": {
                "month": 1,
                "year": 2024,
                "expected_status": 200,
                "service_setup": lambda: setattr(self.billing_service_mock.get_bill, "return_value", {
                    "amount": 100,
                    "month": 1,
                    "year": 2024,
                })
            },
            "bill_not_generated": {
                "month": 2,
                "year": 2024,
                "expected_status": 404,
                "service_setup": lambda: setattr(self.billing_service_mock.get_bill, "side_effect", WebException(status_code=404, message=BILL_NOT_GENERATED_MESSAGE, error_code=DB_ERROR))
            },
        }

        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case['service_setup']()
                response = self.client.get(f"/billing?month={case['month']}&year={case['year']}", headers=self._auth_headers())
                self.assertEqual(response.status_code, case['expected_status'])
                if case['expected_status'] == 200:
                    self.assertEqual(response.json(), self.billing_service_mock.get_bill.return_value)
                else:
                    self.assertEqual(BILL_NOT_GENERATED_MESSAGE, response.json().get("message", ""))
       # self.billing_service_mock.get_bill.return_value = {"amount": 100, "month": 1, "year": 2024}

        # response = self.client.get("/billing?month=1&year=2024", headers=self._auth_headers())

        # assert response.status_code == 200
        # assert response.json() == self.billing_service_mock.get_bill.return_value
