from pydantic import BaseModel, Field


class Building(BaseModel):
    id: str = Field(alias="BuildingId")
    name: str = Field(alias="BuildingName")
    total_floors: int = Field(default=0, alias="TotalFloors")
    available_slots: int = Field(default=0, alias="AvailableSlots")
    total_slots: int = Field(default=0, alias="TotalSlots")