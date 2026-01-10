import time

from fastapi.exceptions import ValidationException
from mypy_boto3_dynamodb.type_defs import PutTypeDef
from pydantic import ValidationError
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

        decrement_floor_available: TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"BUILDING#{parking.building_id}",
                    "SK": f"FLOORINFO#{parking.floor_number}",
                },
                UpdateExpression="SET AvailableSlots = AvailableSlots - :one",
                ExpressionAttributeValues={
                    ":one": 1,
                    ":zero": 0,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK) and AvailableSlots > :zero",
                TableName=TABLE,
            )
        }

        decrement_building_available: TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": "BUILDING",
                    "SK": f"BUILDING#{parking.building_id}",
                },
                UpdateExpression="SET AvailableSlots = AvailableSlots - :one",
                ExpressionAttributeValues={
                    ":one": 1,
                    ":zero": 0,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK) and AvailableSlots > :zero",
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

        try:
            await to_thread(
                lambda : self.table.meta.client.transact_write_items(
                        TransactItems=[
                            update_vehicle,
                            update_slot,
                            decrement_floor_available,
                            decrement_building_available,
                            put_parking_history,
                        ],
                )
            )
        except self.table.meta.client.exceptions.TransactionCanceledException as e:
            print(e.response.get("CancellationReasons"))
            raise WebException(status_code=status.HTTP_409_CONFLICT, message="Parking creation failed due to conflict", error_code=DB_ERROR) from e


    async def unpark_by_numberplate(self, user_id: str, numberplate: str):
        print(f"userid = {user_id}, numberplate = {numberplate}")
        parking_items = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("PARKING#"),
                FilterExpression=(
                    Attr("Numberplate").eq(numberplate)
                    & (
                        Attr("EndTime").not_exists()
                        | Attr("EndTime").eq(None)
                        | Attr("EndTime").eq("null")
                    )
                ),
            ).get("Items", [])
        )

        if not parking_items:
            raise WebException(status_code=404, message="No active parking found for the given numberplate", error_code=DB_ERROR)

        active_parking = parking_items[0]
        print(active_parking)
        parking_sk = active_parking["SK"]
        parking = ParkingHistory(
            user_id=user_id,
            **cast(dict, active_parking)
        )


        update_vehicle : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"VEHICLE#{numberplate}",
                },
                UpdateExpression="SET IsParked = :is_parked",
                ExpressionAttributeValues={
                    ":is_parked": False,
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
                    ":is_occupied": False,
                    ":occupied_by": None,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            )
        }

        increment_floor_available : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"BUILDING#{parking.building_id}",
                    "SK": f"FLOORINFO#{parking.floor_number}",
                },
                UpdateExpression="SET AvailableSlots = AvailableSlots + :one",
                ExpressionAttributeValues={
                    ":one": 1,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            )
        }

        increment_building_available : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": "BUILDING",
                    "SK": f"BUILDING#{parking.building_id}",
                },
                UpdateExpression="SET AvailableSlots = AvailableSlots + :one",
                ExpressionAttributeValues={
                    ":one": 1,
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            )
        }

        update_parking_history : TransactWriteItemTypeDef = {
            "Update": UpdateTypeDef(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": parking_sk,
                },
                UpdateExpression="SET EndTime = :end_time",
                ExpressionAttributeValues={
                    ":end_time": int(time.time()),
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
                TableName=TABLE,
            ),
        }

        await to_thread(
            lambda : self.table.meta.client.transact_write_items(
                TransactItems=[
                    update_vehicle,
                    update_slot,
                    increment_floor_available,
                    increment_building_available,
                    update_parking_history,
                ],
            )
        )


    async def get_parking_history(self, user_id: str, start_time: int, end_time: int) -> list[ParkingHistory]:
        response = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").between(f"PARKING#{start_time}", f"PARKING#{end_time}"),
                FilterExpression=Attr("EndTime").attribute_type("N")
            ).get("Items", [])
        )
        
        history = []
        try:
            history =[ParkingHistory(
                user_id=user_id,
                **cast(dict, item)) for item in response
            ] 
        except ValidationError as e:
            print("Data validation error while fetching parking history:", e.errors())
            raise WebException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Data validation error while fetching parking history", error_code=DB_ERROR) from e
        return history