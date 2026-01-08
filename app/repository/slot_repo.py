from typing import cast
from boto3.dynamodb.conditions import Key
from asyncio.threads import to_thread

from app.models.building import Building
from app.models.floor import Floor
from app.models.slot import Slot, OccupantDetails
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from typing import Annotated

from fastapi import Depends

from app.constants import TABLE
from app.dependencies import get_db


class SlotRepository:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)

    async def get_slots_by_floor(self, floor: Floor)-> list[Slot]:
        slot_query_items = await to_thread(
            lambda : self.table.query(
                KeyConditionExpression=Key("PK").eq(f"BUILDING#{floor.building_id}")&Key("SK").begins_with(f"FLOOR#{floor.floor_number}#SLOT#"),
            ).get("Items")
        )

        return [
            Slot(
                building_id=floor.building_id,
                floor_number=floor.floor_number,
                **cast(dict,s)
            )
            for s in slot_query_items
        ]

    async def get_free_slots_by_floor(self, floor: Floor)-> list[Slot]:
        slots = await self.get_slots_by_floor(floor)

        return [s for s in slots if not s.is_assigned]


    async def update_slot(self, slot: Slot):
        await to_thread(
            lambda : self.table.update_item(
                Key={
                    "PK": f"BUILDING#{slot.building_id}",
                    "SK": f"FLOOR#{slot.floor_number}#SLOT#{slot.slot_id}",
                },
                UpdateExpression="SET occupied_by = :occupied_by",
                ExpressionAttributeValues={
                    ":occupied_by": slot.occupied_by.model_dump(by_alias=True) if slot.occupied_by else None,
                },
            )
        )

    async def update_slot_occupancy(self, building_id: str, floor_number: int, slot_id: int, occupied_by: OccupantDetails | None, is_occupied: bool):
        await to_thread(
            lambda: self.table.update_item(
                Key={
                    "PK": f"BUILDING#{building_id}",
                    "SK": f"FLOOR#{floor_number}#SLOT#{slot_id}",
                },
                UpdateExpression="SET OccupiedBy = :occupied_by, IsOccupied = :is_occupied",
                ExpressionAttributeValues={
                    ":occupied_by": occupied_by.model_dump(by_alias=True) if occupied_by else None,
                    ":is_occupied": is_occupied,
                },
            )
        )