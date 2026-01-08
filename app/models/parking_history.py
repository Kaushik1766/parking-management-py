import datetime
from pydantic.fields import Field
from pydantic import BaseModel


def _now_ts() -> int:
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())


class ParkingHistory(BaseModel):
    user_id: str = Field(exclude=True)
    numberplate: str = Field(alias="Numberplate")
    building_id: str = Field(alias="BuildingId")
    floor_number: int = Field(alias="FloorNumber")
    slot_id: int = Field(alias="SlotId")
    start_time: int = Field(default_factory=_now_ts, alias="StartTime")
    end_time: int | None = Field(default=None, alias="EndTime")
    parking_id: str = Field(alias="ParkingId")
    vehicle_type: str | None = Field(default=None, alias="VehicleType")