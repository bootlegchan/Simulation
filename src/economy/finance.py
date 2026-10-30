from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class LoanContract:
    loan_id: str
    lender_id: str
    borrower_id: str
    principal: float
    interest_rate: float  # e.g., 0.05 per tick/day
    remaining_balance: float
    collateral_property_id: Optional[str] = None
    is_defaulted: bool = False

class DebtManager:
    """Manages loans, interest accrual, defaults, and collateral forfeiture."""

    def __init__(self):
        self.loans: Dict[str, LoanContract] = {}

    def issue_loan(self, loan_id: str, lender_id: str, borrower_id: str, principal: float, interest_rate: float, collateral_id: Optional[str] = None) -> LoanContract:
        contract = LoanContract(
            loan_id=loan_id,
            lender_id=lender_id,
            borrower_id=borrower_id,
            principal=principal,
            interest_rate=interest_rate,
            remaining_balance=principal,
            collateral_property_id=collateral_id
        )
        self.loans[loan_id] = contract
        return contract

    def accrue_interest(self) -> None:
        for loan in self.loans.values():
            if not loan.is_defaulted:
                loan.remaining_balance += loan.remaining_balance * loan.interest_rate

    def repay_loan(self, loan_id: str, amount: float) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.is_defaulted:
            return 0.0
        repaid = min(loan.remaining_balance, amount)
        loan.remaining_balance -= repaid
        return repaid

class BlackMarket:
    """Black market illicit trading engine for contraband/stolen items."""

    @staticmethod
    def is_illicit_transaction(item_is_contraband: bool, is_stolen: bool) -> bool:
        return item_is_contraband or is_stolen

    @staticmethod
    def calculate_black_market_price(base_price: float, risk_factor: float = 1.5) -> float:
        return round(base_price * risk_factor, 2)
