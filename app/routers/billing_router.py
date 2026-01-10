from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_user
from app.dto.login import UserJWT
from app.models.roles import Roles
from app.services.billing import BillingService

router = APIRouter()


@router.get("/billing", tags=["billing"])
async def get_bill(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=1970),
    current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))] = None,
    billing_service: Annotated[BillingService, Depends(BillingService)] = None,
):
    return await billing_service.get_bill(
        user_id=current_user.id,
        user_email=current_user.email,
        month=month,
        year=year,
    )
