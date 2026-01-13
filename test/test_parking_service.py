import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.dto.parking import ParkRequestDTO
from app.errors.web_exception import CONFLICT_ERROR, DB_ERROR, WebException
from app.models.building import Building
from app.models.parking_history import ParkingHistory
from app.models.vehicle import AssignedSlot, Vehicle, VehicleType
from app.repository.building_repo import BuildingRepository
from app.repository.parking_repo import ParkingRepository
from app.repository.slot_repo import SlotRepository
from app.repository.vehicle_repo import VehicleRepository
from app.services.parking import ParkingService


class TestParkingService(unittest.TestCase):
    def setUp(self):
        self.parking_repo = AsyncMock(ParkingRepository)
        self.vehicle_repo = AsyncMock(VehicleRepository)
        self.building_repo = AsyncMock(BuildingRepository)
        self.slot_repo = AsyncMock(SlotRepository)
        self.service = ParkingService(
            parking_repo=self.parking_repo,
            vehicle_repo=self.vehicle_repo,
            building_repo=self.building_repo,
            slot_repo=self.slot_repo,
        )
        self.service.parking_repo = self.parking_repo
        self.service.vehicle_repo = self.vehicle_repo
        self.service.building_repo = self.building_repo
        self.service.slot_repo = self.slot_repo

    def test_park_creates_parking_record(self):
        assigned_slot = AssignedSlot(BuildingId="b1", FloorNumber=2, SlotId=5)
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=assigned_slot,
        )
        self.vehicle_repo.get_vehicle_by_number_plate.return_value = vehicle

        with patch("uuid.uuid4", return_value="parking-1"):
            parking_id = asyncio.run(
                self.service.park("user_1", "user@example.com", ParkRequestDTO(numberplate="ABC123"))
            )

        self.assertEqual(parking_id, "parking-1")
        self.parking_repo.add_parking.assert_awaited_once()
        saved_parking = self.parking_repo.add_parking.await_args.args[0]
        self.assertEqual(saved_parking.parking_id, "parking-1")
        self.assertEqual(saved_parking.building_id, "b1")
        self.assertEqual(saved_parking.floor_number, 2)
        self.assertEqual(saved_parking.slot_id, 5)
        self.assertEqual(saved_parking.numberplate, "ABC123")

    def test_park_raises_when_vehicle_missing(self):
        self.vehicle_repo.get_vehicle_by_number_plate.return_value = None

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.park("user_1", "user@example.com", ParkRequestDTO(numberplate="ABC123")))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)

    def test_park_raises_when_slot_not_assigned(self):
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=None,
        )
        self.vehicle_repo.get_vehicle_by_number_plate.return_value = vehicle

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.park("user_1", "user@example.com", ParkRequestDTO(numberplate="ABC123")))

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.error_code, CONFLICT_ERROR)

    def test_get_parkings_sorts_and_maps(self):
        records = [
            ParkingHistory(
                user_id="user_1",
                ParkingId="p1",
                Numberplate="ABC123",
                BuildingId="b1",
                FloorNumber=1,
                SlotId=2,
                StartTime=5,
                EndTime=None,
                VehicleType="Car",
            ),
            ParkingHistory(
                user_id="user_1",
                ParkingId="p2",
                Numberplate="XYZ999",
                BuildingId="b1",
                FloorNumber=1,
                SlotId=3,
                StartTime=10,
                EndTime=20,
                VehicleType="Car",
            ),
        ]
        self.parking_repo.get_parking_history.return_value = records
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=1, TotalSlots=10, AvailableSlots=8
        )

        responses = asyncio.run(self.service.get_parkings("user_1", start_time=None, end_time=None))

        self.parking_repo.get_parking_history.assert_awaited()
        self.assertEqual([r.ticket_id for r in responses], ["p2", "p1"])
        self.assertEqual(responses[0].building_name, "HQ")
        self.assertEqual(responses[0].start_time, "1970-01-01T00:00:10Z")
        self.assertEqual(responses[0].end_time, "1970-01-01T00:00:20Z")

    def test_unpark_calls_repo(self):
        asyncio.run(self.service.unpark("user_1", "ABC123"))

        self.parking_repo.unpark_by_numberplate.assert_awaited_once_with("user_1", "ABC123")
