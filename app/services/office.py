from typing import Annotated

from fastapi import Depends

from app.dto.office import OfficeResponseDTO
from app.repository.office_repo import OfficeRepository


class OfficeService:
    def __init__(self, office_repo: Annotated[OfficeRepository, Depends(OfficeRepository)]):
        self.office_repo = office_repo

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
