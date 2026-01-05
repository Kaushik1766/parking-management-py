from fastapi import APIRouter, Depends

from app.services.vehicle import VehicleService

router = APIRouter()

@router.get("/")
async def get_vehicles(vehicle_service: VehicleService = Depends(VehicleService)):
    # vehicles = await vehicle_service.get_vehicles_by_user()
    pass