from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_user
from app.dto.login import UserJWT
from app.models.roles import Roles
from app.services.office import OfficeService

router = APIRouter()


@router.get("/")
async def get_offices(
        office_service: Annotated[OfficeService, Depends(OfficeService)],
):
    return await office_service.get_offices()
