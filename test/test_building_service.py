import asyncio
import unittest
from unittest.mock import AsyncMock

from app.dto.building import AddBuildingRequestDTO, AddFloorRequestDTO
from app.errors.web_exception import DB_ERROR, WebException
from app.models.building import Building
from app.models.floor import Floor
from app.models.office import Office
from app.models.slot import OccupantDetails, Slot, SlotType
from app.repository.building_repo import BuildingRepository
from app.repository.floor_repo import FloorRepository
from app.repository.office_repo import OfficeRepository
from app.repository.slot_repo import SlotRepository
from app.services.building import BuildingService


class TestBuildingService(unittest.TestCase):
    def setUp(self):
        self.building_repo = AsyncMock(BuildingRepository)
        self.floor_repo = AsyncMock(FloorRepository)
        self.office_repo = AsyncMock(OfficeRepository)
        self.slot_repo = AsyncMock(SlotRepository)
        self.service = BuildingService(
            building_repo=self.building_repo,
            floor_repo=self.floor_repo,
            office_repo=self.office_repo,
            slot_repo=self.slot_repo,
        )
        self.service.building_repo = self.building_repo
        self.service.floor_repo = self.floor_repo
        self.service.office_repo = self.office_repo
        self.service.slot_repo = self.slot_repo

    def test_get_slots_raises_when_floor_missing(self):
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=1, TotalSlots=10, AvailableSlots=10
        )
        self.floor_repo.get_floors.return_value = [Floor(building_id="b1", FloorNumber=1)]

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.get_slots("b1", 2))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)
        self.floor_repo.get_floors.assert_awaited_once_with("b1")
        self.slot_repo.get_slots_by_floor.assert_not_awaited()

    def test_get_slots_returns_parking_status(self):
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=1, TotalSlots=10, AvailableSlots=10
        )
        self.floor_repo.get_floors.return_value = [Floor(building_id="b1", FloorNumber=1)]
        occupant = OccupantDetails(Username="John", NumberPlate="ABC123", Email="john@example.com", StartTime=0)
        slot = Slot(
            building_id="b1",
            floor_number=1,
            SlotId=5,
            SlotType=SlotType.TWO_WHEELER,
            IsAssigned=True,
            IsOccupied=True,
            OccupiedBy=occupant,
        )
        self.slot_repo.get_slots_by_floor.return_value = [slot]

        slots = asyncio.run(self.service.get_slots("b1", 1))

        self.slot_repo.get_slots_by_floor.assert_awaited()
        self.assertEqual(len(slots), 1)
        slot_response = slots[0]
        self.assertEqual(slot_response.building_id, "b1")
        self.assertEqual(slot_response.floor_number, 1)
        self.assertEqual(slot_response.slot_number, 5)
        self.assertEqual(slot_response.slot_type, SlotType.TWO_WHEELER.value)
        self.assertTrue(slot_response.is_assigned)
        self.assertIsNotNone(slot_response.parking_status)
        self.assertEqual(slot_response.parking_status.number_plate, "ABC123")
        self.assertEqual(slot_response.parking_status.user_email, "john@example.com")
        self.assertEqual(slot_response.parking_status.parked_at, "1970-01-01T00:00:00Z")

    def test_get_floors_returns_office_name_when_assigned(self):
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=2, TotalSlots=10, AvailableSlots=5
        )
        self.floor_repo.get_floors.return_value = [Floor(building_id="b1", FloorNumber=2, OfficeId="office_1")]
        self.office_repo.get_office_by_id.return_value = Office(
            OfficeName="Marketing", BuildingId="b1", FloorNumber=2, OfficeId="office_1"
        )

        floors = asyncio.run(self.service.get_floors("b1"))

        self.floor_repo.get_floors.assert_awaited_once_with("b1")
        self.office_repo.get_office_by_id.assert_awaited_once_with("office_1")
        self.assertEqual(len(floors), 1)
        self.assertEqual(floors[0].assigned_office, "Marketing")

    def test_add_floor_calls_repo_after_validation(self):
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=1, TotalSlots=10, AvailableSlots=10
        )

        asyncio.run(self.service.add_floor("b1", AddFloorRequestDTO(floor_number=3)))

        self.building_repo.get_building_by_id.assert_awaited_once_with("b1")
        self.floor_repo.add_floor.assert_awaited_once_with(building_id="b1", floor_number=3)

    def test_add_building_initializes_with_defaults(self):
        asyncio.run(self.service.add_building(AddBuildingRequestDTO(buildingName="HQ")))

        self.building_repo.add_building.assert_awaited_once()
        saved_building = self.building_repo.add_building.await_args.args[0]
        self.assertEqual(saved_building.name, "HQ")
        self.assertEqual(saved_building.total_floors, 0)
        self.assertEqual(saved_building.total_slots, 0)
        self.assertEqual(saved_building.available_slots, 0)
