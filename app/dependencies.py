from app.models.roles import Roles
import jwt
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.params import Depends
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mypy_boto3_dynamodb import DynamoDBServiceResource
import boto3

from fastapi import FastAPI, Request

from app.dto.login import UserJWT
from app.errors.web_exception import WebException, UNAUTHORIZED_ERROR


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db: DynamoDBServiceResource = boto3.resource("dynamodb")
        app.state.db = db
        yield
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")


def get_db(req: Request) -> DynamoDBServiceResource:
    return req.app.state.db
    # return boto3.resource("dynamodb")


bearer_security = HTTPBearer(scheme_name='Bearer')

def get_user(allowed_roles:list[Roles]):
    def get_auth_user(token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_security)]):
        try:
            decoded_token = jwt.decode(jwt=token.credentials, verify=True, key="asdfasasdfasdf", algorithms=["HS256"])
            user = UserJWT(**decoded_token)

            if user.role not in allowed_roles:
                raise WebException(status_code=401, error_code=UNAUTHORIZED_ERROR, message="Unauthorized user")
            return user
        except WebException:
            raise
        except Exception as exc:
            print(exc)
            raise WebException(status_code=status.HTTP_401_UNAUTHORIZED, error_code=UNAUTHORIZED_ERROR,  message="JWT is invalid or expired")
    return get_auth_user