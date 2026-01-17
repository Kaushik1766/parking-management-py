from dns.rdtypes.util import priority_processing_order
from pydantic import ValidationError
import datetime
import uuid
from typing import Annotated

from fastapi import Depends

from starlette import  status
from app.dto.parking import ParkRequestDTO, ParkingHistoryResponseDTO
from app.errors.web_exception import WebException, DB_ERROR, CONFLICT_ERROR
from app.models.parking_history import ParkingHistory
from app.models.slot import OccupantDetails
from app.repository.building_repo import BuildingRepository
from app.repository.parking_repo import ParkingRepository
from app.repository.slot_repo import SlotRepository
from app.repository.vehicle_repo import VehicleRepository
from app.utils.singleton import singleton

class ParkingService:
    def __init__(
            self,
            parking_repo: Annotated[ParkingRepository, Depends(ParkingRepository)],
            vehicle_repo: Annotated[VehicleRepository, Depends(VehicleRepository)],
            building_repo: Annotated[BuildingRepository, Depends(BuildingRepository)],
            slot_repo: Annotated[SlotRepository, Depends(SlotRepository)],
    ):
        self.parking_repo = parking_repo
        self.vehicle_repo = vehicle_repo
        self.building_repo = building_repo
        self.slot_repo = slot_repo

    async def park(self, user_id: str, user_email: str, req: ParkRequestDTO) -> str:
        vehicle = await self.vehicle_repo.get_vehicle_by_number_plate(user_id, req.numberplate)
        if vehicle is None:
            raise WebException(status_code=status.HTTP_404_NOT_FOUND, message="Vehicle not found", error_code=DB_ERROR)

        if vehicle.assigned_slot is None:
            raise WebException(status_code=status.HTTP_409_CONFLICT, message="Vehicle is not assigned a slot", error_code=CONFLICT_ERROR)

        parking_id = str(uuid.uuid4())
        start_ts = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

        parking = ParkingHistory(
            ParkingId=parking_id,
            Numberplate=vehicle.number_plate,
            BuildingId=vehicle.assigned_slot.building_id,
            FloorNumber=vehicle.assigned_slot.floor_number,
            SlotId=vehicle.assigned_slot.slot_id,
            StartTime=start_ts,
            EndTime=None,
            user_id=user_id,
            VehicleType=vehicle.vehicle_type,
        )

        await self.parking_repo.add_parking(parking)

        return parking_id

    async def unpark(self, user_id: str, numberplate: str):
        # Update parking record end time
        try:
            await self.parking_repo.unpark_by_numberplate(user_id, numberplate)
        except ValidationError as e:
            print(e.errors())
            raise

        # Clear slot occupancy for assigned slot
        # vehicle = await self.vehicle_repo.get_vehicle_by_number_plate(user_id, numberplate)
        # if vehicle and vehicle.assigned_slot:
        #     await self.slot_repo.update_slot_occupancy(
        #         building_id=vehicle.assigned_slot.building_id,
        #         floor_number=vehicle.assigned_slot.floor_number,
        #         slot_id=vehicle.assigned_slot.slot_id,
        #         occupied_by=None,
        #         is_occupied=False,
        #     )

    async def get_parkings(self, user_id: str, start_time: int | None = None, end_time: int | None = None) -> list[ParkingHistoryResponseDTO]:
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

        records = await self.parking_repo.get_parking_history(user_id, start_time, end_time)

        responses: list[ParkingHistoryResponseDTO] = []
        for record in records:
            building = await self.building_repo.get_building_by_id(record.building_id)

            responses.append(
                ParkingHistoryResponseDTO.from_model(
                    ticket_id=record.parking_id,
                    number_plate=record.numberplate,
                    building_id=record.building_id,
                    building_name=building.name,
                    floor_number=record.floor_number,
                    slot_number=record.slot_id,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    vehicle_type=str(record.vehicle_type) if record.vehicle_type else "",
                )
            )
        responses.sort(key=lambda x: x.start_time, reverse=True)

        return responses
