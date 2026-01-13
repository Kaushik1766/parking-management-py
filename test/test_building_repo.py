import unittest
import boto3
from moto import mock_aws

from app.repository.building_repo import BuildingRepository
from app.models.building import Building
from app.constants import TABLE
from app.errors.web_exception import WebException


@mock_aws
class TestBuildingRepository(unittest.IsolatedAsyncioTestCase):

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
        
        self.repo = BuildingRepository(db=self.dynamodb)
        
    def tearDown(self):
        self.table.delete()

    async def test_get_building_by_id_success(self):
        building_id = "bldg001"
        building_data = {
            "PK": "BUILDING",
            "SK": f"BUILDING#{building_id}",
            "BuildingId": building_id,
            "BuildingName": "Main Building",
            "TotalFloors": 5,
            "TotalSlots": 100,
            "AvailableSlots": 75,
        }
        self.table.put_item(Item=building_data)
        
        result = await self.repo.get_building_by_id(building_id)
        
        self.assertIsInstance(result, Building)
        self.assertEqual(result.id, building_id)
        self.assertEqual(result.name, "Main Building")
        self.assertEqual(result.total_floors, 5)
        self.assertEqual(result.total_slots, 100)
        self.assertEqual(result.available_slots, 75)

    async def test_get_building_by_id_not_found(self):
        building_id = "nonexistent"
        
        with self.assertRaises(WebException) as context:
            await self.repo.get_building_by_id(building_id)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("not found", context.exception.message.lower())

    async def test_get_buildings_empty(self):
        result = await self.repo.get_buildings()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_buildings_single(self):
        building_data = {
            "PK": "BUILDING",
            "SK": "BUILDING#bldg001",
            "BuildingId": "bldg001",
            "BuildingName": "Building A",
            "TotalFloors": 3,
            "TotalSlots": 60,
            "AvailableSlots": 45,
        }
        self.table.put_item(Item=building_data)
        
        result = await self.repo.get_buildings()
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Building)
        self.assertEqual(result[0].id, "bldg001")
        self.assertEqual(result[0].name, "Building A")

    async def test_get_buildings_multiple(self):
        buildings = [
            {
                "PK": "BUILDING",
                "SK": "BUILDING#bldg001",
                "BuildingId": "bldg001",
                "BuildingName": "Building A",
                "TotalFloors": 3,
                "TotalSlots": 60,
                "AvailableSlots": 45,
            },
            {
                "PK": "BUILDING",
                "SK": "BUILDING#bldg002",
                "BuildingId": "bldg002",
                "BuildingName": "Building B",
                "TotalFloors": 4,
                "TotalSlots": 80,
                "AvailableSlots": 60,
            },
            {
                "PK": "BUILDING",
                "SK": "BUILDING#bldg003",
                "BuildingId": "bldg003",
                "BuildingName": "Building C",
                "TotalFloors": 2,
                "TotalSlots": 40,
                "AvailableSlots": 30,
            }
        ]
        
        for building in buildings:
            self.table.put_item(Item=building)
        
        result = await self.repo.get_buildings()
        
        self.assertEqual(len(result), 3)
        building_ids = [b.id for b in result]
        self.assertIn("bldg001", building_ids)
        self.assertIn("bldg002", building_ids)
        self.assertIn("bldg003", building_ids)

    async def test_add_building_success(self):
        building = Building(
            BuildingId="bldg999",
            BuildingName="New Building",
            TotalFloors=0,
            TotalSlots=0,
            AvailableSlots=0,
        )
        
        await self.repo.add_building(building)
        
        response = self.table.get_item(
            Key={"PK": "BUILDING", "SK": "BUILDING#bldg999"}
        )
        self.assertIn("Item", response)
        item = response["Item"]
        self.assertEqual(item["BuildingId"], "bldg999")
        self.assertEqual(item["BuildingName"], "New Building")

    async def test_add_building_duplicate_raises_error(self):
        building = Building(
            BuildingId="bldg888",
            BuildingName="Test Building",
            TotalFloors=0,
            TotalSlots=0,
            AvailableSlots=0,
        )
        
        await self.repo.add_building(building)
        
        with self.assertRaises(Exception):
            await self.repo.add_building(building)

    async def test_add_building_with_initial_values(self):
        building = Building(
            BuildingId="bldg777",
            BuildingName="Pre-configured Building",
            TotalFloors=10,
            TotalSlots=200,
            AvailableSlots=150,
        )
        
        await self.repo.add_building(building)
        
        result = await self.repo.get_building_by_id("bldg777")
        self.assertEqual(result.total_floors, 10)
        self.assertEqual(result.total_slots, 200)
        self.assertEqual(result.available_slots, 150)


if __name__ == "__main__":
    unittest.main()
