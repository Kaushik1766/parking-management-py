from uuid import uuid4
from typing import Annotated

from fastapi import Depends
from starlette import status

from app.dto.building import AddBuildingRequestDTO, AddFloorRequestDTO
from app.errors.web_exception import WebException, DB_ERROR
from app.models.building import Building
from app.repository.building_repo import BuildingRepository
from app.repository.floor_repo import FloorRepository


class BuildingService:
    def __init__(
            self,
            building_repo: Annotated[BuildingRepository, Depends(BuildingRepository)],
            floor_repo: Annotated[FloorRepository, Depends(FloorRepository)],
    ):
        self.building_repo = building_repo
        self.floor_repo = floor_repo

    async def add_building(self, req: AddBuildingRequestDTO):
        building = Building(
            BuildingId=str(uuid4()),
            BuildingName=req.building_name,
            TotalFloors=0,
            AvailableSlots=0,
        )

        await self.building_repo.add_building(building)

    async def add_floor(self, building_id: str, req: AddFloorRequestDTO):
        await self.building_repo.get_building_by_id(building_id)

        await self.floor_repo.add_floor(building_id=building_id, floor_number=req.floor_number)
