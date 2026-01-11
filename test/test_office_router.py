import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.office import OfficeService


class TestOfficeRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.office_service_mock = AsyncMock(spec=OfficeService)
        app.dependency_overrides[OfficeService] = lambda: self.office_service_mock

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def test_get_all_offices(self):
        self.office_service_mock.get_offices.return_value = [
            {"building_id": "b1", "floor_number": 1, "office_name": "Office A", "office_id": "o1"}
        ]

        response = self.client.get("/offices/")

        assert response.status_code == 200
        assert response.json() == self.office_service_mock.get_offices.return_value
