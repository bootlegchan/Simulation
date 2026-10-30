from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CivicOffice:
    office_id: str
    title: str  # e.g., Mayor, TaxCollector, Magistrate, Sheriff
    holder_id: Optional[str] = None
    salary: float = 20.0
    tax_rate: float = 0.1

class MunicipalTreasury:
    """Town municipal vault for tax collection and infrastructure projects."""

    def __init__(self, initial_balance: float = 500.0):
        self.balance = initial_balance

    def deposit_tax(self, amount: float) -> None:
        self.balance += max(0.0, amount)

    def withdraw_funds(self, amount: float) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

class CorruptionManager:
    """Evaluates bribery success probability and blackmail mechanics."""

    @staticmethod
    def calculate_bribe_success_probability(bribe_amount: float, official_wealth_need: float, anonymity: float = 0.5) -> float:
        base_prob = (bribe_amount / 50.0) * (official_wealth_need / 100.0) * anonymity
        return max(0.05, min(0.95, base_prob))
