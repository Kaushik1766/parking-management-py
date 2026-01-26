import asyncio
import unittest
from unittest.mock import AsyncMock

from app.constants import BILL_NOT_GENERATED_MESSAGE
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

    def test_get_bill(self):
        cases = {
            "bill_generated": {
                "bill_repo_setup": lambda: setattr(
                    self.billing_repo.get_bill,
                    "return_value",
                    Bill(
                        user_id="user_1",
                        BillingMonth=1,
                        BillingYear=2024,
                        TotalAmount=100.0,
                        BillDate="2024-02-01",
                        ParkingHistory=[],
                    ),
                ),
                "expected_exception": None,
            },
            "bill_with_parking_history": {
                "bill_repo_setup": lambda: setattr(
                    self.billing_repo.get_bill,
                    "return_value",
                    Bill(
                        user_id="user_1",
                        BillingMonth=1,
                        BillingYear=2024,
                        TotalAmount=150.0,
                        BillDate="2024-02-01",
                        ParkingHistory=[
                            BillingParkingHistory(
                                TicketId="ticket_1",
                                NumberPlate="ABC123",
                                BuildingId="b1",
                                BuildingName="HQ Tower",
                                FloorNumber=1,
                                SlotNumber=5,
                                StartTime=1640000000,
                                EndTime=1640010000,
                                VehicleType="FOUR_WHEELER",
                            )
                        ],
                    ),
                ),
                "building_repo_setup": lambda: setattr(
                    self.building_repo.get_building_by_id,
                    "return_value",
                    Building(
                        BuildingId="b1",
                        BuildingName="HQ Tower",
                        TotalFloors=5,
                        AvailableSlots=100,
                    ),
                ),
                "expected_exception": None,
            },
            "bill_not_generated": {
                "bill_repo_setup": lambda: setattr(
                    self.billing_repo.get_bill,
                    "return_value",
                    None,
                ),
                "expected_exception": WebException,
            },
        }
        
        for case_name, case in cases.items():
            with self.subTest(case=case_name):
                case["bill_repo_setup"]()
                if case.get("building_repo_setup"):
                    case["building_repo_setup"]()
                
                if case.get('expected_exception'):
                    with self.assertRaises(WebException) as ctx:
                        asyncio.run(self.service.get_bill("user_1", "user@example.com", 1, 2025))
                else:
                    response = asyncio.run(self.service.get_bill("user_1", "user@example.com", 1, 2025))
                    self.assertIsNotNone(response)
