from typing import Annotated
from app.dto.vehicle import AddVehicleDTO
from fastapi import APIRouter, Depends

from app.dto.login import UserJWT
from app.services.vehicle import VehicleService
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def get_vehicles(
        vehicle_service: Annotated[VehicleService, Depends(VehicleService)],
        current_user: Annotated[UserJWT, Depends(get_current_user)]):
    vehicles = await vehicle_service.get_vehicles_by_user(current_user.id)
    return vehicles

@router.post("/")
async def add_vehicle(
        vehicle: AddVehicleDTO,
        current_user: Annotated[UserJWT, Depends(get_current_user)],
        vehicle_service: Annotated[VehicleService, Depends(VehicleService)] ):
    pass