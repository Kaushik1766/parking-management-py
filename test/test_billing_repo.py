import unittest
from unittest.mock import AsyncMock, MagicMock
import boto3
from moto import mock_aws

from app.repository.billing_repo import BillingRepository
from app.models.bill import Bill, BillingParkingHistory
from app.constants import TABLE


@mock_aws
class TestBillingRepository(unittest.IsolatedAsyncioTestCase):

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
        self.repo = BillingRepository(db=self.dynamodb)
        
    def tearDown(self):
        self.table.delete()

    async def test_get_bill_success(self):
        user_id = "user123"
        month = 11
        year = 2023
        
        bill_data = {
            "PK": f"USER#{user_id}",
            "SK": f"BILL#{year}#{month}",
            "BillingMonth": month,
            "BillingYear": year,
            "TotalAmount": 150.50,
            "BillDate": "2023-12-01",
            "ParkingHistory": [
                {
                    "TicketId": "ticket1",
                    "NumberPlate": "ABC123",
                    "BuildingId": "bldg1",
                    "BuildingName": "Building A",
                    "FloorNumber": 1,
                    "SlotNumber": 5,
                    "VehicleType": "TwoWheeler",
                    "StartTime": 1700000000,
                    "EndTime": 1700010000,
                }
            ]
        }
        self.table.put_item(Item=bill_data)
        
        result = await self.repo.get_bill(user_id, month, year)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Bill)
        self.assertEqual(result.billing_month, month)
        self.assertEqual(result.billing_year, year)
        self.assertEqual(result.total_amount, 150.50)
        self.assertEqual(len(result.parking_history), 1)

    async def test_get_bill_not_found(self):
        user_id = "nonexistent"
        month = 1
        year = 2023
        
        result = await self.repo.get_bill(user_id, month, year)
        
        self.assertIsNone(result)

    async def test_get_bill_with_empty_parking_history(self):
        user_id = "user456"
        month = 12
        year = 2023
        
        bill_data = {
            "PK": f"USER#{user_id}",
            "SK": f"BILL#{year}#{month}",
            "BillingMonth": month,
            "BillingYear": year,
            "TotalAmount": 0.0,
            "BillDate": "2023-12-31",
            "ParkingHistory": []
        }
        self.table.put_item(Item=bill_data)
        
        result = await self.repo.get_bill(user_id, month, year)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.parking_history), 0)
        self.assertEqual(result.total_amount, 0.0)

    async def test_get_bill_multiple_parking_entries(self):
        user_id = "user789"
        month = 10
        year = 2023
        
        bill_data = {
            "PK": f"USER#{user_id}",
            "SK": f"BILL#{year}#{month}",
            "BillingMonth": month,
            "BillingYear": year,
            "TotalAmount": 300.75,
            "BillDate": "2023-11-01",
            "ParkingHistory": [
                {
                    "TicketId": "ticket1",
                    "NumberPlate": "XYZ789",
                    "BuildingId": "bldg1",
                    "BuildingName": "Building A",
                    "FloorNumber": 2,
                    "SlotNumber": 10,
                    "VehicleType": "FourWheeler",
                    "StartTime": 1700000000,
                    "EndTime": 1700010000,
                },
                {
                    "TicketId": "ticket2",
                    "NumberPlate": "ABC456",
                    "BuildingId": "bldg2",
                    "BuildingName": "Building B",
                    "FloorNumber": 1,
                    "SlotNumber": 3,
                    "VehicleType": "TwoWheeler",
                    "StartTime": 1700020000,
                    "EndTime": 1700030000,
                }
            ]
        }
        self.table.put_item(Item=bill_data)
        
        result = await self.repo.get_bill(user_id, month, year)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.parking_history), 2)
        self.assertEqual(result.total_amount, 300.75)


if __name__ == "__main__":
    unittest.main()
