from asyncio.threads import to_thread
from typing import Annotated, cast

from boto3.dynamodb.conditions import Key
from fastapi.params import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.constants import SLOT_LAYOUT
from app.constants import TABLE
from app.dependencies import get_db
from app.models.floor import Floor
from app.models.slot import Slot, SlotType

class FloorRepository:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)

    async def add_floor(self, building_id: str, floor_number: int) -> None:
        slot = Slot(
            building_id=building_id,
            floor_number=floor_number,
            SlotId=0,
            SlotType=SlotType.TWO_WHEELER,
            IsAssigned=False,
            IsOccupied=False,
        )
        with self.table.batch_writer() as batch:
            for idx, i in enumerate(SLOT_LAYOUT):
                slot.slot_id = idx+1
                slot.slot_type = SlotType.TWO_WHEELER if i=='0' else SlotType.FOUR_WHEELER
                batch.put_item(
                    Item={
                        **slot.model_dump(by_alias=True),
                        "PK": f"BUILDING#{building_id}",
                        "SK": f"FLOOR#{floor_number}#SLOT#{slot.slot_id}",
                    }
                )

        floor_info = Floor(
            building_id=building_id,
            FloorNumber=floor_number,
            TotalSlots=len(SLOT_LAYOUT),
            AvailableSlots=len(SLOT_LAYOUT),
        )

        self.table.put_item(
            Item={
                **floor_info.model_dump(by_alias=True),
                "PK": f"BUILDING#{building_id}",
                "SK": f"FLOORINFO#{floor_info.floor_number}",
            },
            ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)",
        )

        self.table.meta.client.update_item(
            TableName=TABLE,
            Key={
                "PK": f"BUILDING",
                "SK": f"BUILDING#{building_id}",
            },
            UpdateExpression="SET TotalFloors = TotalFloors + :inc, TotalSlots = TotalSlots + :slots, AvailableSlots = AvailableSlots + :avail",
            ExpressionAttributeValues={
                ":inc": len(SLOT_LAYOUT),
                ":slots": len(SLOT_LAYOUT),
                ":avail": len(SLOT_LAYOUT),
            }
        )

    async def get_floors(self, building_id: str) -> list[Floor]:
        floors = await to_thread(
            lambda: self.table.query(
                KeyConditionExpression=Key("PK").eq(f"BUILDING#{building_id}") & Key("SK").begins_with("FLOORINFO#"),
            ).get("Items", [])
        )

        return [
            Floor(
                building_id=building_id,
                **cast(dict, floor),
            )
            for floor in floors
        ]