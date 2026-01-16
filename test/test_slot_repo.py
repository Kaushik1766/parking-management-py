import unittest
import boto3
from moto import mock_aws

from app.repository.slot_repo import SlotRepository
from app.models.floor import Floor
from app.models.slot import Slot, SlotType, OccupantDetails
from app.constants import TABLE


@mock_aws
class TestSlotRepository(unittest.IsolatedAsyncioTestCase):
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

        self.repo = SlotRepository(db=self.dynamodb)

        self.building_id = "bldg001"
        self.floor_number = 1

        for i in range(1, 6):
            slot_type = SlotType.TWO_WHEELER if i <= 3 else SlotType.FOUR_WHEELER
            self.table.put_item(
                Item={
                    "PK": f"BUILDING#{self.building_id}",
                    "SK": f"FLOOR#{self.floor_number}#SLOT#{i}",
                    "SlotId": i,
                    "SlotType": slot_type,
                    "IsAssigned": False,
                    "IsOccupied": False,
                }
            )

    def tearDown(self):
        self.table.delete()

    async def test_get_slots_by_floor_success(self):
        floor = Floor(
            building_id=self.building_id,
            floor_number=self.floor_number,
            total_slots=5,
            available_slots=5,
        )

        result = await self.repo.get_slots_by_floor(floor)

        self.assertEqual(len(result), 5)
        for slot in result:
            self.assertIsInstance(slot, Slot)
            self.assertEqual(slot.building_id, self.building_id)
            self.assertEqual(slot.floor_number, self.floor_number)

    async def test_get_slots_by_floor_empty(self):
        floor = Floor(
            building_id="bldg999", floor_number=99, total_slots=0, available_slots=0
        )

        result = await self.repo.get_slots_by_floor(floor)

        self.assertEqual(len(result), 0)

    async def test_get_slots_by_floor_correct_types(self):
        floor = Floor(
            building_id=self.building_id,
            floor_number=self.floor_number,
            total_slots=5,
            available_slots=5,
        )

        result = await self.repo.get_slots_by_floor(floor)

        two_wheeler_count = sum(
            1 for s in result if s.slot_type == SlotType.TWO_WHEELER
        )
        four_wheeler_count = sum(
            1 for s in result if s.slot_type == SlotType.FOUR_WHEELER
        )

        self.assertEqual(two_wheeler_count, 3)
        self.assertEqual(four_wheeler_count, 2)

    async def test_get_free_slots_by_floor_all_free(self):
        floor = Floor(
            building_id=self.building_id,
            floor_number=self.floor_number,
            total_slots=5,
            available_slots=5,
        )

        result = await self.repo.get_free_slots_by_floor(floor)

        self.assertEqual(len(result), 5)
        for slot in result:
            self.assertFalse(slot.is_assigned)

    async def test_get_free_slots_by_floor_some_assigned(self):
        # Assign slot 1 and 3
        self.table.update_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#1",
            },
            UpdateExpression="SET IsAssigned = :val",
            ExpressionAttributeValues={":val": True},
        )
        self.table.update_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#3",
            },
            UpdateExpression="SET IsAssigned = :val",
            ExpressionAttributeValues={":val": True},
        )

        floor = Floor(
            building_id=self.building_id,
            floor_number=self.floor_number,
            total_slots=5,
            available_slots=3,
        )

        result = await self.repo.get_free_slots_by_floor(floor)

        self.assertEqual(len(result), 3)
        slot_ids = [s.slot_id for s in result]
        self.assertNotIn(1, slot_ids)
        self.assertNotIn(3, slot_ids)

    async def test_get_free_slots_by_floor_none_free(self):
        # Assign all slots
        for i in range(1, 6):
            self.table.update_item(
                Key={
                    "PK": f"BUILDING#{self.building_id}",
                    "SK": f"FLOOR#{self.floor_number}#SLOT#{i}",
                },
                UpdateExpression="SET IsAssigned = :val",
                ExpressionAttributeValues={":val": True},
            )

        floor = Floor(
            building_id=self.building_id,
            floor_number=self.floor_number,
            total_slots=5,
            available_slots=0,
        )

        result = await self.repo.get_free_slots_by_floor(floor)

        self.assertEqual(len(result), 0)

    async def test_update_slot_success(self):
        occupant = OccupantDetails(
            username="testuser",
            number_plate="ABC123",
            email="test@example.com",
            start_time=1700000000,
        )

        slot = Slot(
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=2,
            slot_type=SlotType.TWO_WHEELER,
            is_assigned=True,
            is_occupied=True,
            occupied_by=occupant,
        )

        await self.repo.update_slot(slot)

        response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#2",
            }
        )
        item = response["Item"]
        self.assertTrue(item["IsAssigned"])
        self.assertIn("OccupiedBy", item)
        self.assertEqual(item["OccupiedBy"]["Username"], "testuser")

    async def test_update_slot_clear_occupant(self):
        occupant = OccupantDetails(
            username="testuser",
            number_plate="ABC123",
            email="test@example.com",
            start_time=1700000000,
        )

        slot = Slot(
            building_id=self.building_id,
            floor_number=self.floor_number,
            slot_id=3,
            slot_type=SlotType.TWO_WHEELER,
            is_assigned=True,
            is_occupied=True,
            occupied_by=occupant,
        )
        await self.repo.update_slot(slot)

        slot.occupied_by = None
        slot.is_assigned = False
        await self.repo.update_slot(slot)

        response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#3",
            }
        )
        item = response["Item"]
        self.assertFalse(item["IsAssigned"])
        self.assertIsNone(item.get("OccupiedBy"))

    async def test_update_slot_occupancy_occupied(self):
        occupant = OccupantDetails(
            username="parkinguser",
            number_plate="XYZ789",
            email="parking@example.com",
            start_time=1700010000,
        )

        await self.repo.update_slot_occupancy(
            self.building_id, self.floor_number, 4, occupant, True
        )

        response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#4",
            }
        )
        item = response["Item"]
        self.assertTrue(item["IsOccupied"])
        self.assertIn("OccupiedBy", item)
        self.assertEqual(item["OccupiedBy"]["NumberPlate"], "XYZ789")

    async def test_update_slot_occupancy_vacant(self):
        occupant = OccupantDetails(
            username="tempuser",
            number_plate="TMP456",
            email="temp@example.com",
            start_time=1700020000,
        )
        await self.repo.update_slot_occupancy(
            self.building_id, self.floor_number, 5, occupant, True
        )

        await self.repo.update_slot_occupancy(
            self.building_id, self.floor_number, 5, None, False
        )

        response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#5",
            }
        )
        item = response["Item"]
        self.assertFalse(item["IsOccupied"])
        self.assertIsNone(item.get("OccupiedBy"))

    async def test_update_slot_occupancy_different_floors(self):
        floor2 = 2
        self.table.put_item(
            Item={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{floor2}#SLOT#1",
                "SlotId": 1,
                "SlotType": SlotType.TWO_WHEELER,
                "IsAssigned": False,
                "IsOccupied": False,
            }
        )

        occupant1 = OccupantDetails(
            username="user1",
            number_plate="AAA111",
            email="user1@example.com",
            start_time=1700000000,
        )
        occupant2 = OccupantDetails(
            username="user2",
            number_plate="BBB222",
            email="user2@example.com",
            start_time=1700010000,
        )

        await self.repo.update_slot_occupancy(
            self.building_id, self.floor_number, 1, occupant1, True
        )
        await self.repo.update_slot_occupancy(
            self.building_id, floor2, 1, occupant2, True
        )

        response1 = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOOR#{self.floor_number}#SLOT#1",
            }
        )
        response2 = self.table.get_item(
            Key={"PK": f"BUILDING#{self.building_id}", "SK": f"FLOOR#{floor2}#SLOT#1"}
        )

        self.assertEqual(response1["Item"]["OccupiedBy"]["NumberPlate"], "AAA111")
        self.assertEqual(response2["Item"]["OccupiedBy"]["NumberPlate"], "BBB222")


if __name__ == "__main__":
    unittest.main()
