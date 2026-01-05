import boto3
import pytest
from pytest import fixture

from app.repository.building_repo import BuildingRepository
from app.repository.vehicle_repo import VehicleRepository


@fixture
def building_repo() -> BuildingRepository:
    db = boto3.resource("dynamodb")
    return BuildingRepository(db)

@pytest.mark.parametrize(
    ("building_id", "expected_name", "exception"),
    [
        ("27307900-fbe9-4838-b9a2-d1ad6b25f9a7", "eiffel", False),
        ("random-id", "", True)
    ]

)
async def test_get_building_by_id(building_repo: BuildingRepository, building_id: str, expected_name: str, exception: bool):
    if exception:
        with pytest.raises(Exception):
            await building_repo.get_building_by_id(building_id)
    else:
        building = await building_repo.get_building_by_id(building_id)
        assert building.name == expected_name