import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.models.parking_history import ParkingHistory, _now_ts


class TestParkingHistory(unittest.TestCase):
    @patch('app.models.parking_history.datetime')
    def test_now_ts(self, mock_datetime):
        """Test _now_ts returns current timestamp"""
        # Mock the datetime to return a fixed timestamp
        mock_now = datetime(2021, 12, 20, 13, 46, 40, tzinfo=timezone.utc)
        mock_datetime.datetime.now.return_value = mock_now
        
        result = _now_ts()
        self.assertEqual(result, 1640008000)

    def test_parking_history_with_default_start_time(self):
        """Test ParkingHistory uses default factory for start_time"""
        history = ParkingHistory(
            user_id="user123",
            Numberplate="ABC123",
            BuildingId="b1",
            FloorNumber=1,
            SlotId=5,
            ParkingId="p1",
            VehicleType="FOUR_WHEELER",
        )
        
        self.assertEqual(history.user_id, "user123")
        self.assertEqual(history.numberplate, "ABC123")
        self.assertEqual(history.building_id, "b1")
        self.assertEqual(history.floor_number, 1)
        self.assertEqual(history.slot_id, 5)
        self.assertEqual(history.parking_id, "p1")
        self.assertEqual(history.vehicle_type, "FOUR_WHEELER")
        self.assertIsNone(history.end_time)
        # start_time should be set to current timestamp
        self.assertIsInstance(history.start_time, int)
        self.assertGreater(history.start_time, 0)

    def test_parking_history_with_explicit_start_time(self):
        """Test ParkingHistory with explicit start_time"""
        history = ParkingHistory(
            user_id="user123",
            Numberplate="ABC123",
            BuildingId="b1",
            FloorNumber=1,
            SlotId=5,
            StartTime=1640000000,
            EndTime=1640010000,
            ParkingId="p1",
            VehicleType="TWO_WHEELER",
        )
        
        self.assertEqual(history.start_time, 1640000000)
        self.assertEqual(history.end_time, 1640010000)
        self.assertEqual(history.vehicle_type, "TWO_WHEELER")

    def test_parking_history_user_id_excluded(self):
        """Test that user_id is excluded from dict representation"""
        history = ParkingHistory(
            user_id="user123",
            Numberplate="ABC123",
            BuildingId="b1",
            FloorNumber=1,
            SlotId=5,
            ParkingId="p1",
        )
        
        # Convert to dict and check user_id is excluded
        history_dict = history.model_dump()
        self.assertNotIn("user_id", history_dict)


if __name__ == "__main__":
    unittest.main()
