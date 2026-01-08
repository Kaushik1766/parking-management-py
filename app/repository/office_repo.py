import boto3
from typing import cast
from asyncio.threads import to_thread
from typing import Annotated

from boto3.dynamodb.conditions import Key
from fastapi.params import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.constants import TABLE
from app.dependencies import get_db
from app.models.office import Office

class OfficeRepository:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)

    async def add_office(self, office: Office):
        await to_thread(
            lambda :self.table.put_item(
                Item={
                    **office.model_dump(by_alias=True),
                    "PK":"OFFICE",
                    "SK":f"DETAILS#{office.office_id}",
                },
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        )

    async def get_office_by_id(self, office_id: str)->Office:
        office_item = await to_thread(
            lambda :self.table.get_item(
                Key={
                    "PK":"OFFICE",
                    "SK":f"DETAILS#{office_id}",
                }
            ).get("Item")
        )

        return Office(**cast(dict, office_item))

    async def get_offices(self) -> list[Office]:
        offices = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq("OFFICE") & Key("SK").begins_with("DETAILS#"),
                ProjectionExpression="OfficeName, BuildingId, FloorNumber, OfficeId",
            ).get("Items", [])
        )

        return [Office(**cast(dict, office)) for office in offices]

    async def get_all_offices(self) -> list[Office]:
        offices = await to_thread(
            lambda :self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq("OFFICE") & boto3.dynamodb.conditions.Key("SK").begins_with("DETAILS#"),
            ).get("Items", [])
        )

        return [Office(**cast(dict, o)) for o in offices]