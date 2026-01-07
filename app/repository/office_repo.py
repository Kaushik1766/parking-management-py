from typing import cast
from asyncio.threads import to_thread
from app.models.office import Office
from app.models.slot import Slot, SlotType
from app.models.floor import Floor
from app.constants import SLOT_LAYOUT
from app.constants import TABLE
import boto3
from app.dependencies import get_db
from fastapi.params import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from typing import Annotated

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