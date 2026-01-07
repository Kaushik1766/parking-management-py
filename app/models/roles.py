from enum import Enum


class Roles(str, Enum):
    ADMIN = "Admin"
    CUSTOMER = "Customer"

    @staticmethod
    def from_num(v:int):
        if v==0:
            return Roles.CUSTOMER
        elif v==1:
            return Roles.ADMIN
        else:
            raise TypeError("Invalid role number")
