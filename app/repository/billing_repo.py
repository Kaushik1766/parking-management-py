from typing import Annotated, cast
from asyncio.threads import to_thread

from fastapi import Depends
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.constants import TABLE
from app.dependencies import get_db
from app.models.bill import Bill


class BillingRepository:
    def __init__(
        self,
        db: Annotated[DynamoDBServiceResource, Depends(get_db)],
    ):
        self.db = db
        self.table = db.Table(TABLE)

    async def get_bill(self, user_id: str, month: int, year: int) -> Bill | None:
        item = await to_thread(
            lambda: self.table.meta.client.get_item(
                TableName=TABLE,
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"BILL#{year}#{month}",
                },
            ).get("Item")
        )

        if not item:
            return None

        bill = Bill(user_id=user_id, **cast(dict, item))
        return bill
