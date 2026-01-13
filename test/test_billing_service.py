import asyncio
import unittest
from unittest.mock import AsyncMock

from app.errors.web_exception import DB_ERROR, WebException
from app.models.bill import Bill, BillingParkingHistory
from app.models.building import Building
from app.repository.billing_repo import BillingRepository
from app.repository.building_repo import BuildingRepository
from app.services.billing import BillingService


class TestBillingService(unittest.TestCase):
    def setUp(self):
        self.billing_repo = AsyncMock(BillingRepository)
        self.building_repo = AsyncMock(BuildingRepository)
        self.service = BillingService(billing_repo=self.billing_repo, building_repo=self.building_repo)
        self.service.billing_repo = self.billing_repo
        self.service.building_repo = self.building_repo

    def test_get_bill_returns_response(self):
        history = [
            BillingParkingHistory(
                TicketId="t1",
                NumberPlate="ABC123",
                BuildingId="b1",
                BuildingName="HQ",
                FloorNumber=1,
                SlotNumber=2,
                VehicleType="TwoWheeler",
                StartTime=1,
                EndTime=2,
            ),
            BillingParkingHistory(
                TicketId="t2",
                NumberPlate="XYZ999",
                BuildingId="b1",
                BuildingName="HQ",
                FloorNumber=1,
                SlotNumber=3,
                VehicleType="FourWheeler",
                StartTime=3,
                EndTime=4,
            ),
        ]
        bill = Bill(
            user_id="user_1",
            BillingMonth=1,
            BillingYear=2025,
            TotalAmount=150.0,
            BillDate="2025-02-01",
            ParkingHistory=history,
        )
        self.billing_repo.get_bill.return_value = bill
        self.building_repo.get_building_by_id.return_value = Building(
            BuildingId="b1", BuildingName="HQ", TotalFloors=2, TotalSlots=10, AvailableSlots=5
        )

        response = asyncio.run(self.service.get_bill("user_1", "user@example.com", 1, 2025))

        self.billing_repo.get_bill.assert_awaited_once_with("user_1", 1, 2025)
        self.building_repo.get_building_by_id.assert_awaited_once_with("b1")
        self.assertEqual(len(response.parking_history), 2)
        self.assertEqual(response.parking_history[0].building_name, "HQ")
        self.assertEqual(response.user_email, "user@example.com")
        self.assertEqual(response.total_amount, 150.0)

    def test_get_bill_raises_when_missing(self):
        self.billing_repo.get_bill.return_value = None

        with self.assertRaises(WebException) as ctx:
            asyncio.run(self.service.get_bill("user_1", "user@example.com", 1, 2025))

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.error_code, DB_ERROR)
        self.assertEqual(ctx.exception.message, "Bill not generated for this month")
