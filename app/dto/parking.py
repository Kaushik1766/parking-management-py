from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _ts_to_iso(ts: int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


class ParkRequestDTO(BaseModel):
    numberplate: str


class ParkingHistoryResponseDTO(BaseModel):
    ticket_id: str = Field(alias="TicketId")
    number_plate: str = Field(alias="NumberPlate")
    building_id: str = Field(alias="BuildingId")
    building_name: str = Field(alias="BuildingName")
    floor_number: int = Field(alias="FloorNumber")
    slot_number: int = Field(alias="SlotNumber")
    start_time: str = Field(alias="StartTime")
    end_time: str | None = Field(alias="EndTime")
    vehicle_type: str = Field(alias="VehicleType")

    @classmethod
    def from_model(cls, *, ticket_id: str, number_plate: str, building_id: str, building_name: str, floor_number: int, slot_number: int, start_time: int, end_time: int | None, vehicle_type: str):
        return cls(
            TicketId=ticket_id,
            NumberPlate=number_plate,
            BuildingId=building_id,
            BuildingName=building_name,
            FloorNumber=floor_number,
            SlotNumber=slot_number,
            StartTime=_ts_to_iso(start_time),
            EndTime=_ts_to_iso(end_time),
            VehicleType=vehicle_type,
        )
