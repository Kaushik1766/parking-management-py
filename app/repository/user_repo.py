from typing import cast
from fastapi import Depends
from mypy_boto3_dynamodb import DynamoDBServiceResource

from app.constants import DB
from app.dependencies import get_db
from app.models.roles import Roles
from app.models.user import User


class UserRepository:
    def __init__(self, db: DynamoDBServiceResource = Depends(get_db)) -> None:
        self.db = db.Table(DB)

    async def get_by_email(self, email: str):
        uid_lookup_res = self.db.get_item(
            Key={"PK": "USER", "SK": email},
            ProjectionExpression="#uuid",
            ExpressionAttributeNames={"#uuid": "UUID"},
        ).get("Item")

        if uid_lookup_res is None:
            raise Exception("User not found")

        uid = uid_lookup_res.get("UUID")
        user_query_res = self.db.get_item(
            Key={"PK": f"USER#{uid}", "SK": "PROFILE"}
        ).get("Item")

        if user_query_res is None:
            raise Exception("User not found")
        return User(**cast(dict, user_query_res))
