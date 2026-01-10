from typing import cast
from app.models import slot
from app.models.floor import Floor
from app.models.slot import Slot
from boto3.dynamodb.conditions import Key
from app.constants import TABLE
from app.repository.slot_repo import SlotRepository
from app.repository.user_repo import UserRepository
from app.repository.floor_repo import FloorRepository
from app.repository.office_repo import OfficeRepository
import asyncio
from uuid import uuid4
from app.models.building import Building
from app.models.office import Office
from app.repository.building_repo import BuildingRepository
import boto3



async def main():
    db = boto3.resource('dynamodb')
    
    slot_repo = SlotRepository(db)

    slots = await slot_repo.get_slots_by_floor(floor=Floor(
            building_id="b32fb06e-5169-43bb-bcbe-5047b022eedd",
            FloorNumber=1,
        )
    )
    for s in slots:
        print(s)


asyncio.run(main())
