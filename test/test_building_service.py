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
        
    def test_add_floor(self):
        cases = {
            "valid_add":{
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ",
                        TotalFloors=1,
                        AvailableSlots=10,
                    ),
                ),
                "floor_repo_setup": lambda: setattr(
                    self.floor_repo.add_floor,
                    "return_value",
                    None,
                ),
                "expected_exception": None,
            },
            "building_not_found":{
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "side_effect",
                    WebException(
                        status_code=404,
                        message="Building not found",
                        error_code=DB_ERROR,
                    ),
                ),
                "floor_repo_setup": lambda: None,
                "expected_exception": WebException,
            },
            "floor_exists": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ",
                        TotalFloors=1,
                        AvailableSlots=10,
                    ),
                ),
                "floor_repo_setup": lambda: setattr(
                    self.floor_repo.add_floor,
                    "side_effect",
                    WebException(
                        status_code=409,
                        message="Floor already exists",
                        error_code=DB_ERROR,
                    ),
                ),
                "expected_exception": WebException,
            }
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["building_repo_setup"]()
                case["floor_repo_setup"]()
                
                if case.get('expected_exception'):
                    with self.assertRaises(WebException) as ctx:
                        asyncio.run(self.service.add_floor("b1", AddFloorRequestDTO(floor_number=2)))
                else:
                    asyncio.run(self.service.add_floor("b1", AddFloorRequestDTO(floor_number=2)))
                    self.building_repo.get_building_by_id.assert_awaited_once_with("b1")
                    self.floor_repo.add_floor.assert_awaited_once_with(building_id="b1", floor_number=2)

    def test_get_buildings(self):
        self.building_repo.get_buildings.return_value = [
            Building(
                BuildingId="b1",
                BuildingName="HQ",
                TotalFloors=2,
                TotalSlots=10,
                AvailableSlots=5,
            )
        ]

        buildings = asyncio.run(self.service.get_buildings())

        self.building_repo.get_buildings.assert_awaited_once()
        self.assertEqual(len(buildings), 1)
        building_response = buildings[0]
        self.assertEqual(building_response.building_id, "b1")
        self.assertEqual(building_response.name, "HQ")
        self.assertEqual(building_response.available_slots, 5)
        self.assertEqual(building_response.total_slots, 10)
        self.assertEqual(building_response.total_floors, 2)

    def test_get_floors(self):
        cases = {
            "building_exists": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ",
                        TotalFloors=2,
                        AvailableSlots=5,
                    ),
                ),
                "floor_repo_setup": lambda: setattr(
                    self.floor_repo.get_floors,
                    "return_value",
                    [
                        Floor(building_id="b1", FloorNumber=1, TotalSlots=5, AvailableSlots=3, OfficeId=None)
                    ],
                ),
                "office_repo_setup": lambda: None,
                "expected_exception": None,
            },
            "building_not_found": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "side_effect",
                    WebException(
                        status_code=404,
                        message="Building not found",
                        error_code=DB_ERROR,
                    ),
                ),
                "floor_repo_setup": lambda: None,
                "office_repo_setup": lambda: None,
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["building_repo_setup"]()
                case["floor_repo_setup"]()
                case["office_repo_setup"]()
                
                if case.get('expected_exception'):
                    with self.assertRaises(WebException) as ctx:
                        asyncio.run(self.service.get_floors("b1"))
                else:
                    floors = asyncio.run(self.service.get_floors("b1"))
                    self.assertEqual(len(floors), 1)
                    floor_response = floors[0]
                    self.assertEqual(floor_response.building_id, "b1")
                    self.assertEqual(floor_response.floor_number, 1)
                    self.assertEqual(floor_response.total_slots, 5)
                    self.assertEqual(floor_response.available_slots, 3)
                    self.assertIsNone(floor_response.assigned_office)
    
    def test_get_slots(self):
        cases = {
            "building_and_floor_exists": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ",
                        TotalFloors=2,
                        AvailableSlots=5,
                    ),
                ),
                "floor_repo_setup": lambda: setattr(
                    self.floor_repo.get_floors,
                    "return_value",
                    [
                        Floor(building_id="b1", FloorNumber=1)
                    ],
                ),
                "slot_repo_setup": lambda: setattr(
                    self.slot_repo.get_slots_by_floor,
                    "return_value",
                    [
                        Slot(
                            building_id="b1",
                            floor_number=1,
                            SlotId=1,
                            SlotType=SlotType.FOUR_WHEELER,
                            IsAssigned=False,
                            IsOccupied=False,
                            OccupiedBy=None,
                        )
                    ],
                ),
                "expected_exception": None,
            },
            "building_not_found": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "side_effect",
                    WebException(
                        status_code=404,
                        message="Building not found",
                        error_code=DB_ERROR,
                    ),
                ),
                "floor_repo_setup": lambda: None,
                "slot_repo_setup": lambda: None,
                "expected_exception": WebException, 
            },
            "floor_not_found": {
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ",
                        TotalFloors=2,
                        AvailableSlots=5,
                    ),
                ),
                "floor_repo_setup": lambda: setattr(
                    self.floor_repo.get_floors,
                    "return_value",
                    [
                        Floor(building_id="b1", FloorNumber=2)
                    ],
                ),
                "slot_repo_setup": lambda: None,
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["building_repo_setup"]()
                case["floor_repo_setup"]()
                case["slot_repo_setup"]()
                
                if case.get('expected_exception'):
                    with self.assertRaises(WebException) as ctx:
                        asyncio.run(self.service.get_slots("b1", 1))
                else:
                    slots = asyncio.run(self.service.get_slots("b1", 1))
                    self.assertEqual(len(slots), 1)
                    slot_response = slots[0]
                    self.assertEqual(slot_response.building_id, "b1")
                    self.assertEqual(slot_response.floor_number, 1)
                    self.assertEqual(slot_response.slot_number, 1)
                    self.assertEqual(slot_response.slot_type, SlotType.FOUR_WHEELER.value)
                    self.assertFalse(slot_response.is_assigned)
                    self.assertIsNone(slot_response.parking_status)
    