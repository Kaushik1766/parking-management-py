from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.office import OfficeService

router = APIRouter()


@router.get("/")
async def get_all_offices(
        office_service: Annotated[OfficeService, Depends(OfficeService)],
):
    return await office_service.get_offices()
