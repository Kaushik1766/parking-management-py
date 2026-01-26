import unittest
from datetime import datetime, timezone

from app.dto.billing import BillParkingHistoryDTO, BillResponseDTO, _ts_to_iso


class TestBillingDTO(unittest.TestCase):
    def test_ts_to_iso_with_timestamp(self):
        """Test _ts_to_iso converts timestamp to ISO format"""
        timestamp = 1640000000
        result = _ts_to_iso(timestamp)
        # Verify it's a valid ISO string with Z suffix
        self.assertTrue(result.endswith("Z"))
        self.assertIn("2021-12-20", result)

    def test_ts_to_iso_with_none(self):
        """Test _ts_to_iso returns None for None input"""
        result = _ts_to_iso(None)
        self.assertIsNone(result)

    def test_bill_parking_history_dto_from_raw_with_end_time(self):
        """Test BillParkingHistoryDTO.from_raw with end_time"""
        dto = BillParkingHistoryDTO.from_raw(
            ticket_id="T123",
            number_plate="ABC123",
            building_id="B1",
            building_name="HQ",
            floor_number=1,
            slot_number=5,
            start_time=1640000000,
            end_time=1640010000,
            vehicle_type="FOUR_WHEELER",
        )

        self.assertEqual(dto.ticket_id, "T123")
        self.assertEqual(dto.number_plate, "ABC123")
        self.assertEqual(dto.building_id, "B1")
        self.assertEqual(dto.building_name, "HQ")
        self.assertEqual(dto.floor_number, 1)
        self.assertEqual(dto.slot_number, 5)
        self.assertTrue(dto.start_time.endswith("Z"))
        self.assertIn("2021-12-20", dto.start_time)
        self.assertTrue(dto.end_time.endswith("Z"))
        self.assertIn("2021-12-20", dto.end_time)
        self.assertEqual(dto.vehicle_type, "FOUR_WHEELER")

    def test_bill_parking_history_dto_from_raw_without_end_time(self):
        """Test BillParkingHistoryDTO.from_raw without end_time"""
        dto = BillParkingHistoryDTO.from_raw(
            ticket_id="T456",
            number_plate="XYZ789",
            building_id="B2",
            building_name="Tower",
            floor_number=2,
            slot_number=10,
            start_time=1640000000,
            end_time=None,
            vehicle_type="TWO_WHEELER",
        )

        self.assertEqual(dto.ticket_id, "T456")
        self.assertEqual(dto.number_plate, "XYZ789")
        self.assertIsNone(dto.end_time)

    def test_bill_response_dto_creation(self):
        """Test BillResponseDTO can be created"""
        parking_history_data = {
            "TicketId": "T123",
            "NumberPlate": "ABC123",
            "BuildingId": "B1",
            "BuildingName": "HQ",
            "FloorNumber": 1,
            "SlotNumber": 5,
            "VehicleType": "FOUR_WHEELER",
            "StartTime": "2021-12-20T13:46:40Z",
            "EndTime": "2021-12-20T16:33:20Z",
        }

        bill = BillResponseDTO(
            parking_history=[BillParkingHistoryDTO(**parking_history_data)],
            total_amount=150.50,
            bill_date="2021-12-31",
            user_email="user@test.com",
            user_id="U123",
            billing_month=12,
            billing_year=2021,
        )

        self.assertEqual(bill.total_amount, 150.50)
        self.assertEqual(bill.bill_date, "2021-12-31")
        self.assertEqual(bill.user_email, "user@test.com")
        self.assertEqual(bill.user_id, "U123")
        self.assertEqual(bill.billing_month, 12)
        self.assertEqual(bill.billing_year, 2021)
        self.assertEqual(len(bill.parking_history), 1)


if __name__ == "__main__":
    unittest.main()
