from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _ts_to_iso(ts: int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


class ParkRequestDTO(BaseModel):
    numberplate: str


class ParkingHistoryResponseDTO(BaseModel):
    ticket_id: str = Field(alias="ticketId")
    number_plate: str = Field(alias="numberPlate")
    building_id: str = Field(alias="buildingId")
    building_name: str = Field(alias="buildingName")
    floor_number: int = Field(alias="floorNumber")
    slot_number: int = Field(alias="slotNumber")
    start_time: str = Field(alias="startTime")
    end_time: str | None = Field(alias="endTime")
    vehicle_type: str = Field(alias="vehicleType")

    @classmethod
    def from_model(cls, *, ticket_id: str, number_plate: str, building_id: str, building_name: str, floor_number: int, slot_number: int, start_time: int, end_time: int | None, vehicle_type: str):
        return cls(
            ticketId=ticket_id,
            numberPlate=number_plate,
            buildingId=building_id,
            buildingName=building_name,
            floorNumber=floor_number,
            slotNumber=slot_number,
            startTime=_ts_to_iso(start_time),
            endTime=_ts_to_iso(end_time),
            vehicleType=vehicle_type,
        )
