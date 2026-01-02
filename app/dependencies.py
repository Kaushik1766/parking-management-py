from contextlib import asynccontextmanager
from mypy_boto3_dynamodb import DynamoDBServiceResource
import boto3

from fastapi import FastAPI, Request


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
