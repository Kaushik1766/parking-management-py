from typing import Annotated

from starlette import status
from starlette.responses import JSONResponse

from app.dto.vehicle import AddVehicleRequestDTO
from fastapi import APIRouter, Depends

from app.dto.login import UserJWT
from app.models.roles import Roles
from app.services.vehicle import VehicleService
from app.dependencies import get_user

router = APIRouter()

@router.get("/")
async def get_vehicles(
        vehicle_service: Annotated[VehicleService, Depends(VehicleService)],
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))]):
    vehicles = await vehicle_service.get_vehicles_by_user(current_user.id)
    return vehicles

@router.post("/")
async def add_vehicle(
        vehicle: AddVehicleRequestDTO,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))],
        vehicle_service: Annotated[VehicleService, Depends(VehicleService)] ):
    await vehicle_service.add_vehicle(
        vehicle=vehicle,
        office_id=current_user.officeId,
        user_id=current_user.id
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Vehicle added successfully",
        }
    )

@router.delete("/{numberplate}")
async def delete_vehicle(
        numberplate: str,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))],
        vehicle_service: Annotated[VehicleService, Depends(VehicleService)]):
    await vehicle_service.delete_vehicle(number_plate=numberplate, user_id=current_user.id)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Vehicle deleted successfully",
        }
    )

