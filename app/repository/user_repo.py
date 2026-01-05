from asyncio import to_thread
from typing import cast, overload, Sequence, List
import boto3

from fastapi import Depends, HTTPException
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef, PutTypeDef

from app.constants import DB
from app.dependencies import get_db
from app.errors.web_exception import WebException, DB_ERROR
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
            raise HTTPException(status_code=409,detail="User not found")

        uid = uid_lookup_res.get("UUID")
        user_query_res = await to_thread(
            lambda: self.table.get_item(Key={"PK": f"USER#{uid}", "SK": "PROFILE"}).get(
                "Item"
            )
        )

        if user_query_res is None:
            raise WebException(status_code=409, message="User not found", error_code=DB_ERROR)
        return User(**cast(dict, user_query_res))

    async def save_user(self, user: User):
        # email_lookup_res = await to_thread(
        #     lambda: self.table.get_item(
        #         Key={"PK": "USER", "SK": user.email},
        #         ProjectionExpression="#uuid",
        #         ExpressionAttributeNames={"#uuid": "UUID"},
        #     ).get("Item")
        # )
        #
        # if email_lookup_res is not None:
        #     raise WebException(status_code=409, message="User already exists", error_code=DB_ERROR )
        #
        # client = boto3.client("dynamodb")
        put_lookup: TransactWriteItemTypeDef = {
            "Put":{
                "Item":{
                    "PK":"USER",
                    "SK":user.email,
                    "UUID":user.user_id,
                },
                "TableName":DB,
                "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
            }
        }

        put_user: TransactWriteItemTypeDef = {
            "Put":{
                "Item":{
                    "PK":f"USER#{user.user_id}",
                    "SK":"PROFILE",
                    **user.model_dump(by_alias=True),
                },
                "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                "TableName":DB,
            }
        }

        tx = await to_thread(
            lambda: self.table.meta.client.transact_write_items(
                TransactItems=[
                    put_lookup,
                    put_user
                ]
            )
        )

        # print(tx)

        # with self.table.batch_writer() as batch:
        #     batch.put_item({"PK": "USER", "SK": user.email, "UUID": user.user_id})
        #     batch.put_item(
        #         {
        #             **user.model_dump(by_alias=True),
        #             "PK": f"USER#{user.user_id}",
        #             "SK": "PROFILE",
        #         }
        #     )
