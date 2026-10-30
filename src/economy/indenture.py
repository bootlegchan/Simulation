"""
Survival Economics, Indentured Servitude & Contraband Fencing Engine.
Models desperate debt peonage contracts, wage garnishment, and underground black market fences.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject

@dataclass
class IndentureContract:
    contract_id: str
    debtor_id: str
    master_id: str
    initial_debt_gold: float
    remaining_debt_gold: float
    wage_garnishment_rate: float = 0.75  # 75% of earned wages transferred to master
    duration_ticks: int = 43200  # 30 days
    start_tick: int = 0
    is_fulfilled: bool = False

class IndentureManager:
    """Manages debt peonage contracts between destitute citizens and wealthy creditors."""

    def __init__(self):
        self.contracts: Dict[str, IndentureContract] = {}

    def issue_indenture(
        self,
        debtor: NPC,
        master: NPC,
        debt_amount: float,
        current_tick: int
    ) -> IndentureContract:
        """Binds a destitute debtor to a master, garnishing future wages to settle debt."""
        contract_id = f"indenture_{uuid.uuid4().hex[:8]}"
        contract = IndentureContract(
            contract_id=contract_id,
            debtor_id=debtor.id,
            master_id=master.id,
            initial_debt_gold=debt_amount,
            remaining_debt_gold=debt_amount,
            start_tick=current_tick
        )
        self.contracts[contract_id] = contract

        debtor.social_profile["is_indentured"] = True
        debtor.social_profile["indenture_master_id"] = master.id
        debtor.adjust_feeling("stress", 30.0)
        debtor.adjust_feeling("resentment", 35.0)
        debtor.adjust_feeling("pride", -40.0)

        master.adjust_feeling("pride", 25.0)

        return contract

    def process_wage_garnishment(
        self,
        contract_id: str,
        earned_wage: float,
        debtor: NPC,
        master: NPC
    ) -> Dict[str, Any]:
        """Garnishes a debtor's wage, routing 75% to master to pay down debt principal."""
        if contract_id not in self.contracts:
            return {"success": False, "reason": "Invalid contract ID"}

        contract = self.contracts[contract_id]
        if contract.is_fulfilled:
            return {"success": False, "reason": "Contract already fulfilled"}

        garnished = round(earned_wage * contract.wage_garnishment_rate, 2)
        paid_to_debtor = round(earned_wage - garnished, 2)

        actual_reduction = min(contract.remaining_debt_gold, garnished)
        contract.remaining_debt_gold = max(0.0, round(contract.remaining_debt_gold - actual_reduction, 2))

        master.wealth += actual_reduction
        debtor.wealth += paid_to_debtor

        if contract.remaining_debt_gold <= 0.0:
            contract.is_fulfilled = True
            debtor.social_profile["is_indentured"] = False
            debtor.adjust_feeling("contentment", 45.0)
            debtor.adjust_feeling("stress", -30.0)

        return {
            "success": True,
            "contract_id": contract_id,
            "earned_wage": earned_wage,
            "garnished_to_master": actual_reduction,
            "kept_by_debtor": paid_to_debtor,
            "remaining_debt": contract.remaining_debt_gold,
            "is_fulfilled": contract.is_fulfilled
        }


class ContrabandFencingRing:
    """Underground broker counter for fencing stolen heirlooms, counterfeit coinage, and moonshine."""

    @staticmethod
    def fence_stolen_item(
        thief: NPC,
        broker_counter: InteractiveObject,
        stolen_item: ItemInstance,
        item_base_value: float,
        fence_commission_rate: float = 0.40  # Fence takes 40% cut
    ) -> Dict[str, Any]:
        """Fences an illicit or stolen item into laundered gold."""
        if not broker_counter.has_capability("fence_stolen_goods"):
            return {"success": False, "reason": "Object lacks fence_stolen_goods capability"}

        if stolen_item not in thief.inventory:
            return {"success": False, "reason": "Item not in thief inventory"}

        thief.inventory.remove(stolen_item)
        payout = round(item_base_value * (1.0 - fence_commission_rate), 2)
        thief.wealth += payout

        thief.adjust_feeling("pride", 15.0)
        thief.vices["crime_propensity"] = min(100.0, thief.vices.get("crime_propensity", 0.0) + 3.0)

        return {
            "success": True,
            "item_fenced_id": stolen_item.item_def_id,
            "base_value": item_base_value,
            "laundered_payout": payout,
            "thief_wealth_after": thief.wealth
        }
