from typing import cast
from asyncio import to_thread
from typing import List

from app.constants import TABLE
from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.dependencies import get_db
from app.models.vehicle import Vehicle
from boto3.dynamodb.conditions import Key

from app.errors.web_exception import WebException, DB_ERROR


class VehicleRepository:
    def __init__(self, db: DynamoDBServiceResource = Depends(get_db)):
        self.table = db.Table(TABLE)

    async def get_vehicles_by_user_id(self, user_id: str) -> List[Vehicle]:
        vehicles = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")
                & Key("SK").begins_with("VEHICLE#"),
                ProjectionExpression="VehicleId, Numberplate, VehicleType, IsParked, AssignedSlot",
            ).get("Items")
        )

        # print(vehicles)
        vehicle_res = []
        for i in vehicles:
            vehicle_res.append(Vehicle(**cast(dict, i)))

        return vehicle_res

    async def get_vehicle_by_number_plate(
        self, user_id: str, number_plate: str
    ) -> Vehicle | None:
        vehicle = await to_thread(
            lambda: self.table.get_item(
                Key={"PK": f"USER#{user_id}", "SK": f"VEHICLE#{number_plate}"},
                ProjectionExpression="VehicleId, Numberplate, VehicleType, IsParked, AssignedSlot",
            ).get("Item")
        )

        if vehicle is None:
            return None

        return Vehicle(**cast(dict, vehicle))

    async def save_vehicle(self, vehicle: Vehicle, user_id: str):
        await to_thread(
            lambda: self.table.put_item(
                Item={
                    **vehicle.model_dump(by_alias=True),
                    "PK": f"USER#{user_id}",
                    "SK": f"VEHICLE#{vehicle.number_plate}",
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)",
            )
        )

    async def delete_vehicle(self, user_id: str, number_plate: str):
        is_parked = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")
            & Key("SK").begins_with("PARKING#"),
            ProjectionExpression="IsParked",
            FilterExpression="attribute_not_exists(EndTime) and Numberplate = :np",
            ExpressionAttributeValues={":np": number_plate},
        ).get("Items")

        if len(is_parked) > 0:
            raise WebException(
                status_code=400,
                error_code=DB_ERROR,
                message="Cannot delete a vehicle that is currently parked.",
            )
        await to_thread(
            lambda: self.table.delete_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"VEHICLE#{number_plate}",
                },
                ConditionExpression="attribute_exists(PK) and attribute_exists(SK)",
            )
        )

