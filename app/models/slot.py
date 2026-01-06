from enum import Enum
from pydantic.fields import Field
from pydantic import BaseModel

class SlotType(str, Enum):
    TWO_WHEELER = "TwoWheeler"
    FOUR_WHEELER = "FourWheeler"

class OccupantDetails(BaseModel):
    username: str = Field(alias='Username')
    number_plate: str = Field(alias='NumberPlate')
    email: str = Field(alias='Email')
    start_time: int = Field(alias='StartTime')

class Slot(BaseModel):
    slot_id: int = Field(alias='SlotId')
    slot_type: SlotType = Field(alias='SlotType')
    is_assigned: bool = Field(alias='IsAssigned')
    is_occupied: bool = Field(alias='IsOccupied')
    occupied_by: OccupantDetails | None = Field(default=None,alias='OccupiedBy')