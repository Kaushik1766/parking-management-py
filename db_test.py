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
    building_repo = BuildingRepository(db)
    # await building_repo.add_building(Building(
    #     BuildingId=str(uuid4()),
    #     BuildingName="AdminOffice"
    # ))
    # await OfficeRepository(db).add_office(Office(BuildingId="61fb1c4a-6a24-42ea-ba43-cbc2f1126f1b", FloorNumber=2, OfficeId=str(uuid4()), OfficeName="MainOffice"))


asyncio.run(main())
