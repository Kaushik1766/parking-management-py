import unittest
import boto3
import time
from moto import mock_aws

from app.repository.parking_repo import ParkingRepository
from app.models.parking_history import ParkingHistory
from app.models.user import User
from app.models.roles import Roles
from app.constants import TABLE
from app.errors.web_exception import WebException


@mock_aws
class TestParkingRepository(unittest.IsolatedAsyncioTestCase):

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

        self.repo = ParkingRepository(db=self.dynamodb)

        self.user_id = "user001"
        self.building_id = "bldg001"
        self.floor_number = 1
        self.slot_id = 5
        self.numberplate = "ABC123"

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": "PROFILE",
            "Id": self.user_id,
            "Username": "testuser",
            "Email": "test@example.com",
            "PasswordHash": "hash",
            "OfficeId": "office001",
            "Role": Roles.CUSTOMER,
        })

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": f"VEHICLE#{self.numberplate}",
            "VehicleId": "vehicle001",
            "Numberplate": self.numberplate,
            "VehicleType": "TwoWheeler",
            "IsParked": False,
        })

        self.table.put_item(Item={
            "PK": "BUILDING",
            "SK": f"BUILDING#{self.building_id}",
            "BuildingId": self.building_id,
            "BuildingName": "Test Building",
            "TotalFloors": 1,
            "TotalSlots": 30,
            "AvailableSlots": 30,
        })

        self.table.put_item(Item={
            "PK": f"BUILDING#{self.building_id}",
            "SK": f"FLOORINFO#{self.floor_number}",
            "FloorNumber": self.floor_number,
            "TotalSlots": 30,
            "AvailableSlots": 30,
        })

        self.table.put_item(Item={
            "PK": f"BUILDING#{self.building_id}",
            "SK": f"FLOOR#{self.floor_number}#SLOT#{self.slot_id}",
            "SlotId": self.slot_id,
            "SlotType": "TwoWheeler",
            "IsOccupied": False,
            "IsAssigned": False,
        })

    def tearDown(self):
        self.table.delete()

    async def test_add_parking_success(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking001",
            vehicle_type="TwoWheeler"
        )

        await self.repo.add_parking(parking)

        parking_response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": f"PARKING#{start_time}"
            }
        )
        self.assertIn("Item", parking_response)
        parking_item = parking_response["Item"]
        self.assertEqual(parking_item["Numberplate"], self.numberplate)
        self.assertEqual(parking_item["BuildingId"], self.building_id)

    async def test_add_parking_updates_vehicle(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking002",
            vehicle_type="TwoWheeler"
        )

        await self.repo.add_parking(parking)

        vehicle_response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": f"VEHICLE#{self.numberplate}"
            }
        )
        self.assertTrue(vehicle_response["Item"]["IsParked"])

    async def test_add_parking_updates_slot(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking003",
            vehicle_type="TwoWheeler"
        )

        await self.repo.add_parking(parking)

        slot_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#{self.slot_id}"
            }
        )
        slot = slot_response["Item"]
        self.assertTrue(slot["IsOccupied"])
        self.assertIn("OccupiedBy", slot)
        self.assertEqual(slot["OccupiedBy"]["NumberPlate"], self.numberplate)

    async def test_add_parking_decrements_available_slots(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking004",
            vehicle_type="TwoWheeler"
        )

        await self.repo.add_parking(parking)

        floor_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOORINFO#{self.floor_number}"
            }
        )
        self.assertEqual(floor_response["Item"]["AvailableSlots"], 29)

        building_response = self.table.get_item(
            Key={"PK": "BUILDING", "SK": f"BUILDING#{self.building_id}"}
        )
        self.assertEqual(building_response["Item"]["AvailableSlots"], 29)

    async def test_add_parking_user_not_found_raises_error(self):
        parking = ParkingHistory(
            user_id="nonexistent",
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=int(time.time()),
            parking_id="parking005",
            vehicle_type="TwoWheeler"
        )

        with self.assertRaises(WebException) as context:
            await self.repo.add_parking(parking)

        self.assertEqual(context.exception.status_code, 404)

    async def test_unpark_by_numberplate_success(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking006",
            vehicle_type="TwoWheeler"
        )
        await self.repo.add_parking(parking)

        await self.repo.unpark_by_numberplate(self.user_id, self.numberplate)

        parking_response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": f"PARKING#{start_time}"
            }
        )
        self.assertIn("EndTime", parking_response["Item"])
        self.assertIsNotNone(parking_response["Item"]["EndTime"])

    async def test_unpark_updates_vehicle(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking007",
            vehicle_type="TwoWheeler"
        )
        await self.repo.add_parking(parking)

        await self.repo.unpark_by_numberplate(self.user_id, self.numberplate)

        vehicle_response = self.table.get_item(
            Key={
                "PK": f"USER#{self.user_id}",
                "SK": f"VEHICLE#{self.numberplate}"
            }
        )
        self.assertFalse(vehicle_response["Item"]["IsParked"])

    async def test_unpark_frees_slot(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking008",
            vehicle_type="TwoWheeler"
        )
        await self.repo.add_parking(parking)

        await self.repo.unpark_by_numberplate(self.user_id, self.numberplate)

        slot_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#{self.slot_id}"
            }
        )
        slot = slot_response["Item"]
        self.assertFalse(slot["IsOccupied"])
        self.assertIsNone(slot.get("OccupiedBy"))

    async def test_unpark_increments_available_slots(self):
        start_time = int(time.time())
        parking = ParkingHistory(
            user_id=self.user_id,
            numberplate=self.numberplate,
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=self.slot_id,
            start_time=start_time,
            parking_id="parking009",
            vehicle_type="TwoWheeler"
        )
        await self.repo.add_parking(parking)

        await self.repo.unpark_by_numberplate(self.user_id, self.numberplate)

        floor_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOORINFO#{self.floor_number}"
            }
        )
        self.assertEqual(floor_response["Item"]["AvailableSlots"], 30)

        building_response = self.table.get_item(
            Key={"PK": "BUILDING", "SK": f"BUILDING#{self.building_id}"}
        )
        self.assertEqual(building_response["Item"]["AvailableSlots"], 30)

    async def test_unpark_no_active_parking_raises_error(self):
        with self.assertRaises(WebException) as context:
            await self.repo.unpark_by_numberplate(self.user_id, self.numberplate)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("No active parking", context.exception.message)

    async def test_get_parking_history_success(self):
        start_time1 = 1700000000
        end_time1 = 1700010000
        start_time2 = 1700020000
        end_time2 = 1700030000

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": f"PARKING#{start_time1}",
            "Numberplate": self.numberplate,
            "BuildingId": self.building_id,
            "FloorNumber": self.floor_number,
            "SlotId": self.slot_id,
            "StartTime": start_time1,
            "EndTime": end_time1,
            "ParkingId": "parking010",
            "VehicleType": "TwoWheeler",
        })

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": f"PARKING#{start_time2}",
            "Numberplate": self.numberplate,
            "BuildingId": self.building_id,
            "FloorNumber": self.floor_number,
            "SlotId": self.slot_id,
            "StartTime": start_time2,
            "EndTime": end_time2,
            "ParkingId": "parking011",
            "VehicleType": "TwoWheeler",
        })

        result = await self.repo.get_parking_history(
            self.user_id,
            start_time1,
            start_time2 + 1
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], ParkingHistory)
        self.assertIsInstance(result[1], ParkingHistory)

    async def test_get_parking_history_empty(self):
        result = await self.repo.get_parking_history(
            self.user_id,
            1600000000,
            1600100000
        )

        self.assertEqual(len(result), 0)

    async def test_get_parking_history_filters_active_parking(self):
        completed_time = 1700000000
        active_time = 1700020000

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": f"PARKING#{completed_time}",
            "Numberplate": self.numberplate,
            "BuildingId": self.building_id,
            "FloorNumber": self.floor_number,
            "SlotId": self.slot_id,
            "StartTime": completed_time,
            "EndTime": 1700010000,
            "ParkingId": "parking012",
            "VehicleType": "TwoWheeler",
        })

        self.table.put_item(Item={
            "PK": f"USER#{self.user_id}",
            "SK": f"PARKING#{active_time}",
            "Numberplate": self.numberplate,
            "BuildingId": self.building_id,
            "FloorNumber": self.floor_number,
            "SlotId": self.slot_id,
            "StartTime": active_time,
            "ParkingId": "parking013",
            "VehicleType": "TwoWheeler",
        })

        result = await self.repo.get_parking_history(
            self.user_id,
            completed_time,
            active_time + 1
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].start_time, completed_time)


if __name__ == "__main__":
    unittest.main()
