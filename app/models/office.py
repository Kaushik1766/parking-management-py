from pydantic import Field
from pydantic.main import BaseModel

class Office(BaseModel):
    office_name: str = Field(alias="OfficeName")
    building_id: str = Field(alias="BuildingId")
    floor_number: int = Field(alias="FloorNumber")
    office_id: str = Field(alias="OfficeId")