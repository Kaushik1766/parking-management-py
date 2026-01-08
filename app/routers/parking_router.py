from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from app.dependencies import get_user
from app.dto.login import UserJWT
from app.dto.parking import ParkRequestDTO
from app.models.roles import Roles
from app.services.parking import ParkingService

router = APIRouter()


@router.post("/")
async def park_vehicle(
        req: ParkRequestDTO,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))],
        parking_service: Annotated[ParkingService, Depends(ParkingService)],
):
    ticket_id = await parking_service.park(user_id=current_user.id, user_email=current_user.email, req=req)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"ticketId": ticket_id},
    )


@router.get("/")
async def get_parkings(
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))],
        parking_service: Annotated[ParkingService, Depends(ParkingService)],
        start_time: int | None = None,
        end_time: int | None = None,
):
    return await parking_service.get_parkings(user_id=current_user.id, start_time=start_time, end_time=end_time)


@router.patch("/{numberplate}/unpark")
async def unpark_vehicle(
        numberplate: str,
        current_user: Annotated[UserJWT, Depends(get_user([Roles.CUSTOMER]))],
        parking_service: Annotated[ParkingService, Depends(ParkingService)],
):
    await parking_service.unpark(user_id=current_user.id, numberplate=numberplate)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Vehicle unparked successfully"},
    )
