import unittest

from app.dto.login import LoginDTO, JwtDTO
from app.dto.register import RegisterDTO
from app.dto.office import AddOfficeRequestDTO, OfficeResponseDTO
from app.dto.parking import ParkRequestDTO
from app.dto.vehicle import AddVehicleRequestDTO, VehicleResponseDTO


class TestDTOs(unittest.TestCase):
    def test_login_dto(self):
        """Test LoginDTO creation"""
        dto = LoginDTO(email="test@example.com", password="pass123")
        self.assertEqual(dto.email, "test@example.com")
        self.assertEqual(dto.password, "pass123")

    def test_jwt_dto(self):
        """Test JwtDTO creation"""
        dto = JwtDTO(jwt="token123")
        self.assertEqual(dto.jwt, "token123")

    def test_register_dto(self):
        """Test RegisterDTO creation"""
        dto = RegisterDTO(
            name="john", 
            email="john@test.com", 
            password="pass123", 
            officeId="o1"
        )
        self.assertEqual(dto.name, "john")
        self.assertEqual(dto.email, "john@test.com")

    def test_add_office_dto(self):
        """Test AddOfficeRequestDTO creation"""
        dto = AddOfficeRequestDTO(office_name="HR", floor_number=2)
        self.assertEqual(dto.office_name, "HR")
        self.assertEqual(dto.floor_number, 2)

    def test_office_response_dto(self):
        """Test OfficeResponseDTO creation"""
        dto = OfficeResponseDTO(
            building_id="b1",
            floor_number=1,
            office_name="Engineering",
            office_id="o1"
        )
        self.assertEqual(dto.building_id, "b1")
        self.assertEqual(dto.office_name, "Engineering")

    def test_park_request_dto(self):
        """Test ParkRequestDTO creation"""
        dto = ParkRequestDTO(numberplate="ABC123")
        self.assertEqual(dto.numberplate, "ABC123")


if __name__ == "__main__":
    unittest.main()
