"""Civic Offices and Municipal Treasury."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class CivicOffice:
    office_id: str
    title: str
    incumbent_id: Optional[str] = None

class MunicipalTreasury:
    def __init__(self, balance: float = 500.0):
        self.balance: float = round(float(balance), 2)

    def withdraw_funds(self, amount: float) -> bool:
        if self.balance >= amount:
            self.balance = round(self.balance - amount, 2)
            return True
        return False
