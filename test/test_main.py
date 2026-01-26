import unittest
from unittest.mock import Mock

from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from fastapi.exceptions import ValidationException
from pydantic import ValidationError

from app.main import (
    http_exception_handler,
    exception_handler,
    web_exception_handler,
    validation_exception_handler,
)
from app.errors.web_exception import WebException, VALIDATION_ERROR, DB_ERROR, UNEXPECTED_ERROR


class TestMainExceptionHandlers(unittest.TestCase):
    def setUp(self):
        self.mock_request = Mock()

    def test_http_exception_handler(self):
        """Test http_exception_handler returns correct JSON response"""
        exc = HTTPException(status_code=404, detail="Not found")
        response = http_exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.body.decode(), '{"message":"Not found","code":1003}')

    def test_exception_handler_conditional_check_failed(self):
        """Test exception_handler for ConditionalCheckFailedException"""
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "Condition failed"
            }
        }
        exc = ClientError(error_response, "PutItem")
        response = exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.body.decode(),
            '{"message":"Resource already exists","code":1003}'
        )

    def test_exception_handler_transaction_canceled(self):
        """Test exception_handler for TransactionCanceledException"""
        error_response = {
            "Error": {
                "Code": "TransactionCanceledException",
                "Message": "Transaction canceled"
            }
        }
        exc = ClientError(error_response, "TransactWriteItems")
        response = exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.body.decode(),
            '{"message":"Transaction canceled due to conflict","code":1003}'
        )

    def test_exception_handler_other_error(self):
        """Test exception_handler for other ClientError"""
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Resource not found"
            }
        }
        exc = ClientError(error_response, "GetItem")
        response = exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.body.decode(),
            '{"message":"Internal Server Error","code":1003}'
        )

    def test_web_exception_handler(self):
        """Test web_exception_handler returns correct JSON response"""
        exc = WebException(
            status_code=400,
            message="Bad request",
            error_code=DB_ERROR
        )
        response = web_exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.body.decode(),
            '{"message":"Bad request","code":1001}'
        )

    def test_validation_exception_handler(self):
        """Test validation_exception_handler returns correct JSON response"""
        # Create a mock ValidationException
        exc = Mock(spec=ValidationException)
        exc.errors.return_value = [{"loc": ["field"], "msg": "Invalid", "type": "value_error"}]
        exc.__str__ = Mock(return_value="Validation error")
        
        response = validation_exception_handler(self.mock_request, exc)
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("Validation error", response.body.decode())
        self.assertIn(str(VALIDATION_ERROR), response.body.decode())

    def test_health_endpoint(self):
        """Test health endpoint returns ok"""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
