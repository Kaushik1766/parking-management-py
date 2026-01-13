import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.dto.office import AddOfficeRequestDTO
from app.errors.web_exception import DB_ERROR, WebException
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
        self.service.office_repo = self.office_repo
        self.service.building_repo = self.building_repo
        self.service.floor_repo = self.floor_repo

    def test_get_offices_returns_mapped_models(self):
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

    def test_add_office_raises_when_floor_missing(self):
        self.building_repo.get_building_by_id.return_value = object()
        self.floor_repo.get_floors.return_value = []

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.add_office("b1", AddOfficeRequestDTO(office_name="Sales", floor_number=3)))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)
        self.office_repo.add_office.assert_not_awaited()

    def test_add_office_persists_and_returns_id(self):
        self.building_repo.get_building_by_id.return_value = object()
        self.floor_repo.get_floors.return_value = [Floor(building_id="b1", FloorNumber=3)]

        with patch("uuid.uuid4", return_value="generated-id"):
            office_id = asyncio.run(
                self.service.add_office("b1", AddOfficeRequestDTO(office_name="Sales", floor_number=3))
            )

        self.office_repo.add_office.assert_awaited_once()
        saved_office = self.office_repo.add_office.await_args.args[0]
        self.assertEqual(saved_office.office_id, "generated-id")
        self.assertEqual(saved_office.building_id, "b1")
        self.assertEqual(saved_office.floor_number, 3)
        self.assertEqual(saved_office.office_name, "Sales")
        self.assertEqual(office_id, "generated-id")

    def test_delete_office_validates_building(self):
        self.office_repo.get_office_by_id.return_value = Office(
            OfficeName="Sales", BuildingId="b2", FloorNumber=1, OfficeId="office_1"
        )

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.delete_office("b1", "office_1"))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)
        self.office_repo.delete_office.assert_not_awaited()

    def test_delete_office_calls_repo_when_valid(self):
        self.office_repo.get_office_by_id.return_value = Office(
            OfficeName="Sales", BuildingId="b1", FloorNumber=1, OfficeId="office_1"
        )

        asyncio.run(self.service.delete_office("b1", "office_1"))

        self.office_repo.delete_office.assert_awaited_once_with(
            building_id="b1", floor_number=1, office_id="office_1"
        )
