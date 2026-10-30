"""
Credit Instruments, Promissory Notes, Tally Stick IOUs, and Guild Cartel Price-Fixing.
Models informal credit expansion, negotiable secondary debt trading, cartel price floors, and scavenger undercutting.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.item import ItemInstance


@dataclass
class CreditNoteRecord:
    note_id: str
    debtor_id: str
    original_creditor_id: str
    current_holder_id: str
    principal_gold: float
    interest_rate: float
    issued_tick: int
    is_settled: bool = False
    is_defaulted: bool = False


class CreditInstrumentManager:
    """Manages creation, circulation, secondary market discounting, and redemption of debt instruments."""

    def __init__(self, credit_config: Optional[Dict[str, Any]] = None):
        cfg = (credit_config or {}).get("credit_system", {})
        self.instruments_cfg = cfg.get("instruments", {})
        self.limits_by_class = cfg.get("credit_limits_by_social_class", {
            "PATRICIAN": 600.0,
            "BURGHER": 300.0,
            "COMMONER": 100.0,
            "INDENTURED": 25.0,
            "OUTCAST": 0.0
        })
        self.secondary_discount = cfg.get("secondary_debt_discount_factor", 0.80)
        self.default_stigma = cfg.get("default_stigma_penalty", 35.0)
        self.active_notes: Dict[str, CreditNoteRecord] = {}

    def issue_promissory_note(
        self,
        debtor: NPC,
        creditor: NPC,
        amount: float,
        current_tick: int,
        instrument_type: str = "item_promissory_note"
    ) -> Dict[str, Any]:
        social_class = debtor.social_profile.get("social_class", "COMMONER")
        credit_limit = self.limits_by_class.get(social_class, 100.0)

        # Check existing debt
        current_debt = sum(n.principal_gold for n in self.active_notes.values() if n.debtor_id == debtor.id and not n.is_settled)
        if current_debt + amount > credit_limit:
            return {"success": False, "reason": "Credit limit exceeded for debtor social class."}

        note_id = f"note_{uuid.uuid4().hex[:8]}"
        record = CreditNoteRecord(
            note_id=note_id,
            debtor_id=debtor.id,
            original_creditor_id=creditor.id,
            current_holder_id=creditor.id,
            principal_gold=amount,
            interest_rate=0.05 if "promissory" in instrument_type else 0.03,
            issued_tick=current_tick
        )
        self.active_notes[note_id] = record

        # Create physical item instance in creditor inventory
        item_inst = ItemInstance(
            instance_id=note_id,
            item_def_id=instrument_type,
            freshness=100.0,
            durability=100.0,
            quality=1.0,
            owner_id=creditor.id,
            metadata={
                "note_id": note_id,
                "debtor_id": debtor.id,
                "principal_gold": amount,
                "interest_rate": record.interest_rate
            }
        )
        creditor.inventory.append(item_inst)

        # Transfer credit gold to debtor
        creditor.wealth -= amount
        debtor.wealth += amount
        debtor.adjust_feeling("contentment", 15.0)
        debtor.adjust_feeling("stress", -10.0)

        return {
            "success": True,
            "note_id": note_id,
            "debtor_id": debtor.id,
            "creditor_id": creditor.id,
            "amount": amount,
            "instrument_type": instrument_type
        }

    def trade_secondary_debt(
        self,
        seller: NPC,
        buyer: NPC,
        note_instance: ItemInstance
    ) -> Dict[str, Any]:
        """Sells an existing debt instrument to a third party at a secondary market discount."""
        if note_instance not in seller.inventory:
            return {"success": False, "reason": "Note not in seller possession"}

        note_id = note_instance.metadata.get("note_id")
        record = self.active_notes.get(note_id)
        if not record or record.is_settled or record.is_defaulted:
            return {"success": False, "reason": "Invalid or inactive debt instrument"}

        discounted_price = round(record.principal_gold * self.secondary_discount, 2)
        if buyer.wealth < discounted_price:
            return {"success": False, "reason": "Buyer has insufficient funds for discounted IOU"}

        # Execute transaction
        buyer.wealth -= discounted_price
        seller.wealth += discounted_price

        seller.inventory.remove(note_instance)
        buyer.inventory.append(note_instance)
        note_instance.owner_id = buyer.id
        record.current_holder_id = buyer.id

        seller.adjust_feeling("contentment", 10.0)
        buyer.adjust_feeling("pride", 15.0)

        return {
            "success": True,
            "note_id": note_id,
            "face_value": record.principal_gold,
            "discounted_price": discounted_price,
            "seller_id": seller.id,
            "buyer_id": buyer.id
        }

    def redeem_debt(
        self,
        debtor: NPC,
        holder: NPC,
        note_instance: ItemInstance
    ) -> Dict[str, Any]:
        """Debtor repays principal plus interest, redeeming and canceling the note."""
        note_id = note_instance.metadata.get("note_id")
        record = self.active_notes.get(note_id)
        if not record or record.is_settled:
            return {"success": False, "reason": "Note is already settled"}

        total_due = round(record.principal_gold * (1.0 + record.interest_rate), 2)
        if debtor.wealth < total_due:
            # Default!
            record.is_defaulted = True
            debtor.adjust_feeling("stress", 35.0)
            debtor.adjust_feeling("guilt", 25.0)
            if hasattr(debtor, "adjust_moral_erosion"):
                debtor.adjust_moral_erosion(10.0)
            return {
                "success": False,
                "reason": "Debtor defaulted due to insufficient wealth",
                "defaulted": True,
                "total_due": total_due
            }

        debtor.wealth -= total_due
        holder.wealth += total_due
        record.is_settled = True

        if note_instance in holder.inventory:
            holder.inventory.remove(note_instance)

        debtor.adjust_feeling("contentment", 25.0)
        debtor.adjust_feeling("stress", -20.0)
        holder.adjust_feeling("contentment", 20.0)

        return {
            "success": True,
            "note_id": note_id,
            "settled": True,
            "amount_paid": total_due,
            "debtor_id": debtor.id,
            "holder_id": holder.id
        }

    def process_daily_credit_checks(self, npcs: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
        audited_count = len(self.active_notes)
        defaulted_count = 0
        for note_id, record in self.active_notes.items():
            if not record.is_settled and not record.is_defaulted:
                if current_tick - record.created_tick > 4320:
                    debtor = npcs.get(record.debtor_id)
                    total_due = round(record.principal_gold * (1.0 + record.interest_rate), 2)
                    if debtor and debtor.wealth < total_due:
                        record.is_defaulted = True
                        defaulted_count += 1
                        debtor.adjust_feeling("stress", 20.0)
                        debtor.adjust_feeling("guilt", 15.0)
        return {
            "audited_notes": audited_count,
            "defaulted_notes": defaulted_count,
            "tick": current_tick
        }


class GuildCartelManager:
    """Enforces cartel price floors, fines guild members who undercut, and tracks black market sales."""

    def __init__(self, guild_config: Optional[Dict[str, Any]] = None):
        cfg = (guild_config or {}).get("guild_monopolies", {})
        self.guilds = cfg.get("guilds", {})
        self.scavenger_discount = cfg.get("scavenger_black_market_discount", 0.30)
        self.violations: List[Dict[str, Any]] = []

    def get_guild_for_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        for g in self.guilds.values():
            if item_id in g.get("price_floors", {}):
                return g
        return None

    def evaluate_sale_price(
        self,
        seller: NPC,
        item_id: str,
        offered_price: float,
        current_tick: int
    ) -> Dict[str, Any]:
        guild = self.get_guild_for_item(item_id)
        if not guild:
            return {"is_restricted": False, "compliant": True}

        floor = guild["price_floors"][item_id]
        is_member = seller.id in guild.get("member_ids", [])

        if offered_price < floor:
            if is_member:
                fine = guild.get("undercut_fine", 30.0)
                seller.wealth = max(0.0, seller.wealth - fine)
                seller.adjust_feeling("stress", 20.0)
                seller.adjust_feeling("resentment", 15.0)
                violation = {
                    "guild_id": guild["id"],
                    "violator_id": seller.id,
                    "item_id": item_id,
                    "floor_price": floor,
                    "offered_price": offered_price,
                    "fine_levied": fine,
                    "tick": current_tick
                }
                self.violations.append(violation)
                return {
                    "is_restricted": True,
                    "compliant": False,
                    "is_guild_member": True,
                    "fine_levied": fine,
                    "floor_price": floor
                }
            else:
                # Non-guild scavenger undercutting on the black market!
                return {
                    "is_restricted": True,
                    "compliant": False,
                    "is_guild_member": False,
                    "black_market_undercut": True,
                    "floor_price": floor
                }

        return {"is_restricted": True, "compliant": True, "floor_price": floor}
