from mypy_boto3_dynamodb.type_defs import PutTypeDef
from app.models.slot import OccupantDetails
from mypy_boto3_dynamodb.type_defs import UpdateItemInputTableUpdateItemTypeDef
from mypy_boto3_dynamodb.type_defs import UpdateTypeDef
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef
from app.errors.web_exception import DB_ERROR
from app.errors.web_exception import WebException
from typing import cast
import datetime
from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from typing import Annotated
from app.models.parking_history import ParkingHistory
from asyncio import to_thread

from starlette import status
from app.constants import TABLE
from app.dependencies import get_db
from boto3.dynamodb.conditions import Key, Attr

from app.models.user import User


class ParkingRepository:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)


    async def add_parking(self, parking: ParkingHistory):
        # item = {
        #     "PK": f"USER#{parking.user_id}",
        #     "SK": f"PARKING#{parking.start_time}",
        #     **parking.model_dump(exclude_none=True),
        # }
        #
        # await to_thread(lambda: self.table.put_item(Item=item))
        user_item = await to_thread(
            lambda: self.table.get_item(
                Key={
                    "PK": f"USER#{parking.user_id}",
                    "SK": f"PROFILE",
                }
            ).get("Item")
        )

        if not user_item:
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="No active parking found for the given user", error_code=DB_ERROR)

        user = User(**cast(dict, user_item))

        update_vehicle : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"USER#{parking.user_id}",
                    "SK": f"VEHICLE#{parking.numberplate}",
                },
                UpdateExpression="SET IsParked = :is_parked",
                ExpressionAttributeValues={
                    ":is_parked": True,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            )
        }

        update_slot : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"BUILDING#{parking.building_id}",
                    "SK": f"FLOOR#{parking.floor_number}#SLOT#{parking.slot_id}",
                },
                UpdateExpression="SET IsOccupied = :is_occupied, OccupiedBy = :occupied_by",
                ExpressionAttributeValues={
                    ":is_occupied": True,
                    ":occupied_by": OccupantDetails(
                        Username=user.username,
                        NumberPlate=parking.numberplate,
                        Email=user.email,
                        StartTime=parking.start_time,
                    ).model_dump(by_alias=True),
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            )
        }

        put_parking_history : TransactWriteItemTypeDef = {
            "Put": PutTypeDef(
                TableName=TABLE,
                Item={
                    "PK": f"USER#{user.user_id}",
                    "SK": f"PARKING#{parking.start_time}",
                    **parking.model_dump(by_alias=True),
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)",
            ),
        }

        await to_thread(
            lambda : self.table.meta.client.transact_write_items(
                TransactItems=[update_vehicle, update_slot, put_parking_history],
            )
        )


    async def unpark_by_numberplate(self, user_id: str, numberplate: str):
        parking = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("PARKING#"),
                FilterExpression=Attr("NumberPlate").eq(numberplate) & Attr("EndTime").not_exists(),
                Limit=1,
            ).get("Items")
        )

        if not parking:
            raise WebException(status_code=404, message="No active parking found for the given numberplate", error_code=DB_ERROR)

        parking_sk = parking[0]["SK"]
        await to_thread(
            lambda: self.table.update_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": parking_sk,
                },
                UpdateExpression="SET EndTime = :end_time",
                ExpressionAttributeValues={
                    ":end_time": int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
                }
            )
        )

    async def get_parking_history(self, user_id: str, start_time: int, end_time: int) -> list[ParkingHistory]:
        response = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").between(f"PARKING#{start_time}", f"PARKING#{end_time}"),
            ).get("Items", [])
        )
        
        return [ParkingHistory(**cast(dict, item)) for item in response]