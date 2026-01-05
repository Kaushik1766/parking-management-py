import pytest
from pytest import fixture
import boto3
from app.models.vehicle import Vehicle
from typing import List

from app.repository.vehicle_repo import VehicleRepository


@fixture
def vehicle_repo()->VehicleRepository:
    return VehicleRepository(db=boto3.resource("dynamodb"))

@pytest.mark.parametrize(
    ("id", "expected_result_len"),
    [
        ("3de3211f-9db6-4ced-9398-157bd7d2b839", 3),
        ("63d9f323-f8dd-4acf-9abb-e7a9539551be", 0),
        ("adfasdfas", 0),
    ]
)
async def test_get_vehicles_by_user_id(vehicle_repo: VehicleRepository, id:str, expected_result_len:int):
    vehicles = await vehicle_repo.get_vehicles_by_user_id(id)
    assert len(vehicles) == expected_result_len, isinstance(vehicles, list)