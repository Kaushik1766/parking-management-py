import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_db, get_user
from app.dto.login import UserJWT
from app.models.roles import Roles
from app.errors.web_exception import WebException, UNAUTHORIZED_ERROR


class TestDependencies(unittest.TestCase):
    def test_get_db(self):
        """Test get_db returns db from app state"""
        mock_db = Mock()
        mock_request = Mock(spec=Request)
        mock_request.app.state.db = mock_db

        result = get_db(mock_request)
        self.assertEqual(result, mock_db)

    def test_get_user_valid_token_admin_role(self):
        """Test get_user with valid token and admin role"""
        import time
        token_payload = {
            "id": "user123",
            "email": "admin@test.com",
            "role": "Admin",
            "officeId": "office1",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        
        token = jwt.encode(token_payload, "asdfasasdfasdf", algorithm="HS256")
        mock_token = Mock(spec=HTTPAuthorizationCredentials)
        mock_token.credentials = token

        get_auth_user = get_user([Roles.ADMIN])
        user = get_auth_user(mock_token)

        self.assertIsInstance(user, UserJWT)
        self.assertEqual(user.id, "user123")
        self.assertEqual(user.email, "admin@test.com")
        self.assertEqual(user.role, Roles.ADMIN)

    def test_get_user_valid_token_customer_role(self):
        """Test get_user with valid token and customer role"""
        import time
        token_payload = {
            "id": "user456",
            "email": "user@test.com",
            "role": "Customer",
            "officeId": "office2",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        
        token = jwt.encode(token_payload, "asdfasasdfasdf", algorithm="HS256")
        mock_token = Mock(spec=HTTPAuthorizationCredentials)
        mock_token.credentials = token

        get_auth_user = get_user([Roles.CUSTOMER])
        user = get_auth_user(mock_token)

        self.assertIsInstance(user, UserJWT)
        self.assertEqual(user.id, "user456")
        self.assertEqual(user.email, "user@test.com")
        self.assertEqual(user.role, Roles.CUSTOMER)

    def test_get_user_unauthorized_role(self):
        """Test get_user raises exception when user role is not allowed"""
        import time
        token_payload = {
            "id": "user123",
            "email": "user@test.com",
            "role": "Customer",
            "officeId": "office1",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        
        token = jwt.encode(token_payload, "asdfasasdfasdf", algorithm="HS256")
        mock_token = Mock(spec=HTTPAuthorizationCredentials)
        mock_token.credentials = token

        get_auth_user = get_user([Roles.ADMIN])  # Only allow admin
        
        with self.assertRaises(WebException) as ctx:
            get_auth_user(mock_token)
        
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.error_code, UNAUTHORIZED_ERROR)
        self.assertEqual(ctx.exception.message, "Unauthorized user")

    def test_get_user_invalid_token(self):
        """Test get_user raises exception with invalid token"""
        mock_token = Mock(spec=HTTPAuthorizationCredentials)
        mock_token.credentials = "invalid_token"

        get_auth_user = get_user([Roles.CUSTOMER])
        
        with self.assertRaises(WebException) as ctx:
            get_auth_user(mock_token)
        
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.error_code, UNAUTHORIZED_ERROR)

    def test_get_user_allows_multiple_roles(self):
        """Test get_user allows any of the specified roles"""
        import time
        token_payload = {
            "id": "user123",
            "email": "user@test.com",
            "role": "Customer",
            "officeId": "office1",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        
        token = jwt.encode(token_payload, "asdfasasdfasdf", algorithm="HS256")
        mock_token = Mock(spec=HTTPAuthorizationCredentials)
        mock_token.credentials = token

        # Should work with both ADMIN and CUSTOMER allowed
        get_auth_user = get_user([Roles.ADMIN, Roles.CUSTOMER])
        user = get_auth_user(mock_token)

        self.assertIsInstance(user, UserJWT)
        self.assertEqual(user.role, Roles.CUSTOMER)


class TestLifespan(unittest.IsolatedAsyncioTestCase):
    """Test lifespan context manager"""
    
    @patch('app.dependencies.boto3')
    async def test_lifespan_initializes_db(self, mock_boto3):
        """Test lifespan successfully initializes database"""
        from app.dependencies import lifespan
        
        mock_db = Mock()
        mock_boto3.resource.return_value = mock_db
        mock_app = Mock()
        mock_app.state = Mock()
        
        async with lifespan(mock_app):
            self.assertEqual(mock_app.state.db, mock_db)
            mock_boto3.resource.assert_called_once()


if __name__ == "__main__":
    unittest.main()
