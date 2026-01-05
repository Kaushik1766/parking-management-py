from fastapi.params import Depends

from app.repository.vehicle_repo import VehicleRepo


class VehicleService:
    def __init__(self, vehicle_repo: VehicleRepo = Depends(VehicleRepo)):
        self.vehicle_repo = vehicle_repo

    # def get_vehicles(self, ):