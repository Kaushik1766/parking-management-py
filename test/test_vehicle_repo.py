import unittest

import boto3
from moto import mock_aws

from app.constants import TABLE
from app.repository.vehicle_repo import VehicleRepository


class TestVehicleRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repo = VehicleRepository(self.dynamodb)

        self.table.put_item(
            Item={
                "PK": "USER#user-1",
                "SK": "VEHICLE#ABC123",
                "VehicleId": "veh-1",
                "Numberplate": "ABC123",
                "VehicleType": "FourWheeler",
                "IsParked": True,
                "AssignedSlot": {"BuildingId": "b1", "FloorNumber": 1, "SlotId": 2},
            }
        )
        self.table.put_item(
            Item={
                "PK": "USER#user-1",
                "SK": "VEHICLE#XYZ999",
                "VehicleId": "veh-2",
                "Numberplate": "XYZ999",
                "VehicleType": "TwoWheeler",
                "IsParked": False,
                "AssignedSlot": None,
            }
        )

    def tearDown(self):
        self.mock.stop()

    async def test_get_vehicles_by_user_id_returns_all(self):
        vehicles = await self.repo.get_vehicles_by_user_id("user-1")

        plates = sorted([v.number_plate for v in vehicles])
        self.assertEqual(plates, ["ABC123", "XYZ999"])

    async def test_get_vehicles_by_user_id_returns_empty_for_unknown(self):
        vehicles = await self.repo.get_vehicles_by_user_id("no-user")
        self.assertEqual(vehicles, [])

    async def test_get_vehicle_by_number_plate_returns_vehicle(self):
        vehicle = await self.repo.get_vehicle_by_number_plate("user-1", "ABC123")

        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.vehicle_id, "veh-1")
        self.assertTrue(vehicle.is_parked)

    async def test_get_vehicle_by_number_plate_returns_none_when_missing(self):
        vehicle = await self.repo.get_vehicle_by_number_plate("user-1", "NONE")
        self.assertIsNone(vehicle)
