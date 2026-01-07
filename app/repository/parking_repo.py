from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from typing import Annotated

from app.constants import TABLE
from app.dependencies import get_db


class ParkingRepostiory:
    def __init__(
            self,
            db: Annotated[DynamoDBServiceResource, Depends(get_db)]
    ):
        self.db = db
        self.table = db.Table(TABLE)


    # async def add_parking(self, ):