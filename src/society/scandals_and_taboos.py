"""
Social Scandals, Moral Economies, Ostracism and Vice Escapism Engine.
Models community taboos, social shunning, price gouging on pariahs, and illicit vice dens.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject

class TabooType(Enum):
    UNMASKED_CULTIST = "UNMASKED_CULTIST"
    CHRONIC_DEBT_DEFAULT = "CHRONIC_DEBT_DEFAULT"
    PUBLIC_DESECRATION = "PUBLIC_DESECRATION"
    EXPOSED_EXTORTIONIST = "EXPOSED_EXTORTIONIST"
    FLAGRANT_ADULTERY = "FLAGRANT_ADULTERY"

@dataclass
class OstracismOrder:
    target_npc_id: str
    taboo: TabooType
    reason: str
    severity_stigma: float = 60.0  # 0 to 100
    issued_tick: int = 0
    is_active: bool = True

class SocialOstracismEngine:
    """Manages community pariah status, social shunning, and merchant trade refusal."""

    def __init__(self):
        self.active_orders: Dict[str, OstracismOrder] = {}  # target_npc_id -> OstracismOrder

    def issue_ostracism(
        self,
        target_npc: NPC,
        taboo: TabooType,
        reason: str,
        current_tick: int
    ) -> OstracismOrder:
        order = OstracismOrder(
            target_npc_id=target_npc.id,
            taboo=taboo,
            reason=reason,
            severity_stigma=75.0,
            issued_tick=current_tick,
            is_active=True
        )
        self.active_orders[target_npc.id] = order
        target_npc.social_profile["is_shunned"] = True
        target_npc.adjust_feeling("loneliness", 50.0)
        target_npc.adjust_feeling("stress", 40.0)
        return order

    def is_shunned(self, npc_id: str) -> bool:
        order = self.active_orders.get(npc_id)
        return order is not None and order.is_active

    def calculate_merchant_markup(self, customer_npc_id: str, base_price: float) -> float:
        """Shunned citizens face severe 50% price gouging from merchants."""
        if self.is_shunned(customer_npc_id):
            return round(base_price * 1.5, 2)
        return base_price

    def enforce_social_shun(self, shunner: NPC, target: NPC) -> Dict[str, Any]:
        """A law-abiding citizen turns their back on a shunned pariah, refusing conversation."""
        if not self.is_shunned(target.id):
            return {"shunned": False, "reason": "Target is not ostracized"}

        target.adjust_feeling("loneliness", 15.0)
        target.adjust_feeling("resentment", 15.0)
        shunner.adjust_feeling("pride", 5.0)

        return {
            "shunned": True,
            "shunner_id": shunner.id,
            "target_id": target.id,
            "target_loneliness": target.get_feeling("loneliness")
        }

    def grant_reconciliation(self, target_npc: NPC, penance_gold: float = 50.0) -> bool:
        """Public atonement or debt settlement lifts the ostracism order."""
        if target_npc.id in self.active_orders:
            order = self.active_orders[target_npc.id]
            order.is_active = False
            target_npc.social_profile["is_shunned"] = False
            target_npc.adjust_feeling("loneliness", -40.0)
            target_npc.adjust_feeling("contentment", 30.0)
            return True
        return False


class ViceEscapismDen:
    """Underground gambling and narcotics den where desperate or hedonistic NPCs escape reality."""

    @staticmethod
    def indulge_lotus_resin(
        npc: NPC,
        resin_item: ItemInstance
    ) -> Dict[str, Any]:
        """Consumes illicit lotus resin: drastically blunts stress and grief, but increases addiction dependence."""
        if resin_item.item_def_id != "contraband_lotus_resin":
            return {"success": False, "reason": "Not lotus resin"}

        if resin_item in npc.inventory:
            npc.inventory.remove(resin_item)

        # High psychological escapism
        npc.adjust_feeling("stress", -45.0)
        npc.adjust_feeling("grief", -35.0)
        npc.adjust_feeling("contentment", 25.0)
        npc.needs["energy"] = max(0.0, npc.needs.get("energy", 50.0) - 25.0)

        # Vice addiction increase
        npc.vices["alcohol_dependence"] = min(100.0, npc.vices.get("alcohol_dependence", 0.0) + 5.0)
        npc.vices["vice_indulgence"] = min(100.0, npc.vices.get("vice_indulgence", 0.0) + 10.0)

        return {
            "success": True,
            "npc_id": npc.id,
            "stress_after": npc.get_feeling("stress"),
            "grief_after": npc.get_feeling("grief"),
            "vice_indulgence": npc.vices["vice_indulgence"]
        }

    @staticmethod
    def gamble_underground(
        gambler: NPC,
        gambling_pit: InteractiveObject,
        wager_gold: float = 20.0,
        loaded_dice: Optional[ItemInstance] = None,
        random_roll: float = 0.5
    ) -> Dict[str, Any]:
        """High-stakes illicit dice gambling with loaded dice cheating capability."""
        if not gambling_pit.has_capability("illicit_gambling"):
            return {"success": False, "reason": "Object lacks illicit_gambling capability"}

        if gambler.wealth < wager_gold:
            return {"success": False, "reason": "Insufficient wealth to wager"}

        gambler.wealth -= wager_gold
        has_loaded_dice = loaded_dice is not None and loaded_dice.item_def_id == "item_loaded_dice"
        win_threshold = 0.35 if has_loaded_dice else 0.55

        won = random_roll >= win_threshold
        winnings = 0.0

        if won:
            winnings = wager_gold * 2.0
            gambler.wealth += winnings
            gambler.adjust_feeling("pride", 25.0)
            gambler.adjust_feeling("contentment", 20.0)
        else:
            gambler.adjust_feeling("resentment", 20.0)
            gambler.adjust_feeling("stress", 15.0)

        gambler.vices["gambling_drive"] = min(100.0, gambler.vices.get("gambling_drive", 0.0) + 4.0)

        return {
            "success": True,
            "won": won,
            "wager_gold": wager_gold,
            "winnings": winnings,
            "net_profit": winnings - wager_gold,
            "cheat_used": has_loaded_dice,
            "current_wealth": gambler.wealth
        }
