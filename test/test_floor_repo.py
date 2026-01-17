import unittest
import boto3
from moto import mock_aws
from unittest.mock import patch

from app.repository.floor_repo import FloorRepository
from app.models.floor import Floor
from app.models.slot import Slot, SlotType
from app.constants import TABLE, SLOT_LAYOUT


@mock_aws
class TestFloorRepository(unittest.IsolatedAsyncioTestCase):

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

        self.repo = FloorRepository(db=self.dynamodb)

        self.building_id = "bldg001"
        self.table.put_item(Item={
            "PK": "BUILDING",
            "SK": f"BUILDING#{self.building_id}",
            "BuildingId": self.building_id,
            "BuildingName": "Test Building",
            "TotalFloors": 0,
            "TotalSlots": 0,
            "AvailableSlots": 0,
        })

    def tearDown(self):
        self.table.delete()

    async def test_add_floor_success(self):
        floor_number = 1

        await self.repo.add_floor(self.building_id, floor_number)

        floor_info_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOORINFO#{floor_number}"
            }
        )
        self.assertIn("Item", floor_info_response)
        floor_item = floor_info_response["Item"]
        self.assertEqual(floor_item["FloorNumber"], floor_number)
        self.assertEqual(floor_item["TotalSlots"], len(SLOT_LAYOUT))
        self.assertEqual(floor_item["AvailableSlots"], len(SLOT_LAYOUT))

    async def test_add_floor_creates_slots(self):
        floor_number = 2

        await self.repo.add_floor(self.building_id, floor_number)

        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"BUILDING#{self.building_id}",
                ":sk": f"FLOOR#{floor_number}#SLOT#"
            }
        )

        slots = response.get("Items", [])
        self.assertEqual(len(slots), len(SLOT_LAYOUT))

        for idx, slot in enumerate(sorted(slots, key=lambda x: x["SlotId"])):
            expected_type = SlotType.TWO_WHEELER if SLOT_LAYOUT[idx] == '0' else SlotType.FOUR_WHEELER
            self.assertEqual(slot["SlotType"], expected_type)
            self.assertEqual(slot["SlotId"], idx + 1)
            self.assertFalse(slot["IsAssigned"])
            self.assertFalse(slot["IsOccupied"])

    async def test_add_floor_updates_building_stats(self):
        floor_number = 1

        await self.repo.add_floor(self.building_id, floor_number)

        building_response = self.table.get_item(
            Key={"PK": "BUILDING", "SK": f"BUILDING#{self.building_id}"}
        )
        building = building_response["Item"]
        self.assertEqual(building["TotalFloors"], 1)
        self.assertEqual(building["TotalSlots"], len(SLOT_LAYOUT))
        self.assertEqual(building["AvailableSlots"], len(SLOT_LAYOUT))

    async def test_add_floor_multiple_floors(self):
        await self.repo.add_floor(self.building_id, 1)
        await self.repo.add_floor(self.building_id, 2)
        await self.repo.add_floor(self.building_id, 3)

        building_response = self.table.get_item(
            Key={"PK": "BUILDING", "SK": f"BUILDING#{self.building_id}"}
        )
        building = building_response["Item"]
        self.assertEqual(building["TotalFloors"], 3)
        self.assertEqual(building["TotalSlots"], len(SLOT_LAYOUT) * 3)
        self.assertEqual(building["AvailableSlots"], len(SLOT_LAYOUT) * 3)

    async def test_add_floor_duplicate_raises_error(self):
        floor_number = 1
        await self.repo.add_floor(self.building_id, floor_number)

        with self.assertRaises(Exception):
            await self.repo.add_floor(self.building_id, floor_number)

    async def test_get_floors_empty(self):
        result = await self.repo.get_floors(self.building_id)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_floors_single(self):
        floor_number = 1
        await self.repo.add_floor(self.building_id, floor_number)

        result = await self.repo.get_floors(self.building_id)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Floor)
        self.assertEqual(result[0].floor_number, floor_number)
        self.assertEqual(result[0].building_id, self.building_id)
        self.assertEqual(result[0].total_slots, len(SLOT_LAYOUT))

    async def test_get_floors_multiple(self):
        await self.repo.add_floor(self.building_id, 1)
        await self.repo.add_floor(self.building_id, 2)
        await self.repo.add_floor(self.building_id, 3)

        result = await self.repo.get_floors(self.building_id)

        self.assertEqual(len(result), 3)
        floor_numbers = [f.floor_number for f in result]
        self.assertIn(1, floor_numbers)
        self.assertIn(2, floor_numbers)
        self.assertIn(3, floor_numbers)

    async def test_get_floors_different_buildings(self):
        building2_id = "bldg002"
        self.table.put_item(Item={
            "PK": "BUILDING",
            "SK": f"BUILDING#{building2_id}",
            "BuildingId": building2_id,
            "BuildingName": "Test Building 2",
            "TotalFloors": 0,
            "TotalSlots": 0,
            "AvailableSlots": 0,
        })

        await self.repo.add_floor(self.building_id, 1)
        await self.repo.add_floor(building2_id, 1)
        await self.repo.add_floor(building2_id, 2)

        result_bldg1 = await self.repo.get_floors(self.building_id)
        result_bldg2 = await self.repo.get_floors(building2_id)

        self.assertEqual(len(result_bldg1), 1)
        self.assertEqual(len(result_bldg2), 2)


if __name__ == "__main__":
    unittest.main()
