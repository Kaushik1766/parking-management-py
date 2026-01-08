from pydantic.fields import Field
from pydantic import BaseModel
import datetime


class ParkingHistory(BaseModel):
    user_id: str = Field(exclude=True)
    numberplate: str = Field(alias="NumberPlate")
    building_id: str = Field(alias="BuildingId")
    floor_number: int = Field(alias="FloorNumber")
    slot_id: int = Field(alias="SlotId")
    start_time: int = Field( default=datetime.datetime.now(tz=datetime.timezone.utc), alias="StartTime")
    end_time: int = Field(alias="EndTime")
    parking_id: str = Field(alias="ParkingId")