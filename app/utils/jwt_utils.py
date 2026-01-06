import jwt

from app.dto.login import JwtDTO, UserJWT
from app.errors.web_exception import WebException, UNAUTHORIZED_ERROR
from starlette import status


def validate_jwt(token: str)->UserJWT:
    try:
        decoded_token = jwt.decode(jwt=token, verify=True, key="asdfasasdfasdf", algorithms=["HS256"])
        return UserJWT(**decoded_token)

    except Exception as exc:
        print(exc)
        raise WebException(status_code=status.HTTP_401_UNAUTHORIZED, error_code=UNAUTHORIZED_ERROR,  message="JWT is invalid or expired")

def test_validate_jwt():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc3NzQ0NTIsImlhdCI6MTc2NzY4ODA1MiwianRpIjoiM2RlMzIxMWYtOWRiNi00Y2VkLTkzOTgtMTU3YmQ3ZDJiODM5IiwiZW1haWwiOiJrYXVzaGlrQGEuY29tIiwiaWQiOiIzZGUzMjExZi05ZGI2LTRjZWQtOTM5OC0xNTdiZDdkMmI4MzkiLCJyb2xlIjowLCJvZmZpY2VJZCI6ImM0MmY4MDU0LTAxY2UtNDU4Mi04YWJhLWFjZDI2NDE2NzgxOSJ9.ySmIPVN2EieJVdpCN6XKmNgzGs1SGnJ-oeKYGDdPyJ0"

    assert validate_jwt(token=token).email == "kaushik@a.com"