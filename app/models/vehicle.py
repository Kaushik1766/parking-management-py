from pydantic import BaseModel, Field, field_validator
from enum import Enum


class VehicleType(str, Enum):
    TWO_WHEELER = "TwoWheeler"
    FOUR_WHEELER = "FourWheeler"


class AssignedSlot(BaseModel):
    building_id: str = Field(alias="BuildingId")
    floor_number: int = Field(alias="FloorNumber")
    slot_id: int = Field(alias="SlotId")


class Vehicle(BaseModel):
    vehicle_id: str = Field(alias="VehicleId")
    number_plate: str = Field(alias="Numberplate")
    vehicle_type: VehicleType = Field(alias="VehicleType")
    is_parked: bool = Field(alias="IsParked")
    assigned_slot: AssignedSlot | None = Field(default=None, alias="AssignedSlot")