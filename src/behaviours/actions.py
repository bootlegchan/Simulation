"""
Expanded Action Registry & Behavioral Capabilities Engine.
Supports physical intimacy, domestic living, sentimental heirlooms,
illicit clandestine operations, and vibrant social community life.
Updates NPC needs, feelings, and social relationships dynamically.
"""
from typing import Any, Dict, List, Optional
import uuid

from src.entities.npc import NPC
from src.entities.item import ItemInstance
from src.entities.object import InteractiveObject
from src.society.romance import InterpersonalBond, RelationshipStage, AgreementType, AffectionStyle

class ActionRegistry:
    """Registry of comprehensive NPC actions, capabilities, and emotional reactions."""

    # ---------------------------------------------------------
    # 1. CORE SURVIVAL & ECONOMIC ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def eat(npc: NPC, item_instance: ItemInstance) -> bool:
        if item_instance in npc.inventory:
            npc.inventory.remove(item_instance)
            food_val = 40.0
            if "spiced_cider" in item_instance.item_def_id:
                food_val = 30.0
                npc.adjust_feeling("contentment", 20.0)
                npc.adjust_feeling("stress", -15.0)
            elif "roast_pig" in item_instance.item_def_id:
                food_val = 80.0
                npc.adjust_feeling("contentment", 35.0)
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - food_val)
            return True
        return False

    @staticmethod
    def sleep(npc: NPC) -> bool:
        npc.needs["energy"] = min(100.0, npc.needs.get("energy", 0.0) + 50.0)
        npc.adjust_feeling("stress", -10.0)
        return True

    @staticmethod
    def work(npc: NPC) -> float:
        earned = 15.0
        npc.wealth += earned
        npc.needs["energy"] = max(0.0, npc.needs.get("energy", 0.0) - 20.0)
        npc.adjust_feeling("contentment", 5.0)
        return earned

    @staticmethod
    def steal(thief: NPC, victim: NPC, item_instance: ItemInstance) -> bool:
        if item_instance in victim.inventory:
            victim.inventory.remove(item_instance)
            item_instance.owner_id = thief.id
            thief.inventory.append(item_instance)
            thief.adjust_feeling("pride", 10.0)
            victim.adjust_feeling("resentment", 30.0)
            return True
        return False

    @staticmethod
    def bribe(briber: NPC, official: NPC, amount: float) -> bool:
        if briber.wealth >= amount:
            briber.wealth -= amount
            official.wealth += amount
            briber.adjust_feeling("guilt", 15.0)
            official.adjust_feeling("guilt", 20.0)
            return True
        return False

    # ---------------------------------------------------------
    # 2. PHYSICAL INTIMACY & COURTSHIP ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def court_with_gift(
        suitor: NPC,
        target: NPC,
        gift_item: ItemInstance,
        bond: Optional[InterpersonalBond] = None,
        social_network: Any = None
    ) -> Dict[str, Any]:
        """Court a target NPC with a gift bouquet, pendant, or keepsake."""
        if gift_item not in suitor.inventory:
            return {"success": False, "reason": "Gift item not in inventory"}

        suitor.inventory.remove(gift_item)
        target.inventory.append(gift_item)
        gift_item.owner_id = target.id

        # Emotional feeling updates
        suitor.adjust_feeling("tenderness", 20.0)
        suitor.adjust_feeling("loneliness", -20.0)
        suitor.adjust_feeling("pride", 15.0)

        target.adjust_feeling("tenderness", 25.0)
        target.adjust_feeling("loneliness", -20.0)
        target.adjust_feeling("contentment", 20.0)

        # Update romance bond if present
        if bond:
            bond.romantic_affection = min(100.0, bond.romantic_affection + 25.0)
            bond.trust = min(100.0, bond.trust + 15.0)
            if bond.stage in (RelationshipStage.STRANGER, RelationshipStage.ACQUAINTANCE, RelationshipStage.FRIEND):
                bond.stage = RelationshipStage.COURTING

        if social_network and hasattr(social_network, "get_bond"):
            rel = social_network.get_bond(target.id, suitor.id)
            rel.adjust_axis("romantic_affection", 25.0)
            rel.adjust_axis("trust", 15.0)

        return {
            "success": True,
            "action": "COURT_WITH_GIFT",
            "suitor_id": suitor.id,
            "target_id": target.id,
            "gift_item_id": gift_item.item_def_id,
            "target_tenderness": target.get_feeling("tenderness"),
        }

    @staticmethod
    def execute_private_intimacy(
        actor: NPC,
        partner: NPC,
        bond: Optional[InterpersonalBond] = None,
        canopy_bed: Optional[InteractiveObject] = None,
        room_privacy: float = 80.0,
        current_tick: int = 0
    ) -> Dict[str, Any]:
        """
        Executes high-privacy romantic bonding and physical intimacy.
        Surges passion and tenderness while eliminating loneliness and stress.
        """
        effective_privacy = room_privacy
        if canopy_bed and canopy_bed.has_capability("private_intimacy"):
            effective_privacy = min(100.0, effective_privacy + 25.0)

        if effective_privacy < 60.0:
            actor.adjust_feeling("stress", 15.0)
            partner.adjust_feeling("stress", 15.0)
            return {"success": False, "reason": "Insufficient privacy for intimate bonding"}

        # Deep feeling transformations
        actor.adjust_feeling("passion", 35.0)
        partner.adjust_feeling("passion", 35.0)
        actor.adjust_feeling("tenderness", 30.0)
        partner.adjust_feeling("tenderness", 30.0)
        actor.adjust_feeling("contentment", 30.0)
        partner.adjust_feeling("contentment", 30.0)

        actor.adjust_feeling("stress", -30.0)
        partner.adjust_feeling("stress", -30.0)
        actor.set_feeling("loneliness", 0.0)
        partner.set_feeling("loneliness", 0.0)

        # Need fulfillment
        actor.needs["social"] = min(100.0, actor.needs.get("social", 50.0) + 35.0)
        partner.needs["social"] = min(100.0, partner.needs.get("social", 50.0) + 35.0)

        # Relationship stage progression
        stage_advanced = False
        if bond:
            bond.romantic_affection = min(100.0, bond.romantic_affection + 20.0)
            bond.trust = min(100.0, bond.trust + 15.0)
            if bond.stage == RelationshipStage.COURTING and bond.romantic_affection >= 75.0:
                bond.stage = RelationshipStage.LOVERS
                stage_advanced = True

        return {
            "success": True,
            "action": "PRIVATE_INTIMACY",
            "actor_id": actor.id,
            "partner_id": partner.id,
            "effective_privacy": effective_privacy,
            "stage_advanced": stage_advanced,
            "actor_passion": actor.get_feeling("passion"),
            "actor_tenderness": actor.get_feeling("tenderness"),
        }

    @staticmethod
    def comfort_partner(
        actor: NPC,
        partner: NPC,
        bond: Optional[InterpersonalBond] = None,
        soothing_balm: Optional[ItemInstance] = None
    ) -> Dict[str, Any]:
        """Provides physical comfort and emotional reassurance to a stressed or grieving partner."""
        balm_applied = False
        if soothing_balm and soothing_balm in actor.inventory:
            actor.inventory.remove(soothing_balm)
            balm_applied = True

        grief_reduction = 35.0 if balm_applied else 20.0
        stress_reduction = 30.0 if balm_applied else 20.0

        partner.adjust_feeling("grief", -grief_reduction)
        partner.adjust_feeling("stress", -stress_reduction)
        partner.adjust_feeling("tenderness", 25.0)
        actor.adjust_feeling("tenderness", 25.0)
        actor.adjust_feeling("contentment", 20.0)

        if bond:
            bond.trust = min(100.0, bond.trust + 15.0)

        return {
            "success": True,
            "action": "COMFORT_PARTNER",
            "actor_id": actor.id,
            "partner_id": partner.id,
            "balm_applied": balm_applied,
            "partner_grief": partner.get_feeling("grief"),
            "partner_stress": partner.get_feeling("stress"),
        }

    @staticmethod
    def public_affection_display(
        actor: NPC,
        partner: NPC,
        bond: Optional[InterpersonalBond],
        onlookers: List[NPC],
        social_network: Any = None,
        spouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Displays public romance (hand-holding, walking together). Can trigger acute jealousy if with an affair partner."""
        actor.adjust_feeling("pride", 15.0)
        partner.adjust_feeling("pride", 15.0)
        actor.adjust_feeling("contentment", 15.0)
        partner.adjust_feeling("contentment", 15.0)

        jealous_witness_ids = []
        if spouse_id and any(o.id == spouse_id for o in onlookers):
            for o in onlookers:
                if o.id == spouse_id:
                    o.adjust_feeling("jealousy", 65.0)
                    o.adjust_feeling("resentment", 50.0)
                    o.adjust_feeling("stress", 35.0)
                    jealous_witness_ids.append(o.id)
                    if social_network and hasattr(social_network, "get_bond"):
                        rel = social_network.get_bond(o.id, actor.id)
                        rel.adjust_axis("trust", -45.0)
                        rel.adjust_axis("respect", -35.0)

        return {
            "success": True,
            "action": "PUBLIC_AFFECTION_DISPLAY",
            "actor_id": actor.id,
            "partner_id": partner.id,
            "jealous_witnesses": jealous_witness_ids,
        }

    # ---------------------------------------------------------
    # 3. DOMESTIC & PERSONAL LIVING ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def gather_at_family_hearth(
        members: List[NPC],
        hearth: InteractiveObject,
        shared_food: Optional[ItemInstance] = None
    ) -> Dict[str, Any]:
        """Family members gather around the carved stone hearth for warmth, dining, and conversation."""
        if not hearth.has_capability("family_gathering"):
            return {"success": False, "reason": "Object lacks family_gathering capability"}

        food_shared = False
        if shared_food:
            food_shared = True

        for m in members:
            m.adjust_feeling("contentment", 25.0)
            m.adjust_feeling("loneliness", -25.0)
            m.adjust_feeling("stress", -15.0)
            m.needs["social"] = min(100.0, m.needs.get("social", 50.0) + 20.0)
            if food_shared:
                m.needs["hunger"] = max(0.0, m.needs.get("hunger", 0.0) - 25.0)

        return {
            "success": True,
            "action": "GATHER_AT_FAMILY_HEARTH",
            "members_count": len(members),
            "food_shared": food_shared,
        }

    @staticmethod
    def write_in_diary(
        npc: NPC,
        writing_desk: InteractiveObject,
        diary_item: ItemInstance,
        entry_text: str,
        current_tick: int
    ) -> Dict[str, Any]:
        """Writes private reflections and secrets in a bound personal diary."""
        if not writing_desk.has_capability("write_diary"):
            return {"success": False, "reason": "Writing desk lacks write_diary capability"}

        npc.adjust_feeling("stress", -20.0)
        npc.adjust_feeling("contentment", 15.0)
        npc.adjust_feeling("loneliness", -10.0)

        entries = diary_item.metadata.setdefault("diary_entries", [])
        entries.append({
            "tick": current_tick,
            "author_id": npc.id,
            "text": entry_text,
        })

        return {
            "success": True,
            "action": "WRITE_IN_DIARY",
            "npc_id": npc.id,
            "entries_total": len(entries),
            "stress_after": npc.get_feeling("stress"),
        }

    @staticmethod
    def inspect_family_heirloom(npc: NPC, heirloom: ItemInstance) -> Dict[str, Any]:
        """Inspects and cherishes an ancestral signet ring, silver locket, or heirloom."""
        if heirloom not in npc.inventory:
            return {"success": False, "reason": "Heirloom not in inventory"}

        npc.adjust_feeling("pride", 25.0)
        npc.adjust_feeling("grief", -20.0)
        npc.adjust_feeling("loneliness", -15.0)
        npc.adjust_feeling("contentment", 15.0)

        return {
            "success": True,
            "action": "INSPECT_FAMILY_HEIRLOOM",
            "npc_id": npc.id,
            "heirloom_id": heirloom.item_def_id,
            "pride_after": npc.get_feeling("pride"),
        }

    @staticmethod
    def snoop_private_chest(
        intruder: NPC,
        owner: NPC,
        chest: InteractiveObject,
        witness_ids: List[str],
        lockpicks: Optional[ItemInstance] = None,
        social_network: Any = None
    ) -> Dict[str, Any]:
        """Attempts to pick or open another character's locked chest to discover diaries or heirlooms."""
        if chest.is_locked and not lockpicks:
            return {"success": False, "reason": "Chest is locked and intruder has no lockpicks"}

        is_witnessed = len(witness_ids) > 0
        if is_witnessed:
            intruder.adjust_feeling("guilt", 30.0)
            owner.adjust_feeling("resentment", 50.0)
            if social_network and hasattr(social_network, "get_bond"):
                rel = social_network.get_bond(owner.id, intruder.id)
                rel.adjust_axis("trust", -50.0)
                rel.adjust_axis("respect", -30.0)

            return {
                "success": False,
                "reason": "Caught snooping by witnesses!",
                "witness_ids": witness_ids,
                "owner_resentment": owner.get_feeling("resentment"),
            }

        intruder.adjust_feeling("pride", 20.0)
        return {
            "success": True,
            "action": "SNOOP_PRIVATE_CHEST",
            "intruder_id": intruder.id,
            "chest_id": chest.id,
            "is_witnessed": False,
        }

    # ---------------------------------------------------------
    # 4. ILLICIT INTRIGUE & UNDERWORLD ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def clandestine_rendezvous(
        lover_a: NPC,
        lover_b: NPC,
        secluded_location_id: str,
        eavesdropper_ids: List[NPC]
    ) -> Dict[str, Any]:
        """Secret meeting between clandestine lovers. Risk of generating blackmail hooks if overheard."""
        lover_a.adjust_feeling("passion", 40.0)
        lover_b.adjust_feeling("passion", 40.0)
        lover_a.adjust_feeling("guilt", 20.0)
        lover_b.adjust_feeling("guilt", 20.0)

        is_intercepted = len(eavesdropper_ids) > 0
        blackmail_hook_generated = False
        spy_id = None

        if is_intercepted:
            spy = eavesdropper_ids[0]
            spy_id = spy.id
            blackmail_hook_generated = True
            hook_item = ItemInstance(
                instance_id=f"inst_hook_{uuid.uuid4().hex[:8]}",
                item_def_id="letter_blackmail_hook",
                freshness=100.0,
                durability=100.0,
                quality=1.0,
                owner_id=spy.id,
                metadata={
                    "target_a_id": lover_a.id,
                    "target_b_id": lover_b.id,
                    "secret_crime": "CLANDESTINE_AFFAIR",
                    "location_id": secluded_location_id,
                }
            )
            spy.inventory.append(hook_item)
            spy.adjust_feeling("pride", 25.0)

        return {
            "success": True,
            "action": "CLANDESTINE_RENDEZVOUS",
            "lover_a_id": lover_a.id,
            "lover_b_id": lover_b.id,
            "is_intercepted": is_intercepted,
            "spy_id": spy_id,
            "blackmail_hook_generated": blackmail_hook_generated,
        }

    @staticmethod
    def blackmail_extort(
        extortionist: NPC,
        victim: NPC,
        blackmail_letter: ItemInstance,
        demanded_gold: float = 30.0
    ) -> Dict[str, Any]:
        """Uses an incriminating blackmail hook to extort gold and obedience from a victim."""
        if blackmail_letter not in extortionist.inventory:
            return {"success": False, "reason": "Blackmail letter not in possession"}

        paid_gold = min(victim.wealth, demanded_gold)
        victim.wealth -= paid_gold
        extortionist.wealth += paid_gold

        victim.adjust_feeling("stress", 40.0)
        victim.adjust_feeling("resentment", 50.0)
        victim.adjust_feeling("guilt", 30.0)

        extortionist.adjust_feeling("pride", 20.0)
        extortionist.adjust_feeling("guilt", 15.0)

        return {
            "success": True,
            "action": "BLACKMAIL_EXTORT",
            "extortionist_id": extortionist.id,
            "victim_id": victim.id,
            "extorted_gold": paid_gold,
            "victim_stress": victim.get_feeling("stress"),
            "victim_resentment": victim.get_feeling("resentment"),
        }

    @staticmethod
    def distill_moonshine(
        brewer: NPC,
        still: InteractiveObject,
        wheat_instance: ItemInstance,
        ale_instance: ItemInstance
    ) -> Optional[ItemInstance]:
        """Distills illicit high-proof moonshine using a hidden copper still."""
        if not still.has_capability("distill_spirits"):
            return None

        if wheat_instance in brewer.inventory and ale_instance in brewer.inventory:
            brewer.inventory.remove(wheat_instance)
            brewer.inventory.remove(ale_instance)

            moonshine = ItemInstance(
                instance_id=f"inst_moonshine_{uuid.uuid4().hex[:8]}",
                item_def_id="contraband_moonshine",
                freshness=100.0,
                durability=100.0,
                quality=1.2,
                owner_id=brewer.id,
            )
            brewer.inventory.append(moonshine)
            brewer.adjust_feeling("pride", 15.0)
            return moonshine
        return None

    # ---------------------------------------------------------
    # 5. COMMUNITY & SOCIAL GATHERING ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def perform_at_tavern_stage(
        bard: NPC,
        stage: InteractiveObject,
        audience: List[NPC]
    ) -> Dict[str, Any]:
        """Bard performs musical ballads on the tavern stage, lifting community spirits and gathering tips."""
        if not stage.has_capability("bard_performance"):
            return {"success": False, "reason": "Stage lacks bard_performance capability"}

        total_tips = 0.0
        for listener in audience:
            listener.adjust_feeling("contentment", 25.0)
            listener.adjust_feeling("stress", -20.0)
            listener.adjust_feeling("loneliness", -25.0)
            listener.needs["social"] = min(100.0, listener.needs.get("social", 50.0) + 25.0)

            # Tip bard if wealthy enough
            if listener.wealth >= 5.0:
                tip = 2.0
                listener.wealth -= tip
                total_tips += tip

        bard.wealth += total_tips
        bard.adjust_feeling("pride", 30.0)
        bard.adjust_feeling("contentment", 25.0)

        return {
            "success": True,
            "action": "PERFORM_AT_TAVERN_STAGE",
            "bard_id": bard.id,
            "audience_size": len(audience),
            "total_tips": total_tips,
        }

    @staticmethod
    def toast_and_carouse(
        patrons: List[NPC],
        drink_item: Optional[ItemInstance] = None
    ) -> Dict[str, Any]:
        """Tavern patrons raise their cups in a collective toast, bonding over drinks."""
        for p in patrons:
            p.adjust_feeling("contentment", 20.0)
            p.adjust_feeling("stress", -15.0)
            p.adjust_feeling("loneliness", -20.0)
            p.needs["social"] = min(100.0, p.needs.get("social", 50.0) + 20.0)

        return {
            "success": True,
            "action": "TOAST_AND_CAROUSE",
            "patrons_count": len(patrons),
        }

    # ---------------------------------------------------------
    # 6. DIVERSE RELATIONSHIP, STROLL & COLLABORATIVE INTIMACY ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def couple_stroll(
        lead_npc: NPC,
        partner_npc: NPC,
        bond: Optional[InterpersonalBond] = None,
        destination_location_id: str = "room_village_square",
        current_tick: int = 0
    ) -> Dict[str, Any]:
        """
        Couples walk synchronized arm-in-arm through the settlement, signaling bonded status.
        Fulfills physical presence affection styles, lowers stress, and restores contentment.
        """
        lead_npc.location_id = destination_location_id
        partner_npc.location_id = destination_location_id
        lead_npc.current_state = "COUPLE_STROLLING"
        partner_npc.current_state = "COUPLE_STROLLING"

        lead_npc.adjust_feeling("contentment", 20.0)
        partner_npc.adjust_feeling("contentment", 20.0)
        lead_npc.adjust_feeling("tenderness", 15.0)
        partner_npc.adjust_feeling("tenderness", 15.0)
        lead_npc.adjust_feeling("loneliness", -30.0)
        partner_npc.adjust_feeling("loneliness", -30.0)
        lead_npc.adjust_feeling("stress", -15.0)
        partner_npc.adjust_feeling("stress", -15.0)

        # Needs
        lead_npc.needs["social"] = min(100.0, lead_npc.needs.get("social", 50.0) + 25.0)
        partner_npc.needs["social"] = min(100.0, partner_npc.needs.get("social", 50.0) + 25.0)

        if bond:
            bond.romantic_affection = min(100.0, bond.romantic_affection + 10.0)
            bond.trust = min(100.0, bond.trust + 5.0)

        return {
            "success": True,
            "action": "COUPLE_STROLL",
            "lead_id": lead_npc.id,
            "partner_id": partner_npc.id,
            "location_id": destination_location_id,
            "lead_contentment": lead_npc.get_feeling("contentment"),
            "partner_contentment": partner_npc.get_feeling("contentment"),
            "tick": current_tick,
        }

    @staticmethod
    def cooperative_work_task(
        worker_a: NPC,
        worker_b: NPC,
        task_type: str = "COOPERATIVE_COOKING",
        station_object: Optional[InteractiveObject] = None,
        bond: Optional[InterpersonalBond] = None
    ) -> Dict[str, Any]:
        """
        Shared domestic or economic task (cooperative cooking, hearth maintenance, workshop assistance).
        Reduces energy exertion through teamwork efficiency and strengthens mutual bond.
        """
        energy_cost = 10.0
        worker_a.needs["energy"] = max(0.0, worker_a.needs.get("energy", 50.0) - energy_cost)
        worker_b.needs["energy"] = max(0.0, worker_b.needs.get("energy", 50.0) - energy_cost)

        worker_a.needs["social"] = min(100.0, worker_a.needs.get("social", 50.0) + 15.0)
        worker_b.needs["social"] = min(100.0, worker_b.needs.get("social", 50.0) + 15.0)

        worker_a.adjust_feeling("contentment", 20.0)
        worker_b.adjust_feeling("contentment", 20.0)
        worker_a.adjust_feeling("tenderness", 15.0)
        worker_b.adjust_feeling("tenderness", 15.0)
        worker_a.adjust_feeling("loneliness", -20.0)
        worker_b.adjust_feeling("loneliness", -20.0)

        if bond:
            bond.trust = min(100.0, bond.trust + 8.0)
            bond.respect = min(100.0, bond.respect + 10.0)

        return {
            "success": True,
            "action": "COOPERATIVE_WORK_TASK",
            "task_type": task_type,
            "worker_a_id": worker_a.id,
            "worker_b_id": worker_b.id,
            "station_id": station_object.id if station_object else None,
            "teamwork_efficiency_bonus": 0.25,
            "mutual_contentment": worker_a.get_feeling("contentment"),
        }

    @staticmethod
    def flirt_and_tease(
        actor: NPC,
        target: NPC,
        bond: Optional[InterpersonalBond] = None,
        is_playful: bool = True
    ) -> Dict[str, Any]:
        """
        Playful flirting, witty banter, and complimentary affection in public or social venues.
        """
        actor.adjust_feeling("passion", 15.0)
        actor.adjust_feeling("loneliness", -15.0)
        actor.adjust_feeling("pride", 10.0)
        actor.adjust_feeling("stress", -10.0)

        target.adjust_feeling("passion", 12.0)
        target.adjust_feeling("loneliness", -15.0)
        target.adjust_feeling("contentment", 15.0)

        actor.needs["social"] = min(100.0, actor.needs.get("social", 50.0) + 20.0)
        target.needs["social"] = min(100.0, target.needs.get("social", 50.0) + 20.0)

        if bond:
            bond.physical_attraction = min(100.0, bond.physical_attraction + 8.0)
            bond.romantic_affection = min(100.0, bond.romantic_affection + 12.0)
            if bond.stage == RelationshipStage.ACQUAINTANCE:
                bond.stage = RelationshipStage.CRUSH

        return {
            "success": True,
            "action": "FLIRT_AND_TEASE",
            "actor_id": actor.id,
            "target_id": target.id,
            "is_playful": is_playful,
            "actor_passion": actor.get_feeling("passion"),
            "target_passion": target.get_feeling("passion"),
        }

    @staticmethod
    def discuss_relationship_boundaries(
        actor: NPC,
        partner: NPC,
        bond: InterpersonalBond,
        proposed_agreement: AgreementType,
        boundaries: List[str]
    ) -> Dict[str, Any]:
        """
        Communicative negotiation of relationship agreements (monogamy, polyamory, platonic cohabitation)
        and declared boundary rules. Strengthens trust and resolves anxiety.
        """
        disc_res = bond.discuss_boundaries(proposed_agreement, boundaries)

        actor.adjust_feeling("contentment", 20.0)
        partner.adjust_feeling("contentment", 20.0)
        actor.adjust_feeling("stress", -20.0)
        partner.adjust_feeling("stress", -20.0)
        actor.adjust_feeling("jealousy", -30.0)
        partner.adjust_feeling("jealousy", -30.0)

        actor.needs["social"] = min(100.0, actor.needs.get("social", 50.0) + 20.0)
        partner.needs["social"] = min(100.0, partner.needs.get("social", 50.0) + 20.0)

        return {
            "success": True,
            "action": "DISCUSS_BOUNDARIES",
            "actor_id": actor.id,
            "partner_id": partner.id,
            "agreement_type": bond.agreement_type.value,
            "declared_boundaries": bond.declared_boundaries,
            "bond_trust": bond.trust,
        }

    @staticmethod
    def mediate_relationship_conflict(
        mediator: NPC,
        partner_a: NPC,
        partner_b: NPC,
        bond: InterpersonalBond
    ) -> Dict[str, Any]:
        """
        Restorative mediation by a community elder, counselor, or trusted mutual friend.
        Resolves boundary breaches and calms acute jealousy and resentment.
        """
        partner_a.adjust_feeling("resentment", -35.0)
        partner_b.adjust_feeling("resentment", -35.0)
        partner_a.adjust_feeling("jealousy", -30.0)
        partner_b.adjust_feeling("jealousy", -30.0)
        partner_a.adjust_feeling("contentment", 20.0)
        partner_b.adjust_feeling("contentment", 20.0)

        bond.trust = min(100.0, bond.trust + 25.0)
        bond.respect = min(100.0, bond.respect + 20.0)

        return {
            "success": True,
            "action": "MEDIATE_CONFLICT",
            "mediator_id": mediator.id,
            "partner_a_id": partner_a.id,
            "partner_b_id": partner_b.id,
            "restored_trust": bond.trust,
            "partner_a_resentment": partner_a.get_feeling("resentment"),
            "partner_b_resentment": partner_b.get_feeling("resentment"),
        }

    # ---------------------------------------------------------
    # 7. CLANDESTINE CULTS, SURVIVAL INDENTURE & SCANDAL ACTIONS
    # ---------------------------------------------------------

    @staticmethod
    def conduct_cult_rite(
        cult: Any,
        participants: List[NPC],
        altar_obj: InteractiveObject,
        occult_tome_item: Optional[ItemInstance] = None,
        current_tick: int = 0
    ) -> Dict[str, Any]:
        """Executes a clandestine cult ceremony at the subterranean altar."""
        from src.society.cults import CultRiteEngine
        return CultRiteEngine.conduct_esoteric_rite(
            cult=cult,
            participants=participants,
            altar_obj=altar_obj,
            occult_tome_item=occult_tome_item,
            current_tick=current_tick
        )

    @staticmethod
    def issue_indenture_bond(
        indenture_mgr: Any,
        debtor: NPC,
        master: NPC,
        debt_amount: float,
        current_tick: int = 0
    ) -> Dict[str, Any]:
        """Binds a destitute debtor to a master under debt peonage."""
        contract = indenture_mgr.issue_indenture(debtor, master, debt_amount, current_tick)
        return {
            "success": True,
            "action": "ISSUE_INDENTURE",
            "contract_id": contract.contract_id,
            "debtor_id": debtor.id,
            "master_id": master.id,
            "debt_amount": debt_amount,
            "debtor_pride": debtor.get_feeling("pride"),
        }

    @staticmethod
    def garnish_indentured_wages(
        indenture_mgr: Any,
        contract_id: str,
        earned_wage: float,
        debtor: NPC,
        master: NPC
    ) -> Dict[str, Any]:
        """Transfers garnished wages from debtor to master to pay down debt bond."""
        return indenture_mgr.process_wage_garnishment(contract_id, earned_wage, debtor, master)

    @staticmethod
    def fence_contraband_or_stolen(
        thief: NPC,
        broker_counter: InteractiveObject,
        stolen_item: ItemInstance,
        item_base_value: float
    ) -> Dict[str, Any]:
        """Fences an illicit item into laundered currency through a shadow broker."""
        from src.economy.indenture import ContrabandFencingRing
        return ContrabandFencingRing.fence_stolen_item(thief, broker_counter, stolen_item, item_base_value)

    @staticmethod
    def indulge_vice_den(
        npc: NPC,
        den_action_type: str,
        item_or_object: Any,
        wager_gold: float = 20.0,
        random_roll: float = 0.5
    ) -> Dict[str, Any]:
        """Escapes reality in an underground vice den via lotus resin or illicit dice gambling."""
        from src.society.scandals_and_taboos import ViceEscapismDen
        if den_action_type == "CONSUME_LOTUS_RESIN":
            return ViceEscapismDen.indulge_lotus_resin(npc, item_or_object)
        elif den_action_type == "GAMBLE_DICE":
            loaded_dice = next((i for i in npc.inventory if i.item_def_id == "item_loaded_dice"), None)
            return ViceEscapismDen.gamble_underground(npc, item_or_object, wager_gold=wager_gold, loaded_dice=loaded_dice, random_roll=random_roll)
        return {"success": False, "reason": "Unknown den action type"}

    @staticmethod
    def enforce_social_ostracism(
        ostracism_engine: Any,
        shunner: NPC,
        target: NPC
    ) -> Dict[str, Any]:
        """Enforces community shunning and pariah status against a taboo violator."""
        return ostracism_engine.enforce_social_shun(shunner, target)

    @staticmethod
    def evaluate_and_trigger_crisis_of_conscience(
        npc: NPC,
        tracker: Any
    ) -> Dict[str, Any]:
        """Evaluates moral dissonance breakdown and self-reporting crisis."""
        from src.npc.moral_erosion import CognitiveDissonanceEngine
        return CognitiveDissonanceEngine.evaluate_dissonance_break(npc, tracker)
