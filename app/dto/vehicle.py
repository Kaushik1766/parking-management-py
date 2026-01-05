from pydantic import BaseModel


class VehicleDTO(BaseModel):
    number_plate: str
    vehicle_type: str
    is_parked: bool
    assigned_building_name: str
    assigned_building_id: str
    assigned_floor_number: int
    assigned_slot_number: int