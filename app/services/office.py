import uuid
from typing import Annotated

from fastapi import Depends
from starlette import status

from app.dto.office import OfficeResponseDTO, AddOfficeRequestDTO
from app.errors.web_exception import WebException, DB_ERROR
from app.models.office import Office
from app.repository.building_repo import BuildingRepository
from app.repository.office_repo import OfficeRepository
from app.repository.floor_repo import FloorRepository


class OfficeService:
    def __init__(
            self,
            office_repo: Annotated[OfficeRepository, Depends(OfficeRepository)],
            building_repo: Annotated[BuildingRepository, Depends(BuildingRepository)],
            floor_repo: Annotated[FloorRepository, Depends(FloorRepository)],
    ):
        self.office_repo = office_repo
        self.building_repo = building_repo
        self.floor_repo = floor_repo

    async def get_offices(self) -> list[OfficeResponseDTO]:
        offices = await self.office_repo.get_offices()

        return [
            OfficeResponseDTO(
                building_id=o.building_id,
                floor_number=o.floor_number,
                office_name=o.office_name,
                office_id=o.office_id,
            )
            for o in offices
        ]

    async def add_office(self, building_id: str, req: AddOfficeRequestDTO):
        # ensure building and floor exist
        await self.building_repo.get_building_by_id(building_id)
        floors = await self.floor_repo.get_floors(building_id)
        if not any(f.floor_number == req.floor_number for f in floors):
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="Floor not found", error_code=DB_ERROR)

        office = Office(
            OfficeName=req.office_name,
            BuildingId=building_id,
            FloorNumber=req.floor_number,
            OfficeId=str(uuid.uuid4()),
        )

        await self.office_repo.add_office(office)

        return office.office_id

    async def delete_office(self, building_id: str, office_id: str):
        # lookup office to validate and get floor
        office = await self.office_repo.get_office_by_id(office_id)
        if office.building_id != building_id:
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="Office not found", error_code=DB_ERROR)

        await self.office_repo.delete_office(building_id=building_id, floor_number=office.floor_number, office_id=office_id)
