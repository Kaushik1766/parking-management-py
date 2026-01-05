from pydantic import BaseModel, Field


class Building(BaseModel):
    id: str = Field(alias="BuildingId")
    name: str = Field(alias="BuildingName")
    total_floors: int = Field(alias="TotalFloors")
    available_slots: int = Field(alias="AvailableSlots")