import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.dto.vehicle import AddVehicleRequestDTO
from app.errors.web_exception import CONFLICT_ERROR, DB_ERROR, WebException
from app.models.building import Building
from app.models.office import Office
from app.models.slot import Slot, SlotType
from app.models.vehicle import AssignedSlot, Vehicle, VehicleType
from app.repository.building_repo import BuildingRepository
from app.repository.office_repo import OfficeRepository
from app.repository.slot_repo import SlotRepository
from app.repository.vehicle_repo import VehicleRepository
from app.services.vehicle import VehicleService


class TestVehicleService(unittest.TestCase):
    def setUp(self):
        self.vehicle_repo = AsyncMock(VehicleRepository)
        self.building_repo = AsyncMock(BuildingRepository)
        self.office_repo = AsyncMock(OfficeRepository)
        self.slot_repo = AsyncMock(SlotRepository)
        self.service = VehicleService(
            vehicle_repo=self.vehicle_repo,
            building_repo=self.building_repo,
            office_repo=self.office_repo,
            slot_repo=self.slot_repo,
        )
        self.service.vehicle_repo = self.vehicle_repo
        self.service.building_repo = self.building_repo
        self.service.office_repo = self.office_repo
        self.service.slot_repo = self.slot_repo

    def test_get_vehicles_by_user_unassigned(self):
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=None,
        )
        self.vehicle_repo.get_vehicles_by_user_id.return_value = [vehicle]

        vehicles = asyncio.run(self.service.get_vehicles_by_user("user_1"))

        self.vehicle_repo.get_vehicles_by_user_id.assert_awaited_once_with("user_1")
        self.assertEqual(len(vehicles), 1)
        v = vehicles[0]
        self.assertEqual(v.assigned_building_id, "unassigned")
        self.assertEqual(v.assigned_building_name, "unassigned")
        self.assertEqual(v.assigned_slot_number, 0)
        self.assertEqual(v.assigned_floor_number, 0)

    def test_get_vehicles_by_user_with_assigned_slot(self):
        assigned_slot = AssignedSlot(BuildingId="b1", FloorNumber=2, SlotId=5)
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=assigned_slot,
        )
        self.vehicle_repo.get_vehicles_by_user_id.return_value = [vehicle]
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=1, TotalSlots=10, AvailableSlots=8
        )

        vehicles = asyncio.run(self.service.get_vehicles_by_user("user_1"))

        self.building_repo.get_building_by_id.assert_awaited_once_with("b1")
        v = vehicles[0]
        self.assertEqual(v.assigned_building_name, "HQ")
        self.assertEqual(v.assigned_slot_number, 5)
        self.assertEqual(v.assigned_floor_number, 2)

    def test_add_vehicle_assigns_slot_when_first_of_type(self):
        self.vehicle_repo.get_vehicles_by_user_id.return_value = []
        self.office_repo.get_office_by_id.return_value = Office(
            OfficeName="Ops", BuildingId="b1", FloorNumber=1, OfficeId="office_1"
        )
        free_slot = Slot(
            building_id="b1",
            floor_number=1,
            SlotId=7,
            SlotType=SlotType.TWO_WHEELER,
            IsAssigned=False,
            IsOccupied=False,
            OccupiedBy=None,
        )
        self.slot_repo.get_free_slots_by_floor.return_value = [free_slot]

        asyncio.run(
            self.service.add_vehicle(AddVehicleRequestDTO(numberplate="ABC123", type=0), user_id="user_1", office_id="office_1")
        )

        self.slot_repo.update_slot.assert_awaited_once()
        updated_slot = self.slot_repo.update_slot.await_args.args[0]
        self.assertTrue(updated_slot.is_assigned)
        self.vehicle_repo.save_vehicle.assert_awaited_once()
        saved_vehicle = self.vehicle_repo.save_vehicle.await_args.args[0]
        self.assertEqual(saved_vehicle.assigned_slot.building_id, "b1")
        self.assertEqual(saved_vehicle.assigned_slot.floor_number, 1)
        self.assertEqual(saved_vehicle.assigned_slot.slot_id, 7)

    def test_add_vehicle_raises_when_no_free_slots(self):
        self.vehicle_repo.get_vehicles_by_user_id.return_value = []
        self.office_repo.get_office_by_id.return_value = Office(
            OfficeName="Ops", BuildingId="b1", FloorNumber=1, OfficeId="office_1"
        )
        self.slot_repo.get_free_slots_by_floor.return_value = []

        with self.assertRaises(WebException) as ctx:
            asyncio.run(
                self.service.add_vehicle(
                    AddVehicleRequestDTO(numberplate="ABC123", type=0), user_id="user_1", office_id="office_1"
                )
            )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.error_code, CONFLICT_ERROR)
        self.vehicle_repo.save_vehicle.assert_not_awaited()

    def test_add_vehicle_reuses_existing_assignment(self):
        existing_slot = AssignedSlot(BuildingId="b1", FloorNumber=1, SlotId=3)
        registered_vehicle = SimpleNamespace(vehicle_type=0, assigned_slot=existing_slot)
        self.vehicle_repo.get_vehicles_by_user_id.return_value = [registered_vehicle]

        asyncio.run(
            self.service.add_vehicle(
                AddVehicleRequestDTO(numberplate="XYZ999", type=0), user_id="user_1", office_id="office_1"
            )
        )

        self.slot_repo.update_slot.assert_not_awaited()
        saved_vehicle = self.vehicle_repo.save_vehicle.await_args.args[0]
        self.assertEqual(saved_vehicle.assigned_slot.slot_id, 3)

    def test_delete_vehicle_raises_when_missing(self):
        self.vehicle_repo.get_vehicle_by_number_plate.return_value = None

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.delete_vehicle("ABC123", "user_1"))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)

    def test_delete_vehicle_calls_repo_when_found(self):
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=None,
        )
        self.vehicle_repo.get_vehicle_by_number_plate.return_value = vehicle

        asyncio.run(self.service.delete_vehicle("ABC123", "user_1"))

        self.vehicle_repo.delete_vehicle.assert_awaited_once_with("user_1", "ABC123")
