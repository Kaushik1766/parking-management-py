from pydantic import BaseModel, Field


class OfficeResponseDTO(BaseModel):
    building_id: str = Field(alias="building_id")
    floor_number: int = Field(alias="floor_number")
    office_name: str = Field(alias="office_name")
    office_id: str = Field(alias="office_id")
