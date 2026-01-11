import time
import jwt
import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

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
            "asdfasasdfasdf",
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_get_bill(self):
        self.billing_service_mock.get_bill.return_value = {"amount": 100, "month": 1, "year": 2024}

        response = self.client.get("/billing?month=1&year=2024", headers=self._auth_headers())

        assert response.status_code == 200
        assert response.json() == self.billing_service_mock.get_bill.return_value
