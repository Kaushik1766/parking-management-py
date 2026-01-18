import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.dto.office import AddOfficeRequestDTO
from app.errors.web_exception import DB_ERROR, WebException
from app.models.building import Building
from app.models.floor import Floor
from app.models.office import Office
from app.repository.building_repo import BuildingRepository
from app.repository.floor_repo import FloorRepository
from app.repository.office_repo import OfficeRepository
from app.services.office import OfficeService


class TestOfficeService(unittest.TestCase):
    def setUp(self):
        self.office_repo = AsyncMock(OfficeRepository)
        self.building_repo = AsyncMock(BuildingRepository)
        self.floor_repo = AsyncMock(FloorRepository)
        self.service = OfficeService(
            office_repo=self.office_repo,
            building_repo=self.building_repo,
            floor_repo=self.floor_repo,
        )
        
    def test_get_offices(self):
        self.office_repo.get_offices.return_value = [
            Office(OfficeName="Engineering", BuildingId="b1", FloorNumber=2, OfficeId="office_1")
        ]

        offices = asyncio.run(self.service.get_offices())

        self.office_repo.get_offices.assert_awaited_once()
        self.assertEqual(len(offices), 1)
        office = offices[0]
        self.assertEqual(office.office_id, "office_1")
        self.assertEqual(office.office_name, "Engineering")
        self.assertEqual(office.building_id, "b1")
        self.assertEqual(office.floor_number, 2)
        
    
    def test_add_office(self):
        cases = {
            "valid_floor": {
                "building_id": "b1",
                "request": AddOfficeRequestDTO(office_name="Sales", floor_number=3),
                "building_repo_setup": lambda: setattr(self.building_repo.get_building_by_id, 'return_value', Building(
                    BuildingId="b1",
                    BuildingName="Main Office",
                )),
                "floor_repo_setup": lambda: setattr(self.floor_repo.get_floors, 'return_value', [Floor(building_id="b1", FloorNumber=3)]),
                "expected_exception": None,
            },
            "building_not_found": {
                "building_id": "b2",
                "request": AddOfficeRequestDTO(office_name="Sales", floor_number=3),
                "building_repo_setup": lambda: setattr(self.building_repo.get_building_by_id, 'side_effect', WebException(status_code=404, message="Building not found", error_code=DB_ERROR)),
                "floor_repo_setup": lambda: None,
                "expected_exception": WebException,
            },
            "floor_not_found": {
                "building_id": "b1",
                "request": AddOfficeRequestDTO(office_name="Sales", floor_number=4),
                "building_repo_setup": lambda: setattr(self.building_repo.get_building_by_id, 'return_value', Building(
                    BuildingId="b1",
                    BuildingName="Main Office",
                )),
                "floor_repo_setup": lambda: setattr(self.floor_repo.get_floors, 'return_value', [Floor(building_id="b1", FloorNumber=3)]),
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case_name=case_name):
                case["building_repo_setup"]()
                case["floor_repo_setup"]()
                
                if case["expected_exception"]:
                    with self.assertRaises(case["expected_exception"]):
                        asyncio.run(self.service.add_office(case["building_id"], case["request"]))
                else:
                    with patch("uuid.uuid4", return_value="generated-id"):
                        office_id = asyncio.run(
                            self.service.add_office(case["building_id"], case["request"])
                        )
                    
                    self.office_repo.add_office.assert_awaited_once()
                    saved_office = self.office_repo.add_office.await_args.args[0]
                    self.assertEqual(saved_office.office_id, "generated-id")
                    self.assertEqual(saved_office.building_id, case["building_id"])
                    self.assertEqual(saved_office.floor_number, case["request"].floor_number)
                    self.assertEqual(saved_office.office_name, case["request"].office_name)
                    self.assertEqual(office_id, "generated-id")
            

    def test_delete_office(self):
        cases = {
            "valid_office": {
                "building_id": "b1",
                "office_id": "office_1",
                "office_repo_setup": lambda: setattr(self.office_repo.get_office_by_id, 'return_value', Office(
                    OfficeName="Sales", BuildingId="b1", FloorNumber=1, OfficeId="office_1"
                )),
                "expected_exception": None,
            },
            "office_not_found_in_building": {
                "building_id": "b1",
                "office_id": "office_1",
                "office_repo_setup": lambda: setattr(self.office_repo.get_office_by_id, 'return_value', Office(
                    OfficeName="Sales", BuildingId="b2", FloorNumber=1, OfficeId="office_1"
                )),
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case_name=case_name):
                case["office_repo_setup"]()
                
                if case["expected_exception"]:
                    with self.assertRaises(case["expected_exception"]):
                        asyncio.run(self.service.delete_office(case["building_id"], case["office_id"]))
                else:
                    asyncio.run(self.service.delete_office(case["building_id"], case["office_id"]))
                    
                    self.office_repo.delete_office.assert_awaited_once_with(
                        building_id=case["building_id"], floor_number=1, office_id=case["office_id"]
                    )
                    