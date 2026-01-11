import unittest

import bcrypt
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from moto import mock_aws

from app.constants import TABLE
from app.models.roles import Roles
from app.models.user import User
from app.repository.user_repo import UserRepository


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repo = UserRepository(self.dynamodb)

        self.existing_user_id = "user-1"
        self.existing_email = "kaushik@example.com"
        hashed_password = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode("utf-8")
        self.table.put_item(
            Item={"PK": "USER", "SK": self.existing_email, "UUID": self.existing_user_id}
        )
        self.table.put_item(
            Item={
                "PK": f"USER#{self.existing_user_id}",
                "SK": "PROFILE",
                "Username": "Kaushik",
                "PasswordHash": hashed_password,
                "Email": self.existing_email,
                "OfficeId": "office-1",
                "Id": self.existing_user_id,
                "Role": Roles.CUSTOMER,
            }
        )

    def tearDown(self):
        self.mock.stop()

    async def test_get_by_email_returns_user(self):
        user = await self.repo.get_by_email(self.existing_email)

        self.assertEqual(user.user_id, self.existing_user_id)
        self.assertEqual(user.email, self.existing_email)
        self.assertEqual(user.role, Roles.CUSTOMER)

    async def test_get_by_email_raises_for_missing(self):
        with self.assertRaises(HTTPException):
            await self.repo.get_by_email("missing@example.com")

    async def test_save_user_persists_user_and_lookup(self):
        new_user = User(
            Email="new@example.com",
            Username="New User",
            PasswordHash="hashed",
            OfficeId="office-2",
            Id="user-2",
            Role=Roles.ADMIN,
        )

        await self.repo.save_user(new_user)

        lookup = self.table.get_item(Key={"PK": "USER", "SK": "new@example.com"}).get("Item")
        profile = self.table.get_item(Key={"PK": "USER#user-2", "SK": "PROFILE"}).get("Item")
        self.assertEqual(lookup["UUID"], "user-2")
        self.assertEqual(profile["Email"], "new@example.com")
        self.assertEqual(profile["Role"], Roles.ADMIN)

    async def test_save_user_raises_for_duplicate_email(self):
        duplicate_user = User(
            Email=self.existing_email,
            Username="Duplicate",
            PasswordHash="hashed",
            OfficeId="office-1",
            Id="user-dup",
            Role=Roles.CUSTOMER,
        )

        with self.assertRaises(ClientError):
            await self.repo.save_user(duplicate_user)
