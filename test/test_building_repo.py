import unittest

import boto3
from moto import mock_aws

from app.constants import TABLE
from app.errors.web_exception import WebException
from app.models.building import Building
from app.repository.building_repo import BuildingRepository


class TestBuildingRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock = mock_aws()
        self.mock.start()
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
        self.table.wait_until_exists()
        self.repo = BuildingRepository(self.dynamodb)

        self.table.put_item(
            Item={
                "PK": "BUILDING",
                "SK": "BUILDING#b1",
                "BuildingId": "b1",
                "BuildingName": "HQ",
                "TotalFloors": 3,
                "TotalSlots": 30,
                "AvailableSlots": 20,
            }
        )

    def tearDown(self):
        self.mock.stop()

    async def test_get_building_by_id_returns_building(self):
        building = await self.repo.get_building_by_id("b1")

        self.assertEqual(building.id, "b1")
        self.assertEqual(building.name, "HQ")
        self.assertEqual(building.total_floors, 3)

    async def test_get_building_by_id_raises_when_missing(self):
        with self.assertRaises(WebException):
            await self.repo.get_building_by_id("missing")

    async def test_get_buildings_returns_all(self):
        self.table.put_item(
            Item={
                "PK": "BUILDING",
                "SK": "BUILDING#b2",
                "BuildingId": "b2",
                "BuildingName": "Annex",
                "TotalFloors": 2,
                "TotalSlots": 10,
                "AvailableSlots": 8,
            }
        )

        buildings = await self.repo.get_buildings()

        ids = sorted([b.id for b in buildings])
        self.assertEqual(ids, ["b1", "b2"])

    async def test_add_building_persists_record(self):
        new_building = Building(
            BuildingId="b3",
            BuildingName="Warehouse",
            TotalFloors=1,
            TotalSlots=5,
            AvailableSlots=5,
        )

        await self.repo.add_building(new_building)

        stored = self.table.get_item(Key={"PK": "BUILDING", "SK": "BUILDING#b3"}).get("Item")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["BuildingName"], "Warehouse")
