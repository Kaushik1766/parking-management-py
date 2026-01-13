import unittest
import boto3
from moto import mock_aws

from app.repository.vehicle_repo import VehicleRepository
from app.models.vehicle import Vehicle, VehicleType, AssignedSlot
from app.constants import TABLE


@mock_aws
class TestVehicleRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        self.table = self.dynamodb.create_table(
            TableName=TABLE,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        
        self.repo = VehicleRepository(db=self.dynamodb)
        
        self.user_id = "user001"
        
    def tearDown(self):
        self.table.delete()

    async def test_get_vehicles_by_user_id_empty(self):
        result = await self.repo.get_vehicles_by_user_id(self.user_id)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_vehicles_by_user_id_single(self):
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#ABC123",
            "VehicleId": "vehicle001",
            "Numberplate": "ABC123",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": False,
        })
        
        result = await self.repo.get_vehicles_by_user_id(self.user_id)
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Vehicle)
        self.assertEqual(result[0].vehicle_id, "vehicle001")
        self.assertEqual(result[0].number_plate, "ABC123")
        self.assertEqual(result[0].vehicle_type, VehicleType.TWO_WHEELER)
        self.assertFalse(result[0].is_parked)

    async def test_get_vehicles_by_user_id_multiple(self):
        vehicles = [
            {
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#CAR001",
                "VehicleId": "vehicle001",
                "Numberplate": "CAR001",
                "VehicleType": VehicleType.FOUR_WHEELER,
                "IsParked": False,
            },
            {
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#BIKE001",
                "VehicleId": "vehicle002",
                "Numberplate": "BIKE001",
                "VehicleType": VehicleType.TWO_WHEELER,
                "IsParked": True,
            },
            {
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#CAR002",
                "VehicleId": "vehicle003",
                "Numberplate": "CAR002",
                "VehicleType": VehicleType.FOUR_WHEELER,
                "IsParked": False,
            }
        ]
        
        for vehicle in vehicles:
            self.table.put_item(Item=vehicle)
        
        result = await self.repo.get_vehicles_by_user_id(self.user_id)
        
        self.assertEqual(len(result), 3)
        numberplates = [v.number_plate for v in result]
        self.assertIn("CAR001", numberplates)
        self.assertIn("BIKE001", numberplates)
        self.assertIn("CAR002", numberplates)

    async def test_get_vehicles_by_user_id_with_assigned_slot(self):
        assigned_slot = {
            "BuildingId": "bldg001",
            "FloorNumber": 2,
            "SlotId": 10,
        }
        
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#XYZ789",
            "VehicleId": "vehicle004",
            "Numberplate": "XYZ789",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": True,
            "AssignedSlot": assigned_slot,
        })
        
        result = await self.repo.get_vehicles_by_user_id(self.user_id)
        
        self.assertEqual(len(result), 1)
        vehicle = result[0]
        self.assertIsNotNone(vehicle.assigned_slot)
        self.assertEqual(vehicle.assigned_slot.building_id, "bldg001")
        self.assertEqual(vehicle.assigned_slot.floor_number, 2)
        self.assertEqual(vehicle.assigned_slot.slot_id, 10)

    async def test_get_vehicle_by_number_plate_success(self):
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#TEST123",
            "VehicleId": "vehicle005",
            "Numberplate": "TEST123",
            "VehicleType": VehicleType.FOUR_WHEELER,
            "IsParked": False,
        })
        
        result = await self.repo.get_vehicle_by_number_plate(self.user_id, "TEST123")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Vehicle)
        self.assertEqual(result.number_plate, "TEST123")
        self.assertEqual(result.vehicle_type, VehicleType.FOUR_WHEELER)

    async def test_get_vehicle_by_number_plate_not_found(self):
        result = await self.repo.get_vehicle_by_number_plate(self.user_id, "NONEXISTENT")
        
        self.assertIsNone(result)

    async def test_get_vehicle_by_number_plate_wrong_user(self):
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#PRIVATE",
            "VehicleId": "vehicle006",
            "Numberplate": "PRIVATE",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": False,
        })
        
        result = await self.repo.get_vehicle_by_number_plate("wrong_user", "PRIVATE")
        
        self.assertIsNone(result)

    async def test_save_vehicle_success(self):
        vehicle = Vehicle(
            VehicleId="vehicle007",
            Numberplate="NEW123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=None
        )
        
        await self.repo.save_vehicle(vehicle, self.user_id)
        
        response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#NEW123"
            }
        )
        self.assertIn("Item", response)
        item = response["Item"]
        self.assertEqual(item["VehicleId"], "vehicle007")
        self.assertEqual(item["Numberplate"], "NEW123")
        self.assertEqual(item["VehicleType"], VehicleType.TWO_WHEELER)

    async def test_save_vehicle_with_assigned_slot(self):
        assigned_slot = AssignedSlot(
            BuildingId="bldg002",
            FloorNumber=3,
            SlotId=15
        )
        
        vehicle = Vehicle(
            VehicleId="vehicle008",
            Numberplate="ASSIGNED",
            VehicleType=VehicleType.FOUR_WHEELER,
            IsParked=False,
            AssignedSlot=assigned_slot
        )
        
        await self.repo.save_vehicle(vehicle, self.user_id)
        
        response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#ASSIGNED"
            }
        )
        item = response["Item"]
        self.assertIn("AssignedSlot", item)
        self.assertEqual(item["AssignedSlot"]["BuildingId"], "bldg002")

    async def test_save_vehicle_duplicate_raises_error(self):
        vehicle = Vehicle(
            VehicleId="vehicle009",
            Numberplate="DUP123",
            VehicleType=VehicleType.TWO_WHEELER,
            IsParked=False,
            AssignedSlot=None
        )
        
        await self.repo.save_vehicle(vehicle, self.user_id)
        
        with self.assertRaises(Exception):
            await self.repo.save_vehicle(vehicle, self.user_id)

    async def test_delete_vehicle_success(self):
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#DELETE",
            "VehicleId": "vehicle010",
            "Numberplate": "DELETE",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": False,
        })
        
        await self.repo.delete_vehicle(self.user_id, "DELETE")
        
        response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": "VEHICLE#DELETE"
            }
        )
        self.assertNotIn("Item", response)

    async def test_delete_vehicle_not_found_raises_error(self):
        with self.assertRaises(Exception):
            await self.repo.delete_vehicle(self.user_id, "NONEXISTENT")

    async def test_delete_vehicle_wrong_user_raises_error(self):
        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "VEHICLE#OWNED",
            "VehicleId": "vehicle011",
            "Numberplate": "OWNED",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": False,
        })
        
        with self.assertRaises(Exception):
            await self.repo.delete_vehicle("wrong_user", "OWNED")

    async def test_vehicle_isolation_between_users(self):
        user1 = "user001"
        user2 = "user002"
        
        self.table.put_item(Item={
            "PK": f"USER#{user1}",
            "SK": "VEHICLE#SHARED",
            "VehicleId": "vehicle012",
            "Numberplate": "SHARED",
            "VehicleType": VehicleType.TWO_WHEELER,
            "IsParked": False,
        })
        
        self.table.put_item(Item={
            "PK": f"USER#{user2}",
            "SK": "VEHICLE#SHARED",
            "VehicleId": "vehicle013",
            "Numberplate": "SHARED",
            "VehicleType": VehicleType.FOUR_WHEELER,
            "IsParked": True,
        })
        
        vehicles_user1 = await self.repo.get_vehicles_by_user_id(user1)
        vehicles_user2 = await self.repo.get_vehicles_by_user_id(user2)
        
        self.assertEqual(len(vehicles_user1), 1)
        self.assertEqual(len(vehicles_user2), 1)
        self.assertEqual(vehicles_user1[0].vehicle_type, VehicleType.TWO_WHEELER)
        self.assertEqual(vehicles_user2[0].vehicle_type, VehicleType.FOUR_WHEELER)


if __name__ == "__main__":
    unittest.main()
