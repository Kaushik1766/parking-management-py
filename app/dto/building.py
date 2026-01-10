from pydantic import BaseModel, Field


class AddBuildingRequestDTO(BaseModel):
    building_name: str = Field(alias="buildingName")


class AddFloorRequestDTO(BaseModel):
    floor_number: int = Field(alias="floor_number")


class BuildingResponseDTO(BaseModel):
    building_id: str = Field(alias="buildingId")
    name: str
    available_slots: int = Field(alias="availableSlots")
    total_slots: int = Field(alias="totalSlots")
    total_floors: int = Field(alias="totalFloors")


class FloorResponseDTO(BaseModel):
    building_id: str = Field(alias="buildingId")
    floor_number: int = Field(alias="floorNumber")
    total_slots: int = Field(alias="totalSlots")
    available_slots: int = Field(alias="availableSlots")
    assigned_office: str | None = Field(alias="assignedOffice")

class ParkingStatusResponseDTO(BaseModel):
    number_plate: str = Field(alias="numberPlate")
    parked_at: str = Field(alias="parkedAt")
    user_name: str = Field(alias="userName")
    user_email: str = Field(alias="userEmail")


class SlotResponseDTO(BaseModel):
    building_id: str = Field(alias="buildingId")
    floor_number: int = Field(alias="floorNumber")
    slot_number: int = Field(alias="slotNumber")
    slot_type: str = Field(alias="slotType")
    is_assigned: bool = Field(alias="isAssigned")
    parking_status: ParkingStatusResponseDTO | None = Field(default=None, alias="parkingStatus")
