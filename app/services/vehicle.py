from typing import Self

from fastapi.params import Depends

from app.dto.vehicle import VehicleDTO
from app.models.vehicle import Vehicle
from app.repository.building_repo import BuildingRepository
from app.repository.vehicle_repo import VehicleRepository


class VehicleService:
    def __init__(self, vehicle_repo: VehicleRepository = Depends(VehicleRepository), building_repo:BuildingRepository = Depends(BuildingRepository)):
        self.vehicle_repo = vehicle_repo
        self.building_repo = building_repo

    async def get_vehicles_by_user(self, user_id:str)->list[VehicleDTO]:
        vehicles = await self.vehicle_repo.get_vehicles_by_user_id(user_id)

        vehicle_response: list[VehicleDTO] = []
        for v in vehicles:
            building = await self.building_repo.get_building_by_id(v.assigned_slot.building_id)
            vehicle_response.append(
                VehicleDTO(
                    number_plate=v.number_plate,
                    assigned_building_id=v.assigned_slot.building_id,
                    vehicle_type=v.vehicle_type,
                    is_parked=v.is_parked,
                    assigned_slot_number=v.assigned_slot.slot_id,
                    assigned_floor_number=v.assigned_slot.floor_number,
                    assigned_building_name= building.name
                )
            )
        return vehicle_response