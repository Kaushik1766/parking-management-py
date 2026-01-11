import time
import jwt
import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.roles import Roles
from app.services.building import BuildingService
from app.services.office import OfficeService


class TestBuildingRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.building_service_mock = AsyncMock(spec=BuildingService)
        self.office_service_mock = AsyncMock(spec=OfficeService)
        app.dependency_overrides[BuildingService] = lambda: self.building_service_mock
        app.dependency_overrides[OfficeService] = lambda: self.office_service_mock

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def _auth_headers(self):
        now = int(time.time())
        token = jwt.encode(
            {
                "email": "admin@example.com",
                "id": "admin_1",
                "role": Roles.ADMIN.value,
                "officeId": "office_1",
                "exp": now + 3600,
                "iat": now,
            },
            "asdfasasdfasdf",
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_add_building(self):
        response = self.client.post(
            "/buildings/",
            json={"buildingName": "HQ"},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        assert response.json() == {"message": "Building added successfully"}

    def test_get_buildings(self):
        self.building_service_mock.get_buildings.return_value = [
            {"buildingId": "b1", "name": "HQ", "availableSlots": 5, "totalSlots": 10, "totalFloors": 2}
        ]

        response = self.client.get("/buildings/", headers=self._auth_headers())

        assert response.status_code == 200
        assert response.json() == self.building_service_mock.get_buildings.return_value

    def test_add_floor(self):
        response = self.client.post(
            "/buildings/b1/floors",
            json={"floor_number": 2},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        assert response.json() == {"message": "Floor added successfully"}

    def test_get_floors(self):
        self.building_service_mock.get_floors.return_value = [
            {"buildingId": "b1", "floorNumber": 1, "totalSlots": 5, "availableSlots": 3, "assignedOffice": None}
        ]

        response = self.client.get("/buildings/b1/floors", headers=self._auth_headers())

        assert response.status_code == 200
        assert response.json() == self.building_service_mock.get_floors.return_value

    def test_get_slots(self):
        self.building_service_mock.get_slots.return_value = [
            {
                "buildingId": "b1",
                "floorNumber": 1,
                "slotNumber": 1,
                "slotType": "Car",
                "isAssigned": False,
                "parkingStatus": None,
            }
        ]

        response = self.client.get("/buildings/b1/floors/1/slots", headers=self._auth_headers())

        assert response.status_code == 200
        assert response.json() == self.building_service_mock.get_slots.return_value

    def test_add_office(self):
        self.office_service_mock.add_office.return_value = "office_123"

        response = self.client.post(
            "/buildings/b1/offices",
            json={"office_name": "Office A", "floor_number": 1},
            headers=self._auth_headers(),
        )

        assert response.status_code == 201
        assert response.json() == {"officeId": "office_123"}

    def test_delete_office(self):
        response = self.client.delete(
            "/buildings/b1/offices/office_123",
            headers=self._auth_headers(),
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Office deleted successfully"}
