import unittest
import boto3
from moto import mock_aws

from app.repository.office_repo import OfficeRepository
from app.models.office import Office
from app.constants import TABLE


@mock_aws
class TestOfficeRepository(unittest.IsolatedAsyncioTestCase):

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
        
        self.repo = OfficeRepository(db=self.dynamodb)
        
        self.building_id = "bldg001"
        self.floor_number = 1
        self.table.put_item(Item={
            "PK": f"BUILDING#{self.building_id}",
            "SK": f"FLOORINFO#{self.floor_number}",
            "FloorNumber": self.floor_number,
            "TotalSlots": 30,
            "AvailableSlots": 30,
            "OfficeId": None,
        })
        
    def tearDown(self):
        self.table.delete()

    async def test_add_office_success(self):
        office = Office(
            office_name="Engineering Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office001"
        )
        
        await self.repo.add_office(office)
        
        office_response = self.table.get_item(
            Key={"PK": "OFFICE", "SK": "DETAILS#office001"}
        )
        self.assertIn("Item", office_response)
        office_item = office_response["Item"]
        self.assertEqual(office_item["OfficeName"], "Engineering Office")
        self.assertEqual(office_item["OfficeId"], "office001")

    async def test_add_office_updates_floor(self):
        office = Office(
            office_name="Sales Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office002"
        )
        
        await self.repo.add_office(office)
        
        floor_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOORINFO#{self.floor_number}"
            }
        )
        self.assertEqual(floor_response["Item"]["OfficeId"], "office002")

    async def test_add_office_duplicate_raises_error(self):
        office = Office(
            office_name="Office 1",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office003"
        )
        await self.repo.add_office(office)
        
        with self.assertRaises(Exception):
            await self.repo.add_office(office)

    async def test_add_office_to_occupied_floor_raises_error(self):
        office1 = Office(
            office_name="First Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office004"
        )
        office2 = Office(
            office_name="Second Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office005"
        )
        await self.repo.add_office(office1)
        
        with self.assertRaises(Exception):
            await self.repo.add_office(office2)

    async def test_get_office_by_id_success(self):
        office = Office(
            office_name="HR Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office006"
        )
        await self.repo.add_office(office)
        
        result = await self.repo.get_office_by_id("office006")
        
        self.assertIsInstance(result, Office)
        self.assertEqual(result.office_id, "office006")
        self.assertEqual(result.office_name, "HR Office")
        self.assertEqual(result.building_id, self.building_id)
        self.assertEqual(result.floor_number, self.floor_number)

    async def test_get_offices_empty(self):
        result = await self.repo.get_offices()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_offices_multiple(self):
        floor2 = 2
        self.table.put_item(Item={
            "PK": f"BUILDING#{self.building_id}",
            "SK": f"FLOORINFO#{floor2}",
            "FloorNumber": floor2,
            "TotalSlots": 30,
            "AvailableSlots": 30,
            "OfficeId": None,
        })
        
        office1 = Office(
            office_name="Office A",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office007"
        )
        office2 = Office(
            office_name="Office B",
            building_id=self.building_id,
            floor_number=floor2,
            office_id="office008"
        )
        await self.repo.add_office(office1)
        await self.repo.add_office(office2)
        
        result = await self.repo.get_offices()
        
        self.assertEqual(len(result), 2)
        office_ids = [o.office_id for o in result]
        self.assertIn("office007", office_ids)
        self.assertIn("office008", office_ids)

    async def test_get_all_offices(self):
        office = Office(
            office_name="Complete Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office009"
        )
        await self.repo.add_office(office)
        
        result = await self.repo.get_all_offices()
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Office)

    async def test_delete_office_success(self):
        office = Office(
            office_name="Temp Office",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office010"
        )
        await self.repo.add_office(office)
        
        await self.repo.delete_office(self.building_id, self.floor_number, "office010")
        
        office_response = self.table.get_item(
            Key={"PK": "OFFICE", "SK": "DETAILS#office010"}
        )
        self.assertNotIn("Item", office_response)
        
        floor_response = self.table.get_item(
            Key={
                "PK": f"BUILDING#{self.building_id}",
                "SK": f"FLOORINFO#{self.floor_number}"
            }
        )
        self.assertNotIn("OfficeId", floor_response["Item"])

    async def test_delete_office_not_found_raises_error(self):
        with self.assertRaises(Exception):
            await self.repo.delete_office(self.building_id, self.floor_number, "nonexistent")

    async def test_delete_office_wrong_floor_raises_error(self):
        office = Office(
            office_name="Office to Delete",
            building_id=self.building_id,
            floor_number=self.floor_number,
            office_id="office011"
        )
        await self.repo.add_office(office)
        
        with self.assertRaises(Exception):
            await self.repo.delete_office(self.building_id, 999, "office011")


if __name__ == "__main__":
    unittest.main()
