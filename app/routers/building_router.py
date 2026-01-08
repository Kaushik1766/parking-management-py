from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from app.dependencies import get_user
from app.dto.building import AddBuildingRequestDTO, AddFloorRequestDTO
from app.dto.login import UserJWT
from app.models.roles import Roles
from app.services.building import BuildingService

router = APIRouter()


@router.post("/")
async def add_building(
        req: AddBuildingRequestDTO,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.ADMIN]))],
        building_service: Annotated[BuildingService, Depends(BuildingService)],
):
    await building_service.add_building(req)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Building added successfully"},
    )


@router.post("/{building_id}/floors")
async def add_floor(
        building_id: str,
        req: AddFloorRequestDTO,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.ADMIN]))],
        building_service: Annotated[BuildingService, Depends(BuildingService)],
):
    await building_service.add_floor(building_id=building_id, req=req)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Floor added successfully"},
    )
