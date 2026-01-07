from app.models.vehicle import AssignedSlot, VehicleType
from uuid import uuid4
from app.errors.web_exception import CONFLICT_ERROR
from app.errors.web_exception import WebException
from app.models.floor import Floor
from app.dto.vehicle import AddVehicleRequestDTO
from typing import Self, Annotated
from starlette import status

from fastapi.params import Depends

from app.dto.vehicle import VehicleResponseDTO
from app.models.vehicle import Vehicle
from app.repository.building_repo import BuildingRepository
from app.repository.office_repo import OfficeRepository
from app.repository.slot_repo import SlotRepository
from app.repository.vehicle_repo import VehicleRepository


class VehicleService:
    def __init__(
            self,
            vehicle_repo: Annotated[VehicleRepository, Depends(VehicleRepository)],
            building_repo:Annotated[BuildingRepository, Depends(BuildingRepository)],
            office_repo: Annotated[OfficeRepository, Depends(OfficeRepository)],
            slot_repo: Annotated[SlotRepository, Depends(SlotRepository)],
        ):
        self.vehicle_repo = vehicle_repo
        self.building_repo = building_repo
        self.office_repo = office_repo
        self.slot_repo = slot_repo

    async def get_vehicles_by_user(self, user_id:str)->list[VehicleResponseDTO]:
        vehicles = await self.vehicle_repo.get_vehicles_by_user_id(user_id)

        vehicle_response: list[VehicleResponseDTO] = []
        for v in vehicles:
            if v.assigned_slot is None:
                vehicle_response.append(
                    VehicleResponseDTO(
                        number_plate=v.number_plate,
                        assigned_building_id="unassigned",
                        vehicle_type=v.vehicle_type,
                        is_parked=v.is_parked,
                        assigned_slot_number=0,
                        assigned_floor_number=0,
                        assigned_building_name= "unassigned"
                    )
                )
            else:
                building = await self.building_repo.get_building_by_id(v.assigned_slot.building_id)
                vehicle_response.append(
                    VehicleResponseDTO(
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

    async def add_vehicle(self, vehicle: AddVehicleRequestDTO, user_id:str, office_id:str):
        registered_vehicles = await self.vehicle_repo.get_vehicles_by_user_id(user_id)

        similar_vehicles = [v for v in registered_vehicles if v.vehicle_type==vehicle.vehicle_type]

        vehicle_model = Vehicle(
            VehicleId=str(uuid4()),
            Numberplate=vehicle.number_plate,
            VehicleType= VehicleType(vehicle.vehicle_type),
            IsParked=False,
        )
        if len(similar_vehicles) == 0:
            office = await self.office_repo.get_office_by_id(office_id)

            free_slots = await self.slot_repo.get_free_slots_by_floor(
                Floor(
                    building_id=office.building_id,
                    FloorNumber=office.floor_number,
                )
            )

            if len(free_slots) == 0:
                raise WebException(error_code=CONFLICT_ERROR, message="No free slots available, please contact the admin", status_code=status.HTTP_409_CONFLICT)

            slot = free_slots[0]
            vehicle_model.assigned_slot = AssignedSlot(
                FloorNumber=office.floor_number,
                BuildingId=office.building_id,
                SlotId= slot.slot_id,
            )

            slot.is_assigned = True

            await self.slot_repo.update_slot(slot)
        else:
            vehicle_model.assigned_slot = similar_vehicles[0].assigned_slot

        await self.vehicle_repo.save_vehicle(vehicle_model, user_id)