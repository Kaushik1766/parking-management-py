from app.errors.web_exception import DB_ERROR
from app.errors.web_exception import WebException
from typing import cast
import datetime
from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from typing import Annotated
from app.models.parking_history import ParkingHistory
from asyncio import to_thread

from app.constants import TABLE
from app.dependencies import get_db
from boto3.dynamodb.conditions import Key, Attr


class ParkingRepostiory:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)


    async def add_parking(self, parking: ParkingHistory):
        item = {
            "PK": f"USER#{parking.user_id}",
            "SK": f"PARKING#{parking.start_time}",
            **parking.model_dump(exclude_none=True),
        }

        await to_thread(lambda: self.table.put_item(Item=item))

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