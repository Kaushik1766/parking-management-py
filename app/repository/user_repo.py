from asyncio import to_thread
from typing import cast

from fastapi import Depends
from mypy_boto3_dynamodb import DynamoDBServiceResource

from app.constants import DB
from app.dependencies import get_db
from app.models.roles import Roles
from app.models.user import User


class UserRepository:
    def __init__(self, db: DynamoDBServiceResource = Depends(get_db)) -> None:
        self.db = db
        self.table = db.Table(DB)

    async def get_by_email(self, email: str):
        uid_lookup_res = await to_thread(
            lambda: self.table.get_item(
                Key={"PK": "USER", "SK": email},
                ProjectionExpression="#uuid",
                ExpressionAttributeNames={"#uuid": "UUID"},
            ).get("Item")
        )

        if uid_lookup_res is None:
            raise Exception("User not found")

        uid = uid_lookup_res.get("UUID")
        user_query_res = await to_thread(
            lambda: self.table.get_item(Key={"PK": f"USER#{uid}", "SK": "PROFILE"}).get(
                "Item"
            )
        )

        if user_query_res is None:
            raise Exception("User not found")
        return User(**cast(dict, user_query_res))

    async def save_user(self, user: User):
        email_lookup_res = await to_thread(
            lambda: self.table.get_item(
                Key={"PK": "USER", "SK": user.email},
                ProjectionExpression="#uuid",
                ExpressionAttributeNames={"#uuid": "UUID"},
            ).get("Item")
        )

        if email_lookup_res is not None:
            raise Exception("User already exists")

        with self.table.batch_writer() as batch:
            batch.put_item({"PK": "USER", "SK": user.email, "UUID": user.user_id})
            batch.put_item(
                {
                    **user.model_dump(by_alias=True),
                    "PK": f"USER#{user.user_id}",
                    "SK": "PROFILE",
                }
            )
