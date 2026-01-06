from pydantic.fields import Field
from pydantic import BaseModel


class Floor(BaseModel):
    floor_number: int = Field(alias="FloorNumber")
    total_slots: int = Field(alias="TotalSlots")
    available_slots: int = Field(alias="AvailableSlots")
    office_id: str|None = Field(default=None, alias="OfficeId")