from pydantic import BaseModel, Field


class AddBuildingRequestDTO(BaseModel):
    building_name: str = Field(alias="buildingName")


class AddFloorRequestDTO(BaseModel):
    floor_number: int = Field(alias="floor_number")
