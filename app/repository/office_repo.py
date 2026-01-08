from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef
from mypy_boto3_dynamodb.type_defs import UpdateItemInputTypeDef
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
        self.client = db.meta.client

    async def add_office(self, office: Office):
        put_office: TransactWriteItemTypeDef = {
            "Put": {
                "TableName": TABLE,
                "Item": {
                    **office.model_dump(by_alias=True),
                    "PK": "OFFICE",
                    "SK": f"DETAILS#{office.office_id}",
                },
                "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
            }
        }

        update_floor: TransactWriteItemTypeDef = {
            "Update": {
                "TableName": TABLE,
                "Key": {
                    "PK": f"BUILDING#{office.building_id}",
                    "SK": f"FLOORINFO#{office.floor_number}",
                },
                "UpdateExpression": "SET OfficeId = :office_id",
                "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK) AND OfficeId = :empty",
                "ExpressionAttributeValues": {
                    ":office_id": office.office_id,
                    ":empty": None
                },
            }
        }

        try:
            await to_thread(
                lambda: self.client.transact_write_items(
                    TransactItems=[put_office, update_floor],
                )
            )
        except self.table.meta.client.exceptions.TransactionCanceledException as e:
            print(e.response.get("CancellationReasons"))
            raise Exception("Office creation failed due to conflict") from e

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
                KeyConditionExpression=Key("PK").eq("OFFICE") & Key("SK").begins_with("DETAILS#"),
            ).get("Items", [])
        )

        return [Office(**cast(dict, o)) for o in offices]

    async def delete_office(self, building_id: str, floor_number: int, office_id: str):
        delete_office :TransactWriteItemTypeDef= {
            "Delete": {
                "TableName": TABLE,
                "Key": {
                    "PK": "OFFICE",
                    "SK": f"DETAILS#{office_id}",
                },
                "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
            }
        }

        clear_floor :TransactWriteItemTypeDef= {
            "Update": {
                "TableName": TABLE,
                "Key": {
                    "PK": f"BUILDING#{building_id}",
                    "SK": f"FLOORINFO#{floor_number}",
                },
                "UpdateExpression": "REMOVE OfficeId",
                "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK) AND OfficeId = :office_id",
                "ExpressionAttributeValues": {
                    ":office_id": office_id,
                },
            }
        }

        await to_thread(
            lambda: self.client.transact_write_items(
                TransactItems=[delete_office, clear_floor]
            )
        )