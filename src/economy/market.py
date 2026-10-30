from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Transaction:
    buyer_id: str
    seller_id: str
    item_instance_id: str
    price: float
    tick: int

class Market:
    """Local market for item exchange and transactions."""

    def __init__(self):
        self.transactions: List[Transaction] = []

    def execute_transaction(self, buyer, seller, item_instance, price: float, tick: int) -> bool:
        if buyer.wealth < price:
            return False
        if item_instance not in seller.inventory:
            return False

        buyer.wealth -= price
        seller.wealth += price

        seller.inventory.remove(item_instance)
        item_instance.owner_id = buyer.id
        buyer.inventory.append(item_instance)

        self.transactions.append(Transaction(buyer.id, seller.id, item_instance.instance_id, price, tick))
        return True
