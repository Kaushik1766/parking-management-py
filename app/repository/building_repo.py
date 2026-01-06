from asyncio import to_thread

from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from starlette import status

from app.dependencies import get_db
from app.constants import TABLE
from app.errors.web_exception import WebException, DB_ERROR
from app.models.building import Building
from typing import cast


class BuildingRepository:
    def __init__(self, db: DynamoDBServiceResource = Depends(get_db)):
        self.db = db
        self.table = db.Table(TABLE)

    async def get_building_by_id(self, building_id: str) -> Building:
        building = await to_thread(
            lambda: self.table.get_item(
                Key={
                    "PK": "BUILDING",
                    "SK": f"BUILDING#{building_id}"
                },
                ProjectionExpression="BuildingId, BuildingName, TotalFloors, AvailableSlots",
            ).get("Item")
        )

        if building is None:
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="Building not found", error_code=DB_ERROR)

        return Building(**cast(dict, building))

    async def add_building(self, building: Building):
        await to_thread(
            lambda : self.table.put_item(
                Item={
                    **building.model_dump(by_alias=True),
                    "PK": "BUILDING",
                    "SK": f"BUILDING#{building.id}",
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)",
            )
        )