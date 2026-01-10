import datetime
from uuid import uuid4
from typing import Annotated

from fastapi import Depends
from starlette import status
from app.models.floor import Floor
from app.repository.slot_repo import SlotRepository

from app.dto.building import (
    AddBuildingRequestDTO,
    AddFloorRequestDTO,
    BuildingResponseDTO,
    FloorResponseDTO,
    ParkingStatusResponseDTO,
    SlotResponseDTO,
)
from app.errors.web_exception import WebException, DB_ERROR
from app.models.building import Building
from app.repository.building_repo import BuildingRepository
from app.repository.floor_repo import FloorRepository
from app.repository.office_repo import OfficeRepository

from app.utils.singleton import singleton

@singleton
class BuildingService:
    def __init__(
            self,
            building_repo: Annotated[BuildingRepository, Depends(BuildingRepository)],
            floor_repo: Annotated[FloorRepository, Depends(FloorRepository)],
            office_repo: Annotated[OfficeRepository, Depends(OfficeRepository)],
            slot_repo: Annotated[SlotRepository, Depends(SlotRepository)],
    ):
        self.building_repo = building_repo
        self.floor_repo = floor_repo
        self.office_repo = office_repo
        self.slot_repo = slot_repo

    async def add_building(self, req: AddBuildingRequestDTO):
        building = Building(
            BuildingId=str(uuid4()),
            BuildingName=req.building_name,
            TotalFloors=0,
            AvailableSlots=0,
        )

        await self.building_repo.add_building(building)

    async def add_floor(self, building_id: str, req: AddFloorRequestDTO):
        await self.building_repo.get_building_by_id(building_id)

        await self.floor_repo.add_floor(building_id=building_id, floor_number=req.floor_number)

    async def get_buildings(self) -> list[BuildingResponseDTO]:
        buildings = await self.building_repo.get_buildings()

        return [
            BuildingResponseDTO(
                buildingId=b.id,
                name=b.name,
                availableSlots=b.available_slots,
                totalSlots=b.total_slots,
                totalFloors=b.total_floors,
            )
            for b in buildings
        ]

    async def get_floors(self, building_id: str) -> list[FloorResponseDTO]:
        await self.building_repo.get_building_by_id(building_id)

        floors = await self.floor_repo.get_floors(building_id)
        floor_responses: list[FloorResponseDTO] = []

        for floor in floors:
            assigned_office = None
            if floor.office_id:
                office = await self.office_repo.get_office_by_id(floor.office_id)
                assigned_office = office.office_name

            floor_responses.append(
                FloorResponseDTO(
                    buildingId=building_id,
                    floorNumber=floor.floor_number,
                    totalSlots=floor.total_slots,
                    availableSlots=floor.available_slots,
                    assignedOffice=assigned_office,
                )
            )

        return floor_responses

    async def get_slots(self, building_id: str, floor_number: int) -> list[SlotResponseDTO]:
        await self.building_repo.get_building_by_id(building_id)

        floors = await self.floor_repo.get_floors(building_id)
        if not any(f.floor_number == floor_number for f in floors):
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="Floor not found", error_code=DB_ERROR)

        slots = await self.slot_repo.get_slots_by_floor(
            Floor(building_id=building_id, FloorNumber=floor_number)
        )

        slot_responses: list[SlotResponseDTO] = []

        for slot in slots:
            parking_status = None
            if slot.occupied_by is not None:
                parked_at_iso = (
                    datetime.datetime.fromtimestamp(slot.occupied_by.start_time, tz=datetime.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                parking_status = ParkingStatusResponseDTO(
                    numberPlate=slot.occupied_by.number_plate,
                    parkedAt=parked_at_iso,
                    userName=slot.occupied_by.username,
                    userEmail=slot.occupied_by.email,
                )

            slot_responses.append(
                SlotResponseDTO(
                    buildingId=building_id,
                    floorNumber=floor_number,
                    slotNumber=slot.slot_id,
                    slotType=slot.slot_type.value,
                    isAssigned=slot.is_assigned,
                    parkingStatus=parking_status,
                )
            )

        return slot_responses
