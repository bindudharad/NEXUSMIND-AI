from enum import Enum


class EnterpriseRole(str, Enum):
    CEO = "CEO"
    HR = "HR"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"
    ADMIN = "Admin"
