import unittest
import boto3
from moto import mock_aws

from app.repository.user_repo import UserRepository
from app.models.user import User
from app.models.roles import Roles
from app.constants import TABLE
from app.errors.web_exception import WebException
from fastapi import HTTPException


@mock_aws
class TestUserRepository(unittest.IsolatedAsyncioTestCase):

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
        
        self.repo = UserRepository(db=self.dynamodb)
        
    def tearDown(self):
        self.table.delete()

    async def test_get_by_email_success(self):
        user_id = "user001"
        email = "test@example.com"
        
        self.table.put_item(Item={
            "PK": "USER",
            "SK": email,
            "UUID": user_id,
        })
        
        self.table.put_item(Item={
            "PK": f"USER#{user_id}",
            "SK": "PROFILE",
            "Id": user_id,
            "Username": "testuser",
            "Email": email,
            "PasswordHash": "hashed_password",
            "OfficeId": "office001",
            "Role": Roles.CUSTOMER,
        })
        
        result = await self.repo.get_by_email(email)
        
        self.assertIsInstance(result, User)
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.email, email)
        self.assertEqual(result.username, "testuser")
        self.assertEqual(result.role, Roles.CUSTOMER)

    async def test_get_by_email_not_found_in_lookup(self):
        with self.assertRaises(HTTPException) as context:
            await self.repo.get_by_email("nonexistent@example.com")
        
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("User not found", context.exception.detail)

    async def test_get_by_email_profile_not_found(self):
        user_id = "user002"
        email = "orphan@example.com"
        
        self.table.put_item(Item={
            "PK": "USER",
            "SK": email,
            "UUID": user_id,
        })
        
        with self.assertRaises(WebException) as context:
            await self.repo.get_by_email(email)
        
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("User not found", context.exception.message)

    async def test_save_user_success(self):
        user = User(
            Id="user003",
            Username="newuser",
            Email="newuser@example.com",
            PasswordHash="hashed_password",
            OfficeId="office001",
            Role=Roles.CUSTOMER
        )
        
        await self.repo.save_user(user)
        
        lookup_response = self.table.get_item(
            Key={"PK": "USER", "SK": "newuser@example.com"}
        )
        self.assertIn("Item", lookup_response)
        self.assertEqual(lookup_response["Item"]["UUID"], "user003")
        
        profile_response = self.table.get_item(
            Key={"PK": "USER#user003", "SK": "PROFILE"}
        )
        self.assertIn("Item", profile_response)
        profile = profile_response["Item"]
        self.assertEqual(profile["Username"], "newuser")
        self.assertEqual(profile["Email"], "newuser@example.com")

    async def test_save_user_duplicate_email_raises_error(self):
        user1 = User(
            Id="user004",
            Username="user1",
            Email="duplicate@example.com",
            PasswordHash="password1",
            OfficeId="office001",
            Role=Roles.CUSTOMER
        )
        
        user2 = User(
            Id="user005",
            Username="user2",
            Email="duplicate@example.com",
            PasswordHash="password2",
            OfficeId="office002",
            Role=Roles.CUSTOMER
        )
        
        await self.repo.save_user(user1)
        
        with self.assertRaises(Exception):
            await self.repo.save_user(user2)

    async def test_save_user_duplicate_user_id_raises_error(self):
        user1 = User(
            Id="user006",
            Username="first",
            Email="first@example.com",
            PasswordHash="password1",
            OfficeId="office001",
            Role=Roles.CUSTOMER
        )
        
        user2 = User(
            Username="second",
            Email="second@example.com",
            PasswordHash="password2",
            OfficeId="office002",
            Role=Roles.CUSTOMER
        )
        
        await self.repo.save_user(user1)
        
        with self.assertRaises(Exception):
            await self.repo.save_user(user2)

    async def test_save_user_with_admin_role(self):
        admin_user = User(
            Id="admin001",
            Username="adminuser",
            Email="admin@example.com",
            PasswordHash="admin_password",
            OfficeId="office001",
            Role=Roles.ADMIN
        )
        
        await self.repo.save_user(admin_user)
        
        result = await self.repo.get_by_email("admin@example.com")
        self.assertEqual(result.role, Roles.ADMIN)

    async def test_save_user_transactional_integrity(self):
        existing_email = "existing@example.com"
        self.table.put_item(Item={
            "PK": "USER",
            "SK": existing_email,
            "UUID": "existing_user",
        })
        
        user = User(
            Id="user007",
            Username="newuser",
            Email=existing_email,
            PasswordHash="password",
            OfficeId="office001",
            Role=Roles.CUSTOMER
        )
        
        with self.assertRaises(Exception):
            await self.repo.save_user(user)
        
        profile_response = self.table.get_item(
            Key={"PK": "USER#user007", "SK": "PROFILE"}
        )
        self.assertNotIn("Item", profile_response)

    async def test_get_by_email_with_all_fields(self):
        user_id = "user008"
        email = "complete@example.com"
        
        self.table.put_item(Item={
            "PK": "USER",
            "SK": email,
            "UUID": user_id,
        })
        
        self.table.put_item(Item={
            "PK": f"USER#{user_id}",
            "SK": "PROFILE",
            "Id": user_id,
            "Username": "completeuser",
            "Email": email,
            "PasswordHash": "secure_hash_123",
            "OfficeId": "office999",
            "Role": Roles.CUSTOMER,
        })
        
        result = await self.repo.get_by_email(email)
        
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.username, "completeuser")
        self.assertEqual(result.email, email)
        self.assertEqual(result.password, "secure_hash_123")
        self.assertEqual(result.office_id, "office999")
        self.assertEqual(result.role, Roles.CUSTOMER)

    async def test_save_multiple_users(self):
        users = [
            User(
                Id=f"user{i}",
                Username=f"user{i}",
                Email=f"user{i}@example.com",
                PasswordHash=f"password{i}",
                OfficeId="office001",
                Role=Roles.CUSTOMER
            )
            for i in range(10, 15)
        ]
        
        for user in users:
            await self.repo.save_user(user)
        
        for i in range(10, 15):
            result = await self.repo.get_by_email(f"user{i}@example.com")
            self.assertEqual(result.user_id, f"user{i}")


if __name__ == "__main__":
    unittest.main()
