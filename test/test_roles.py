import unittest

from app.models.roles import Roles


class TestRoles(unittest.TestCase):
    def test_roles_enum_values(self):
        """Test that roles have correct values"""
        self.assertEqual(Roles.ADMIN.value, "Admin")
        self.assertEqual(Roles.CUSTOMER.value, "Customer")

    def test_from_num_customer(self):
        """Test from_num returns CUSTOMER for 0"""
        self.assertEqual(Roles.from_num(0), Roles.CUSTOMER)

    def test_from_num_admin(self):
        """Test from_num returns ADMIN for 1"""
        self.assertEqual(Roles.from_num(1), Roles.ADMIN)

    def test_from_num_invalid(self):
        """Test from_num raises TypeError for invalid number"""
        with self.assertRaises(TypeError) as ctx:
            Roles.from_num(2)
        self.assertEqual(str(ctx.exception), "Invalid role number")

        with self.assertRaises(TypeError) as ctx:
            Roles.from_num(-1)
        self.assertEqual(str(ctx.exception), "Invalid role number")

    def test_roles_string_comparison(self):
        """Test that roles can be compared as strings"""
        self.assertEqual(Roles.ADMIN, "Admin")
        self.assertEqual(Roles.CUSTOMER, "Customer")


if __name__ == "__main__":
    unittest.main()
