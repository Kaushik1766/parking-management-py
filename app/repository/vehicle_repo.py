from asyncio import to_thread
from typing import List

from app.constants import DB
from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.dependencies import get_db
from app.models.vehicle import Vehicle
from boto3.dynamodb.conditions import Key

from app.errors.web_exception import WebException, DB_ERROR


class VehicleRepo:
    def __init__(self, db: DynamoDBServiceResource = Depends(get_db)):
        self.table = db.Table(DB)

    async def get_vehicles_by_user_id(self, user_id: str) -> List[Vehicle]:
        vehicles = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")&Key("SK").begins_with("VEHICLE#"),
                ProjectionExpression="VehicleId, Numberplate, VehicleType, IsParked, AssignedSlot",
            ).get("Items")
        )

        # print(vehicles)
        vehicle_res = []
        for i in vehicles:
            vehicle_res.append(Vehicle(**i))

        return vehicle_res