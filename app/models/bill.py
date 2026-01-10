from pydantic import BaseModel, Field
from typing import List


class BillingParkingHistory(BaseModel):
    ticket_id: str = Field(alias="TicketId")
    number_plate: str = Field(alias="NumberPlate")
    building_id: str = Field(alias="BuildingId")
    building_name: str = Field(alias="BuildingName")
    floor_number: int = Field(alias="FloorNumber")
    slot_number: int = Field(alias="SlotNumber")
    vehicle_type: str = Field(alias="VehicleType")
    start_time: int = Field(alias="StartTime")
    end_time: int = Field(alias="EndTime")


class Bill(BaseModel):
    user_id: str = Field(exclude=True)
    billing_month: int = Field(alias="BillingMonth")
    billing_year: int = Field(alias="BillingYear")
    total_amount: float = Field(alias="TotalAmount")
    bill_date: str = Field(alias="BillDate")
    parking_history: List[BillingParkingHistory] = Field(default_factory=list, alias="ParkingHistory")
