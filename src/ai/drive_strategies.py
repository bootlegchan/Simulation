"""Modular Autonomous Drive Strategies Registry with Relationship-Weighted Social Dynamics & Sales Tax."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.entities.npc import NPC
from src.behaviours.actions import ActionRegistry
from src.economy.intelligent_food_selection import IntelligentFoodSelector, FoodSourceType

class IDriveStrategy(ABC):
    @abstractmethod
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        pass

class HungerDriveStrategy(IDriveStrategy):
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        choice = IntelligentFoodSelector.select_best_option(npc, context, emergency_hunger=False)
        if choice and choice.source_type == FoodSourceType.INVENTORY_ITEM:
            inv_food = next((i for i in npc.inventory if i.item_def_id == choice.item_def_id), None)
            if inv_food:
                ActionRegistry.eat(npc, inv_food)
            return "EAT_FROM_STORES"
        elif choice and choice.source_type == FoodSourceType.HOUSEHOLD_PANTRY:
            hh_eng = context.get_service("household_economy_engine") if hasattr(context, "get_service") else None
            if hh_eng and hh_eng.consume_pantry_meal(npc, tick):
                return "EAT_FROM_STORES"
        elif choice and choice.price_gold <= npc.wealth and choice.price_gold > 0:
            cost = choice.price_gold
            npc.wealth = max(0.0, round(npc.wealth - cost, 2))
            vendor = context.npcs.get(choice.vendor_id) if choice.vendor_id else None
            if vendor and vendor.id != npc.id:
                from src.configuration.settings import SettingsRegistry
                cul_cfg = SettingsRegistry.get_instance().get("culinary_economy")
                gov_cfg = SettingsRegistry.get_instance().get("civic_governance")
                v_econ = cul_cfg.get("vendor_economics", {})

                # Commercial sales tax (8%) flows to municipal treasury
                comm_cfg = gov_cfg.get("commercial_taxation", {})
                tax_rate = float(comm_cfg.get("sales_tax_rate", 0.08))
                market_tax = round(cost * tax_rate, 2)
                rem_cost = max(0.0, cost - market_tax)

                margin_ratio = float(v_econ.get("vendor_net_margin_ratio", 0.50))
                wholesale_ratio = float(v_econ.get("vendor_wholesale_cost_ratio", 0.50))

                vendor_profit = round(rem_cost * margin_ratio, 2)
                wholesale_cost = round(rem_cost * wholesale_ratio, 2)

                # Vendor earns operating margin
                vendor.wealth = round(vendor.wealth + vendor_profit, 2)
                vendor.record_stat("career_earnings_gold", vendor_profit)

                # Wholesale input cost flows to agricultural producers (farmer/miller)
                supplier = context.find_npc_by_role(["miller", "farmer", "peasant"]) if hasattr(context, "find_npc_by_role") else None
                if supplier and supplier.id != vendor.id:
                    supplier.wealth = round(supplier.wealth + wholesale_cost, 2)
                    supplier.record_stat("career_earnings_gold", wholesale_cost)

                # Sales tax dues flow to municipal treasury
                treasury = getattr(context, "municipal_treasury", None)
                if treasury and hasattr(treasury, "balance") and market_tax > 0:
                    treasury.balance = round(treasury.balance + market_tax, 2)

            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 45.0)
            # Satiety buffer ensures prolonged fullness (3-4 hours)
            npc._satiety_buffer_until_tick = tick + 240
            npc.adjust_feeling("contentment", 8.0)
            npc.adjust_feeling("stress", -4.0)
            return "BUY_AND_EAT_FOOD"

        # Check Parish Charitable Alms Box (Grassroots sustenance from parish tithes)
        aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
        if aid_eng and "aid_sacred_hearth_alms" in aid_eng.lodges:
            parish_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
            if npc.wealth < 6.0 and parish_chest.treasury_balance > parish_chest.min_treasury_reserve_gold:
                ration_cost = 0.50
                if parish_chest.treasury_balance >= ration_cost:
                    parish_chest.treasury_balance = round(parish_chest.treasury_balance - ration_cost, 2)
                    npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 35.0)
                    npc.adjust_feeling("contentment", 6.0)
                    npc.adjust_feeling("stress", -5.0)
                    npc.record_biographical_entry(
                        tick, time_iso, "PARISH_ALMS_RECEIVED",
                        f"Received charitable sustenance bread from Parish Alms Box in {npc.location_id}."
                    )
                    return "PARISH_ALMS_EAT"

        # Means-End Volition Problem Solving: Opportunistically seeks alternative sustenance
        volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
        if volition_eng:
            sol_res = volition_eng.execute_sustenance_problem_solving(npc, context, tick)
            if sol_res.get("success"):
                return sol_res.get("action", "EAT_FROM_STORES")

        # If NO food was available through conventional, compensatory, or transgressive means:
        npc.adjust_feeling("stress", 5.0)
        npc.adjust_feeling("contentment", -8.0)
        return "STARVATION_HUNGER_UNMET" 

class RestDriveStrategy(IDriveStrategy):
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        ActionRegistry.sleep(npc)
        return "SLEEP_REST"

class WorkProductionDriveStrategy(IDriveStrategy):
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
        if volition_eng and npc.id in volition_eng.aspirations:
            from src.entities.occupations import OccupationRegistry
            occ_reg = OccupationRegistry.get_instance()
            shift = occ_reg.get_shift_window(getattr(npc, "occupation", ""))
            if not shift.is_within_shift(hour):
                target_skill = volition_eng.aspirations[npc.id].required_skill
                masters = [
                    p for p in getattr(context, "npcs", {}).values()
                    if p.id != npc.id and p.location_id == npc.location_id and getattr(p, "is_alive", True) and p.get_skill(target_skill) >= 50.0
                ] if hasattr(context, "npcs") else []
                if masters:
                    ActionRegistry.observe_master_artisan(npc, masters[0], context)
                    return "OBSERVE_MASTER_ARTISAN"
                else:
                    ActionRegistry.vocational_study(npc, context)
                    return "VOCATIONAL_STUDY"

        ActionRegistry.work(npc, context)
        return "LABOR_WORK"

class SocializeDriveStrategy(IDriveStrategy):
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        """
        Relationship-Weighted Socializing:
        Fulfillment, stress relief, and feelings scale dynamically based on WHO is in the room.
        - Friends/Lovers: High contentment gain, strong stress & loneliness relief.
        - Rivals/Enemies/Grudges: Ineffective socialization, increases stress and vigilance.
        - Modesty is a two-way street: Proposers will not propose intimacy in rooms they themselves
          find public/uncomfortable; instead, they propose retiring together to private bedchambers.
        """
        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        grudge_eng = context.get_service("memory_grudge_engine") if hasattr(context, "get_service") else None

        peers = [
            n for n in context.npcs.values()
            if n.id != npc.id and n.location_id == npc.location_id and getattr(n, "is_alive", True)
        ] if hasattr(context, "npcs") else []

        avg_affinity = 0.0
        has_active_rival = False

        if peers:
            affinities = []
            for p in peers:
                net_op = op_eng.get_net_opinion(npc.id, p.id) if op_eng and hasattr(op_eng, "get_net_opinion") else 0.0
                if grudge_eng and hasattr(grudge_eng, "has_grudge_against") and grudge_eng.has_grudge_against(npc.id, p.id):
                    net_op -= 50.0
                    has_active_rival = True
                affinities.append(net_op)
            avg_affinity = sum(affinities) / len(affinities)

        # If no peers present in the room, agent cannot socialize with thin air!
        if not peers:
            npc.adjust_feeling("loneliness", 3.0)
            return "SOLITARY_REFLECTION"

        # Scale outcomes based on affinity
        if has_active_rival or avg_affinity < -20.0:
            social_gain = 10.0
            stress_delta = 8.0
            contentment_delta = -5.0
            loneliness_delta = -5.0
        elif avg_affinity > 25.0:
            social_gain = 35.0
            stress_delta = -12.0
            contentment_delta = 10.0
            loneliness_delta = -20.0
        else:
            social_gain = 25.0
            stress_delta = -6.0
            contentment_delta = 6.0
            loneliness_delta = -10.0

        npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + social_gain)
        npc.adjust_feeling("stress", stress_delta)
        npc.adjust_feeling("loneliness", loneliness_delta)
        npc.adjust_feeling("contentment", contentment_delta)

        # Epistemic Engine & Relational Social Prioritization
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
        if ep_eng and peers:
            peers.sort(key=lambda p: ep_eng.calculate_relational_priority(npc, p, context), reverse=True)

        # Ambient communication & gossip diffusion during social interactions
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
        if info_eng and peers:
            partner = peers[0]
            info_eng.share_gossip(npc, partner, context, tick)

            if ep_eng:
                from src.society.epistemic_engine import VisibilityTier
                thread = ep_eng.get_dyadic_thread(npc.id, partner.id)
                working_mem = ep_eng.get_active_working_memory(npc, tick)
                for trace in working_mem:
                    atom = trace.atom
                    if atom.atom_id not in thread.discussed_atom_ids:
                        can_share = False
                        if atom.visibility == VisibilityTier.PUBLIC_SETTLEMENT:
                            can_share = True
                        elif atom.visibility == VisibilityTier.PRIVATE_DYADIC and avg_affinity >= 10.0:
                            can_share = True
                        elif atom.visibility == VisibilityTier.CONFIDENTIAL and avg_affinity >= 30.0:
                            can_share = True
                        elif atom.visibility == VisibilityTier.SECRET and avg_affinity >= 50.0:
                            can_share = True

                        if can_share:
                            ep_eng.impart_knowledge(partner, atom, tick, salience=0.9, confided_by_id=npc.id)
                            ep_eng.record_dyadic_exchange(npc, partner, atom, context, tick)
                            break

        # Autonomous Romantic & Intimacy Engagement when partner or crush is co-located
        rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else None
        if rom_eng and peers:
            partner_cand = None
            spouse_id = npc.social_profile.get("spouse_id") if hasattr(npc, "social_profile") else None
            partner_id = npc.social_profile.get("partner_id") if hasattr(npc, "social_profile") else None

            # Prioritize declared spouse or partner
            for p in peers:
                if p.id in (spouse_id, partner_id):
                    partner_cand = p
                    break

            # Fallback to high mutual affection / crush
            if not partner_cand:
                for p in peers:
                    bond = rom_eng.get_or_create_bond(npc.id, p.id, context=context)
                    if bond.romantic_affection >= 30.0 or bond.physical_attraction >= 40.0:
                        partner_cand = p
                        break

            if partner_cand:
                bond = rom_eng.get_or_create_bond(npc.id, partner_cand.id, context=context)
                passion = float(npc.get_feeling("passion"))
                tension = float(getattr(npc, "unmet_intimacy_tension", 0.0))

                room_id = (npc.location_id or "").lower()
                priv_keywords = ["bedroom", "quarters", "loft", "cellar", "chambers", "cottage", "secluded"]
                is_private_room = any(k in room_id for k in priv_keywords)
                witnesses = [n for n in peers if n.id not in (npc.id, partner_cand.id)]

                # Check the actor's own comfort first! Modesty is a two-way street!
                actor_willing, actor_score, actor_reason = rom_eng.calculate_public_intimacy_willingness(
                    npc, len(witnesses), is_private_room, bond
                )

                if is_private_room or actor_willing:
                    if passion >= 20.0 or tension >= 20.0:
                        res = ActionRegistry.execute_private_intimacy(npc, partner_cand, current_tick=tick, context=context)
                        if res.get("success"):
                            npc.unmet_intimacy_tension = max(0.0, getattr(npc, "unmet_intimacy_tension", 10.0) - 35.0)
                            return "PRIVATE_INTIMACY"
                    elif bond.romantic_affection >= 25.0:
                        ActionRegistry.public_affection_display(npc, partner_cand, context=context)
                        return "PUBLIC_AFFECTION_DISPLAY"
                else:
                    # Actor is modest in public: Do NOT propose intimacy here! Propose retiring to quarters!
                    if passion >= 20.0 or tension >= 20.0:
                        invite_res = ActionRegistry.invite_to_private_quarters(npc, partner_cand, context=context)
                        if invite_res.get("success"):
                            return "INVITE_TO_PRIVATE_QUARTERS"
                    elif bond.romantic_affection >= 25.0:
                        ActionRegistry.public_affection_display(npc, partner_cand, context=context)
                        return "PUBLIC_AFFECTION_DISPLAY"

        # 2. Spiritual Confession or Companion Confiding for Guilty NPCs
        if float(npc.get_feeling("guilt")) >= 30.0:
            dil_eng = context.get_service("moral_dilemma_engine") if hasattr(context, "get_service") else None
            r_low = (npc.location_id or "").lower()
            if any(k in r_low for k in ("chapel", "sanctuary", "church")):
                priest = next((p for p in peers if "priest" in (p.occupation or "").lower()), None)
                if priest:
                    conf_res = ActionRegistry.seek_spiritual_confession(npc, priest, context)
                    if conf_res.get("success"):
                        return "SPIRITUAL_CONFESSION"
            elif op_eng:
                high_trust_peer = next((p for p in peers if op_eng.get_net_opinion(npc.id, p.id) >= 60.0), None)
                if high_trust_peer:
                    confide_res = ActionRegistry.confide_secret(npc, high_trust_peer, "private transgressions", context)
                    if confide_res.get("success"):
                        return "CONFIDE_SECRET"

        # 3. Fraternal Social Club Gatherings
        club_eng = context.get_service("social_club_engine") if hasattr(context, "get_service") else None
        if club_eng and hasattr(club_eng, "clubs"):
            for club in club_eng.clubs.values():
                if npc.id in club.member_ids:
                    conclave = club_eng.evaluate_club_gathering(club.club_id, npc.location_id or "", context, tick)
                    if conclave and conclave.get("success"):
                        return "CLUB_GATHERING"

        # 4. Leisure Recreation Contests & Tavern Wagers
        game_eng = context.get_service("recreation_game_engine") if hasattr(context, "get_service") else None
        if game_eng and peers and float(getattr(npc, "wealth", 0.0)) >= 1.0:
            r_low = (npc.location_id or "").lower()
            candidate_game = None
            if "tavern" in r_low:
                candidate_game = "dice_hazard" if float(getattr(npc, "vices", {}).get("gambling_drive", 0.0)) >= 20.0 or context.random.random() < 0.5 else "arm_wrestling"
            elif any(k in r_low for k in ("square", "plaza", "field")):
                candidate_game = "bocce_ball"

            if candidate_game:
                shuffled_peers = list(peers)
                context.random.shuffle(shuffled_peers)
                for opp in shuffled_peers:
                    game_res = ActionRegistry.play_recreation_game(npc, opp, candidate_game, context)
                    if game_res.get("success"):
                        return f"PLAY_{candidate_game.upper()}"

        return "COMMUNITY_SOCIALIZE"

class CommunalDiningDriveStrategy(IDriveStrategy):
    def execute(self, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        # Closed-loop tavern meal / ale transaction dynamically loaded from culinary_economy.json
        from src.configuration.settings import SettingsRegistry
        cul_cfg = SettingsRegistry.get_instance().get("culinary_economy")
        cd_cfg = cul_cfg.get("communal_dining", {})
        meal_price = float(cd_cfg.get("tavern_meal_price_gold", 1.20))

        if npc.wealth >= meal_price:
            npc.wealth = round(npc.wealth - meal_price, 2)
            innkeeper = context.find_npc_by_role(["innkeeper", "barkeep"]) if hasattr(context, "find_npc_by_role") else None
            treasury = getattr(context, "municipal_treasury", None)
            tax = round(meal_price * 0.08, 2)
            profit = round(meal_price - tax, 2)
            if innkeeper and innkeeper.id != npc.id:
                innkeeper.wealth = round(innkeeper.wealth + profit, 2)
                innkeeper.record_stat("career_earnings_gold", profit)
            if treasury and hasattr(treasury, "balance") and tax > 0:
                treasury.balance = round(treasury.balance + tax, 2)

            h_relief = float(cd_cfg.get("hunger_relief", 35.0))
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - h_relief)
            npc.adjust_feeling("stress", -6.0)
            npc.adjust_feeling("contentment", 8.0)
        else:
            # Cannot afford tavern meal; only receives taproom company without food
            npc.adjust_feeling("stress", 2.0)

        s_relief = float(cd_cfg.get("social_relief", 20.0))
        npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + s_relief)
        return "COMMUNAL_DINING"

class DriveStrategyRegistry:
    def __init__(self):
        self.strategies: Dict[str, IDriveStrategy] = {
            "satisfy_hunger": HungerDriveStrategy(),
            "rest": RestDriveStrategy(),
            "work_production": WorkProductionDriveStrategy(),
            "socialize": SocializeDriveStrategy(),
            "communal_dining": CommunalDiningDriveStrategy(),
        }

    def execute_drive(self, chosen_drive: str, npc: NPC, context: Any, tick: int, time_iso: str, hour: int, locations: Dict[str, str]) -> str:
        strat = self.strategies.get(chosen_drive, self.strategies["rest"])
        return strat.execute(npc, context, tick, time_iso, hour, locations)
