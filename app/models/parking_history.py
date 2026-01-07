# "Numberplate": "UP32KK2222",
# "BuildingId": "BUILDING#B1",
# "FloorNumber": 1,
# "SlotId": 2,
# "StartTime": 1763572066,
# "EndTime": 1763572066
from pydantic.fields import Field
from pydantic import BaseModel


class ParkingHistory(BaseModel):
    numberplate: str = Field(alias="NumberPlate")
    building_id: str = Field(alias="BuildingId")
    floor_number: int = Field(alias="FloorNumber")
    slot_id: int = Field(alias="SlotId")
    start_time: int = Field(alias="StartTime")
    end_time: int = Field(alias="EndTime")