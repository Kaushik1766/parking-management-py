import time
import jwt
import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.roles import Roles
from app.services.vehicle import VehicleService


class TestVehicleRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.vehicle_service_mock = AsyncMock(spec=VehicleService)
        app.dependency_overrides[VehicleService] = lambda: self.vehicle_service_mock

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

    def test_get_vehicles(self):
        self.vehicle_service_mock.get_vehicles_by_user.return_value = [
            {
                "number_plate": "ABC123",
                "vehicle_type": "Car",
                "is_parked": False,
                "assigned_building_name": "HQ",
                "assigned_building_id": "b1",
                "assigned_floor_number": 1,
                "assigned_slot_number": 2,
            }
        ]

        response = self.client.get("/vehicles/", headers=self._auth_headers())

        assert response.status_code == 200
        assert response.json() == self.vehicle_service_mock.get_vehicles_by_user.return_value

    def test_add_vehicle(self):
        response = self.client.post(
            "/vehicles/",
            json={"numberplate": "ABC123", "type": 0},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        assert response.json() == {"message": "Vehicle added successfully"}

    def test_delete_vehicle(self):
        response = self.client.delete(
            "/vehicles/ABC123",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Vehicle deleted successfully"}
