import unittest

from app.errors.web_exception import WebException, DB_ERROR, VALIDATION_ERROR, UNEXPECTED_ERROR, UNAUTHORIZED_ERROR, CONFLICT_ERROR


class TestWebException(unittest.TestCase):
    def test_web_exception_creation(self):
        """Test WebException can be created"""
        exc = WebException(
            status_code=404,
            message="Not found",
            error_code=DB_ERROR
        )
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.message, "Not found")
        self.assertEqual(exc.error_code, DB_ERROR)

    def test_web_exception_with_all_error_codes(self):
        """Test WebException with all error codes"""
        codes = [DB_ERROR, VALIDATION_ERROR, UNEXPECTED_ERROR, UNAUTHORIZED_ERROR, CONFLICT_ERROR]
        for code in codes:
            exc = WebException(status_code=500, message="Error", error_code=code)
            self.assertEqual(exc.error_code, code)


if __name__ == "__main__":
    unittest.main()
