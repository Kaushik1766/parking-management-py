from typing import Annotated, Dict

from fastapi import Depends
from starlette import status

from app.dto.billing import BillParkingHistoryDTO, BillResponseDTO
from app.errors.web_exception import DB_ERROR, WebException
from app.models.bill import Bill
from app.repository.billing_repo import BillingRepository
from app.repository.building_repo import BuildingRepository
from app.utils.singleton import singleton


@singleton
class BillingService:
    def __init__(
        self,
        billing_repo: Annotated[BillingRepository, Depends(BillingRepository)],
        building_repo: Annotated[BuildingRepository, Depends(BuildingRepository)],
    ):
        self.billing_repo = billing_repo
        self.building_repo = building_repo

    async def _get_building_name(self, building_id: str, cache: Dict[str, str]) -> str:
        if building_id in cache:
            return cache[building_id]
        building = await self.building_repo.get_building_by_id(building_id)
        cache[building_id] = building.name
        return building.name

    async def _bill_to_response(self, *, bill: Bill, user_email: str) -> BillResponseDTO:
        cache: Dict[str, str] = {}
        history: list[BillParkingHistoryDTO] = []
        for item in bill.parking_history:
            building_name = await self._get_building_name(item.building_id, cache)
            history.append(
                BillParkingHistoryDTO.from_raw(
                    ticket_id=item.ticket_id,
                    number_plate=item.number_plate,
                    building_id=item.building_id,
                    building_name=building_name,
                    floor_number=item.floor_number,
                    slot_number=item.slot_number,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    vehicle_type=item.vehicle_type,
                )
            )

        return BillResponseDTO(
            parking_history=history,
            total_amount=bill.total_amount,
            bill_date=bill.bill_date,
            user_email=user_email,
            user_id=bill.user_id,
            billing_month=bill.billing_month,
            billing_year=bill.billing_year,
        )

    async def get_bill(self, user_id: str, user_email: str, month: int, year: int) -> BillResponseDTO:
        bill = await self.billing_repo.get_bill(user_id, month, year)
        if bill is None:
            raise WebException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Bill not generated for this month",
                error_code=DB_ERROR,
            )

        return await self._bill_to_response(bill=bill, user_email=user_email)
