import asyncio
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app import dependencies
from app.errors.web_exception import WebException
from app.constants import SLOT_LAYOUT, TABLE
from app.models.bill import Bill
from app.models.building import Building
from app.models.floor import Floor
from app.models.office import Office
from app.models.parking_history import ParkingHistory
from app.models.roles import Roles
from app.models.slot import Slot, OccupantDetails
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repository import billing_repo, building_repo, floor_repo, office_repo, parking_repo, slot_repo, user_repo, vehicle_repo
from app.repository.billing_repo import BillingRepository
from app.repository.building_repo import BuildingRepository
from app.repository.floor_repo import FloorRepository
from app.repository.office_repo import OfficeRepository
from app.repository.parking_repo import ParkingRepository
from app.repository.slot_repo import SlotRepository
from app.repository.user_repo import UserRepository
from app.repository.vehicle_repo import VehicleRepository
from app.services.office import OfficeService
from app.dto.office import AddOfficeRequestDTO


@pytest.fixture(autouse=True)
def patch_to_thread(monkeypatch):
    async def immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    for module in (
        billing_repo,
        building_repo,
        floor_repo,
        office_repo,
        parking_repo,
        slot_repo,
        user_repo,
        vehicle_repo,
    ):
        monkeypatch.setattr(module, "to_thread", immediate)


def _mock_table_with_client():
    table = Mock()
    client = Mock()
    table.meta = SimpleNamespace(client=client)
    return table, client


@pytest.mark.asyncio
async def test_billing_repo_get_bill_paths():
    table, client = _mock_table_with_client()
    db = Mock()
    db.Table.return_value = table

    item = {
        "BillingMonth": 1,
        "BillingYear": 2024,
        "TotalAmount": 10,
        "BillDate": "2024-01-01",
        "ParkingHistory": [],
    }
    client.get_item.side_effect = [{"Item": item}, {}]

    repo = BillingRepository(db=db)

    bill = await repo.get_bill("u1", 1, 2024)
    assert isinstance(bill, Bill)
    assert bill.billing_year == 2024

    missing = await repo.get_bill("u1", 2, 2024)
    assert missing is None


@pytest.mark.asyncio
async def test_building_repo_branches():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table), meta=SimpleNamespace(client=client))

    building_item = {
        "BuildingId": "b1",
        "BuildingName": "Main",
        "TotalFloors": 2,
        "TotalSlots": 20,
        "AvailableSlots": 10,
    }
    table.get_item.side_effect = [
        {"Item": building_item},
        {},
    ]
    table.query.return_value = {
        "Items": [
            {**building_item, "PK": "BUILDING", "SK": "BUILDING#b1"},
        ]
    }

    repo = BuildingRepository(db=db)

    building = await repo.get_building_by_id("b1")
    assert isinstance(building, Building)
    with pytest.raises(WebException):
        await repo.get_building_by_id("missing")

    buildings = await repo.get_buildings()
    assert len(buildings) == 1

    await repo.add_building(Building(**building_item))
    table.put_item.assert_called_once()


@pytest.mark.asyncio
async def test_floor_repo_add_and_query(monkeypatch):
    table, client = _mock_table_with_client()
    batch = Mock()
    batch.__enter__ = Mock(return_value=batch)
    batch.__exit__ = Mock(return_value=False)
    table.batch_writer.return_value = batch
    db = Mock(Table=Mock(return_value=table))

    repo = FloorRepository(db=db)
    await repo.add_floor("B1", 1)

    assert batch.put_item.call_count == len(SLOT_LAYOUT)
    table.put_item.assert_called_once()
    table.meta.client.update_item.assert_called_once()

    table.query.return_value = {
        "Items": [
            {
                "FloorNumber": 1,
                "TotalSlots": len(SLOT_LAYOUT),
                "AvailableSlots": len(SLOT_LAYOUT),
            }
        ]
    }
    floors = await repo.get_floors("B1")
    assert floors and isinstance(floors[0], Floor)


@pytest.mark.asyncio
async def test_office_repo_all_paths():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table), meta=SimpleNamespace(client=client))

    office = Office(
        OfficeName="O1",
        BuildingId="B1",
        FloorNumber=1,
        OfficeId="OFF-1",
    )

    table.get_item.return_value = {"Item": office.model_dump(by_alias=True)}
    table.query.return_value = {
        "Items": [office.model_dump(by_alias=True)]
    }

    class TxnCancelled(Exception):
        def __init__(self):
            super().__init__("cancelled")
            self.response = {"CancellationReasons": ["duplicate"]}

    client.exceptions = SimpleNamespace(TransactionCanceledException=TxnCancelled)

    repo = OfficeRepository(db=db)

    await repo.add_office(office)

    client.transact_write_items.side_effect = TxnCancelled()
    with pytest.raises(WebException):
        await repo.add_office(office)
    client.transact_write_items.side_effect = None

    fetched = await repo.get_office_by_id(office.office_id)
    assert fetched.office_id == office.office_id

    offices = await repo.get_offices()
    assert offices and offices[0].office_id == office.office_id

    all_offices = await repo.get_all_offices()
    assert len(all_offices) == 1

    await repo.delete_office(office.building_id, office.floor_number, office.office_id)
    client.transact_write_items.assert_called()


@pytest.mark.asyncio
async def test_parking_repo_paths():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table))

    repo = ParkingRepository(db=db)

    # add_parking user missing
    table.get_item.return_value = {}
    with pytest.raises(WebException):
        await repo.add_parking(
            ParkingHistory(
                user_id="u1",
                Numberplate="NP",
                BuildingId="B1",
                FloorNumber=1,
                SlotId=1,
                StartTime=1,
                ParkingId="p1",
                VehicleType="TwoWheeler",
            )
        )

    # add_parking success path
    table.get_item.return_value = {
        "Item": {
            "Id": "u1",
            "Username": "user",
            "Email": "u@example.com",
            "PasswordHash": "pw",
            "OfficeId": "O1",
            "Role": Roles.CUSTOMER,
        }
    }
    client.transact_write_items.side_effect = [None, None]
    await repo.add_parking(
        ParkingHistory(
            user_id="u1",
            Numberplate="NP",
            BuildingId="B1",
            FloorNumber=1,
            SlotId=1,
            StartTime=2,
            ParkingId="p2",
            VehicleType="TwoWheeler",
        )
    )

    # unpark_by_numberplate success path
    table.query.return_value = {
        "Items": [
            {
                "PK": "USER#u1",
                "SK": "PARKING#2",
                "Numberplate": "NP",
                "BuildingId": "B1",
                "FloorNumber": 1,
                "SlotId": 1,
                "StartTime": 2,
                "ParkingId": "p2",
                "VehicleType": "TwoWheeler",
            }
        ]
    }
    await repo.unpark_by_numberplate("u1", "NP")

    # unpark missing parking
    table.query.return_value = {"Items": []}
    with pytest.raises(WebException):
        await repo.unpark_by_numberplate("u1", "NONE")

    # get_parking_history success
    table.query.return_value = {
        "Items": [
            {
                "PK": "USER#u1",
                "SK": "PARKING#1",
                "Numberplate": "NP",
                "BuildingId": "B1",
                "FloorNumber": 1,
                "SlotId": 1,
                "StartTime": 1,
                "EndTime": 2,
                "ParkingId": "p1",
                "VehicleType": "TwoWheeler",
            }
        ]
    }
    history = await repo.get_parking_history("u1", 0, 3)
    assert history and isinstance(history[0], ParkingHistory)


@pytest.mark.asyncio
async def test_slot_repo_paths():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table))

    slot_items = [
        {
            "SlotId": 1,
            "SlotType": "TwoWheeler",
            "IsAssigned": False,
            "IsOccupied": False,
        },
        {
            "SlotId": 2,
            "SlotType": "FourWheeler",
            "IsAssigned": True,
            "IsOccupied": False,
        },
    ]
    table.query.return_value = {"Items": slot_items}

    repo = SlotRepository(db=db)
    floor = Floor(building_id="B1", FloorNumber=1, TotalSlots=2, AvailableSlots=2)

    free_slots = await repo.get_free_slots_by_floor(floor)
    assert len(free_slots) == 1

    occupant = OccupantDetails(
        Username="u",
        NumberPlate="NP",
        Email="u@example.com",
        StartTime=1,
    )
    slot = Slot(
        building_id="B1",
        floor_number=1,
        SlotId=1,
        SlotType=slot_items[0]["SlotType"],
        IsAssigned=True,
        IsOccupied=True,
        OccupiedBy=occupant,
    )
    await repo.update_slot(slot)
    await repo.update_slot_occupancy("B1", 1, 2, occupant, True)
    table.update_item.assert_called()


@pytest.mark.asyncio
async def test_user_repo_paths():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table))

    uid_item = {"UUID": "u1"}
    profile_item = {
        "Id": "u1",
        "Username": "user",
        "Email": "u@example.com",
        "PasswordHash": "pw",
        "OfficeId": "O1",
        "Role": Roles.CUSTOMER,
    }

    table.get_item.side_effect = [
        {"Item": uid_item},
        {"Item": profile_item},
    ]
    repo = UserRepository(db=db)
    user = await repo.get_by_email("u@example.com")
    assert isinstance(user, User)

    table.get_item.side_effect = [{}, {"Item": uid_item}]
    with pytest.raises(Exception):
        await repo.get_by_email("missing@example.com")

    table.get_item.side_effect = [{"Item": uid_item}, {}]
    with pytest.raises(WebException):
        await repo.get_by_email("missing-profile@example.com")

    user_model = User(**profile_item)
    client.transact_write_items.return_value = None
    await repo.save_user(user_model)
    client.transact_write_items.assert_called()


@pytest.mark.asyncio
async def test_vehicle_repo_paths():
    table, client = _mock_table_with_client()
    db = Mock(Table=Mock(return_value=table))

    vehicles = [
        {
            "VehicleId": "v1",
            "Numberplate": "NP1",
            "VehicleType": "TwoWheeler",
            "IsParked": False,
        },
        {
            "VehicleId": "v2",
            "Numberplate": "NP2",
            "VehicleType": "FourWheeler",
            "IsParked": True,
        },
    ]
    table.query.return_value = {"Items": vehicles}
    repo = VehicleRepository(db=db)

    owned = await repo.get_vehicles_by_user_id("u1")
    assert len(owned) == 2

    table.get_item.return_value = {"Item": vehicles[0]}
    found = await repo.get_vehicle_by_number_plate("u1", "NP1")
    assert found.number_plate == "NP1"

    table.get_item.return_value = {}
    assert await repo.get_vehicle_by_number_plate("u1", "NONE") is None

    vehicle = Vehicle(
        VehicleId="v3",
        Numberplate="NP3",
        VehicleType="TwoWheeler",
        IsParked=False,
        AssignedSlot=None,
    )
    await repo.save_vehicle(vehicle, "u1")
    table.put_item.assert_called()

    table.query.return_value = {"Items": [{"IsParked": True}]}
    with pytest.raises(WebException):
        await repo.delete_vehicle("u1", "NP1")

    table.query.return_value = {"Items": []}
    await repo.delete_vehicle("u1", "NP1")
    table.delete_item.assert_called()


@pytest.mark.asyncio
async def test_lifespan_handles_boto_error(monkeypatch):
    monkeypatch.setattr(dependencies.boto3, "resource", Mock(side_effect=Exception("boom")))

    app = SimpleNamespace(state=SimpleNamespace())
    with pytest.raises(RuntimeError):
        async with dependencies.lifespan(app):
            pass


@pytest.mark.asyncio
async def test_office_service_floor_missing(monkeypatch):
    building_repo_mock = Mock()
    floor_repo_mock = Mock()
    office_repo_mock = Mock()

    building_repo_mock.get_building_by_id = AsyncMock(return_value=None)
    floor_repo_mock.get_floors = AsyncMock(return_value=[])

    service = OfficeService(
        building_repo=building_repo_mock,
        office_repo=office_repo_mock,
        floor_repo=floor_repo_mock,
    )

    with pytest.raises(WebException):
        await service.add_office(
            "B1",
            AddOfficeRequestDTO(office_name="New", floor_number=2),
        )
