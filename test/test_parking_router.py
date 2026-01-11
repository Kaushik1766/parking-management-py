import time
import jwt
import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.roles import Roles
from app.services.parking import ParkingService


class TestParkingRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.parking_service_mock = AsyncMock(spec=ParkingService)
        app.dependency_overrides[ParkingService] = lambda: self.parking_service_mock

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

    def test_park_vehicle(self):
        self.parking_service_mock.park.return_value = "ticket_123"

        response = self.client.post(
            "/parkings/",
            json={"numberplate": "ABC123"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        assert response.json() == {"ticketId": "ticket_123"}

    def test_get_parkings(self):
        self.parking_service_mock.get_parkings.return_value = [
            {
                "TicketId": "ticket_123",
                "NumberPlate": "ABC123",
                "BuildingId": "b1",
                "BuildingName": "HQ",
                "FloorNumber": 1,
                "SlotNumber": 2,
                "StartTime": "2024-01-01T00:00:00Z",
                "EndTime": None,
                "VehicleType": "Car",
            }
        ]

        response = self.client.get(
            "/parkings/?start_time=1&end_time=10",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        assert response.json() == self.parking_service_mock.get_parkings.return_value

    def test_unpark_vehicle(self):
        response = self.client.patch(
            "/parkings/ABC123/unpark",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Vehicle unparked successfully"}
