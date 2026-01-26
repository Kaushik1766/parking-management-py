import unittest

from app.models.building import Building
from app.models.floor import Floor
from app.models.office import Office
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleType, AssignedSlot
from app.models.bill import Bill, BillingParkingHistory
from app.models.slot import Slot, SlotType, OccupantDetails


class TestModels(unittest.TestCase):
    def test_building_creation(self):
        """Test Building model creation"""
        building = Building(
            BuildingId="b1",
            BuildingName="HQ",
            TotalFloors=5,
            AvailableSlots=100,
            TotalSlots=100,
        )
        self.assertEqual(building.id, "b1")
        self.assertEqual(building.name, "HQ")
        self.assertEqual(building.total_floors, 5)
        self.assertEqual(building.available_slots, 100)

    def test_floor_creation(self):
        """Test Floor model creation"""
        floor = Floor(
            building_id="b1",
            FloorNumber=1,
            TotalSlots=20,
            AvailableSlots=15,
            OfficeId="o1",
        )
        self.assertEqual(floor.building_id, "b1")
        self.assertEqual(floor.floor_number, 1)
        self.assertEqual(floor.total_slots, 20)
        self.assertEqual(floor.available_slots, 15)
        self.assertEqual(floor.office_id, "o1")

    def test_office_creation(self):
        """Test Office model creation"""
        office = Office(
            OfficeName="Engineering",
            BuildingId="b1",
            FloorNumber=2,
            OfficeId="o1",
        )
        self.assertEqual(office.office_name, "Engineering")
        self.assertEqual(office.building_id, "b1")
        self.assertEqual(office.floor_number, 2)
        self.assertEqual(office.office_id, "o1")

    def test_user_creation(self):
        """Test User model creation"""
        from app.models.roles import Roles
        user = User(
            Id="u1",
            Email="user@test.com",
            PasswordHash="password123",
            Username="Test User",
            Role=Roles.CUSTOMER,
            OfficeId="o1",
        )
        self.assertEqual(user.user_id, "u1")
        self.assertEqual(user.email, "user@test.com")
        self.assertEqual(user.password, "password123")
        self.assertEqual(user.username, "Test User")

    def test_vehicle_creation(self):
        """Test Vehicle model creation"""
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.FOUR_WHEELER,
            IsParked=False,
            AssignedSlot=None,
        )
        self.assertEqual(vehicle.vehicle_id, "v1")
        self.assertEqual(vehicle.number_plate, "ABC123")
        self.assertEqual(vehicle.vehicle_type, VehicleType.FOUR_WHEELER)
        self.assertFalse(vehicle.is_parked)
        self.assertIsNone(vehicle.assigned_slot)

    def test_vehicle_with_assigned_slot(self):
        """Test Vehicle with AssignedSlot"""
        assigned_slot = AssignedSlot(
            BuildingId="b1",
            FloorNumber=1,
            SlotId=5,
        )
        vehicle = Vehicle(
            VehicleId="v1",
            Numberplate="ABC123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=True,
            AssignedSlot=assigned_slot,
        )
        self.assertIsNotNone(vehicle.assigned_slot)
        self.assertEqual(vehicle.assigned_slot.building_id, "b1")
        self.assertEqual(vehicle.assigned_slot.floor_number, 1)
        self.assertEqual(vehicle.assigned_slot.slot_id, 5)

    def test_bill_creation(self):
        """Test Bill model creation"""
        bill = Bill(
            user_id="u1",
            BillingMonth=1,
            BillingYear=2024,
            TotalAmount=100.50,
            BillDate="2024-02-01",
            ParkingHistory=[]
        )
        self.assertEqual(bill.user_id, "u1")
        self.assertEqual(bill.billing_month, 1)
        self.assertEqual(bill.billing_year, 2024)
        self.assertEqual(bill.total_amount, 100.50)

    def test_slot_creation(self):
        """Test Slot model creation"""
        slot = Slot(
            building_id="b1",
            floor_number=1,
            SlotId=5,
            SlotType=SlotType.FOUR_WHEELER,
            IsAssigned=True,
            IsOccupied=False,
            OccupiedBy=None
        )
        self.assertEqual(slot.building_id, "b1")
        self.assertEqual(slot.slot_id, 5)
        self.assertEqual(slot.slot_type, SlotType.FOUR_WHEELER)
        self.assertTrue(slot.is_assigned)
        self.assertFalse(slot.is_occupied)


if __name__ == "__main__":
    unittest.main()
