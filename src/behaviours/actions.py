"""Expanded Action Registry with Calibrated Sleep, Overtime, Bilateral Romance, and Communal Dynamics."""
from typing import Any, Dict, List, Optional
import uuid
from src.entities.npc import NPC
from src.entities.item import ItemInstance

class ActionRegistry:
    @staticmethod
    def eat(npc: NPC, item_instance: ItemInstance) -> bool:
        if item_instance in npc.inventory:
            npc.inventory.remove(item_instance)
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 40.0)
            npc.adjust_feeling("contentment", 15.0)
            return True
        return False

    @staticmethod
    def sleep(npc: NPC, context: Optional[Any] = None) -> bool:
        """Calibrated Sleep Energy Recovery loaded dynamically from data/settings/physiology.json."""
        from src.configuration.settings import SettingsRegistry
        phys_cfg = SettingsRegistry.get_instance().get("physiology")
        sleep_cfg = phys_cfg.get("sleep_recovery", {})
        energy_gain = float(sleep_cfg.get("energy_gain_per_hour", 14.0))
        stress_relief = float(sleep_cfg.get("stress_relief_per_hour", -12.0))

        r_loc = (npc.location_id or "").lower()
        is_outdoor = any(k in r_loc for k in ("square", "plaza", "quay", "street", "road", "field", "garden", "market"))
        if is_outdoor:
            energy_gain *= float(sleep_cfg.get("outdoor_sleep_penalty_multiplier", 0.50))
            stress_relief = float(sleep_cfg.get("outdoor_sleep_stress_gain", 6.0))
            npc.adjust_feeling("contentment", -float(sleep_cfg.get("outdoor_sleep_contentment_penalty", 8.0)))
            npc.adjust_feeling("stress", stress_relief)
        else:
            npc.adjust_feeling("stress", stress_relief)
            npc.adjust_feeling("contentment", 6.0)

        npc.needs["energy"] = min(100.0, npc.needs.get("energy", 0.0) + energy_gain)
        return True

    @staticmethod
    def work(npc: NPC, context: Optional[Any] = None) -> float:
        occ = getattr(npc, "occupation", "Commoner").lower()
        work_rate = float(npc.physical_attributes.get("work_rate", 55.0))
        from src.entities.occupations import OccupationRegistry
        occ_reg = OccupationRegistry.get_instance()
        occ_spec = occ_reg.get_occupation_spec(occ)
        base_hourly_wage = float(occ_spec.get("base_hourly_wage", 1.20))
        base_earned = base_hourly_wage * (work_rate / 50.0)

        wage_multiplier = 1.0
        labor_category = "REGULAR_SHIFT"
        job_role_title = npc.occupation or "Laborer"

        # Check Surge Requisition or Overtime
        if context:
            tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
            hour = context.clock.current_virtual_time.hour if hasattr(context, "clock") and context.clock else (tick // 60) % 24
            time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"

            # 1. Surge Job (e.g. Extra Bartender, Deputy Watchman)
            demand_eng = context.get_service("workplace_labor_demand_engine") if hasattr(context, "get_service") else None
            if demand_eng and hasattr(demand_eng, "active_requisitions"):
                for req in demand_eng.active_requisitions.values():
                    if req.is_active and req.assigned_npc_id == npc.id:
                        wage_multiplier = req.hourly_wage_multiplier
                        labor_category = "CASUAL_SURGE"
                        job_role_title = req.job_title
                        break

            # 2. Overtime Shift Check
            if labor_category == "REGULAR_SHIFT":
                from src.entities.occupations import OccupationRegistry
                occ_reg = OccupationRegistry.get_instance()
                shift = occ_reg.get_shift_window(npc.occupation)
                if shift.is_overtime_window(hour):
                    wage_multiplier = shift.overtime_multiplier
                    labor_category = "OVERTIME"

        earned = round(base_earned * wage_multiplier, 1)

        # Closed-loop wage payment (Strict conservation: no unbacked fiat minting!)
        actual_paid = 0.0
        is_sacred = any(k in occ for k in ("priest", "clergy", "monk", "curate"))
        comforted_count = 0
        alms_given_count = 0

        if context:
            from src.entities.occupations import OccupationRegistry
            occ_reg = OccupationRegistry.get_instance()
            is_civic = occ_reg.is_civic(npc.occupation) or "watch" in job_role_title.lower()
            treasury = getattr(context, "municipal_treasury", None)

            if is_sacred:
                # Sacred / Clergy: living compensation is drawn from accumulated parish member levies / tithes
                aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
                if aid_eng and hasattr(aid_eng, "lodges"):
                    parish_chest = aid_eng.lodges.get("aid_sacred_hearth_alms")
                    if parish_chest:
                        stipend = min(earned, max(0.0, round(parish_chest.treasury_balance - 5.0, 2)))
                        if stipend > 0:
                            parish_chest.treasury_balance = round(parish_chest.treasury_balance - stipend, 2)
                            actual_paid = stipend
            elif is_civic and treasury and hasattr(treasury, "balance"):
                if treasury.balance >= earned:
                    treasury.balance = round(treasury.balance - earned, 2)
                    actual_paid = earned
                else:
                    actual_paid = max(0.0, float(treasury.balance))
                    treasury.balance = 0.0
            elif npc.work_location_id:
                bldg = context.find_building_by_id(npc.work_location_id)
                if bldg and bldg.owner_id and bldg.owner_id != npc.id:
                    owner = context.npcs.get(bldg.owner_id)
                    if owner and getattr(owner, "wealth", 0.0) >= (earned + 10.0):
                        owner.wealth = round(owner.wealth - earned, 2)
                        actual_paid = earned
                elif bldg and bldg.owner_id == npc.id:
                    # Self-employed proprietor (Aldous, Greta, Silas): earns by selling produced goods/ale, not fiat wages!
                    actual_paid = 0.0
            elif not npc.work_location_id and treasury and hasattr(treasury, "balance"):
                if treasury.balance >= earned:
                    treasury.balance = round(treasury.balance - earned, 2)
                    actual_paid = earned
        else:
            # Standalone unit test without context
            actual_paid = earned

        if actual_paid > 0:
            npc.wealth = round(npc.wealth + actual_paid, 2)
        energy_drain = round(8.0 * max(1.0, wage_multiplier * 0.9), 1)
        npc.needs["energy"] = max(0.0, round(npc.needs.get("energy", 0.0) - energy_drain, 1))
        npc.adjust_feeling("contentment", 2.0)
        if wage_multiplier > 1.2 or any(k in occ for k in ("smith", "blacksmith", "miner", "laborer")):
            npc.adjust_feeling("stress", 1.5)
        npc.record_stat("career_earnings_gold", earned)

        if context and hasattr(context, "clock") and context.clock:
            tick = context.clock.current_tick
            time_iso = context.clock.current_virtual_time_iso

            # Physical commodity production step with dynamic bottleneck response
            sc_eng = context.get_service("supply_chain_engine")
            if sc_eng and hasattr(sc_eng, "execute_production_step"):
                if "baker" in occ:
                    # If flour is dry, small-batch mill flour first
                    if sc_eng.get_stock_level("flour") < 1.0 and sc_eng.get_stock_level("raw_wheat") >= 1.0:
                        sc_eng.execute_production_step(npc, "mill_flour", context, tick=tick)
                    else:
                        sc_eng.execute_production_step(npc, "bake_bread", context, tick=tick)
                elif "miller" in occ:
                    sc_eng.execute_production_step(npc, "mill_flour", context, tick=tick)
                elif "farmer" in occ:
                    # If flour is critically low, farmers assist in grinding flour
                    if sc_eng.get_stock_level("flour") < 8.0 and sc_eng.get_stock_level("raw_wheat") >= 2.0:
                        sc_eng.execute_production_step(npc, "mill_flour", context, tick=tick)
                    else:
                        sc_eng.execute_production_step(npc, "harvest_wheat", context, tick=tick)
                elif any(k in occ for k in ("laborer", "woodcutter")):
                    firewood_stock = sc_eng.get_stock_level("firewood")
                    timber_stock = sc_eng.get_stock_level("raw_timber")
                    if firewood_stock >= 40.0 and timber_stock < 25.0:
                        sc_eng.execute_production_step(npc, "fell_timber", context, tick=tick)
                    elif firewood_stock < 40.0 and timber_stock >= 1.0:
                        sc_eng.execute_production_step(npc, "split_firewood", context, tick=tick)
                    elif timber_stock < 25.0:
                        sc_eng.execute_production_step(npc, "fell_timber", context, tick=tick)
                elif any(k in occ for k in ("smith", "blacksmith")):
                    if sc_eng.get_stock_level("iron_ingot") < 8.0 and sc_eng.get_stock_level("raw_iron_ore") >= 1.0:
                        sc_eng.execute_production_step(npc, "smelt_iron", context, tick=tick)
                    else:
                        sc_eng.execute_production_step(npc, "forge_tools", context, tick=tick)
                else:
                    occ_recipe_map = {
                        "carpenter": "craft_furniture",
                        "innkeeper": "brew_ale",
                        "woodcutter": "fell_timber",
                        "laborer": "split_firewood"
                    }
                    for occ_k, r_id in occ_recipe_map.items():
                        if occ_k in occ:
                            sc_eng.execute_production_step(npc, r_id, context, tick=tick)
                            break

            if is_sacred:
                # Pastoral Community Support Tasks:
                # 1. Pastoral Counseling & Grief/Stress Consolation
                for parishioner in context.npcs.values():
                    if parishioner.id != npc.id and getattr(parishioner, "is_alive", True):
                        if parishioner.location_id in (npc.location_id, "room_chapel", "room_village_square"):
                            p_grief = float(parishioner.get_feeling("grief"))
                            p_stress = float(parishioner.get_feeling("stress"))
                            if p_grief > 20.0 or p_stress > 40.0:
                                parishioner.adjust_feeling("grief", -25.0)
                                parishioner.adjust_feeling("stress", -20.0)
                                parishioner.adjust_feeling("tenderness", 10.0)
                                comforted_count += 1
                                parishioner.record_biographical_entry(
                                    tick, time_iso, "PASTORAL_CARE_RECEIVED",
                                    f"Received spiritual counsel, blessing, and comfort from Father {npc.name}."
                                )
                                if comforted_count >= 2:
                                    break

                # 2. Sacred Liturgy & Altar Offerings
                if "chapel" in (npc.location_id or "").lower():
                    npc.adjust_feeling("contentment", 4.0)
                    for attendee in context.npcs.values():
                        if attendee.location_id == npc.location_id and attendee.id != npc.id:
                            attendee.adjust_feeling("contentment", 3.0)
                            attendee.adjust_feeling("stress", -5.0)
                            sp = getattr(attendee, "social_profile", {}) or {}
                            facets = sp.setdefault("reputation_facets", {})
                            facets["moral_piety"] = min(100.0, round(facets.get("moral_piety", 50.0) + 2.0, 2))
                            # Voluntary altar offering from solvent worshippers
                            if float(getattr(attendee, "wealth", 0.0)) >= 12.0:
                                offering = 0.10
                                attendee.wealth = round(attendee.wealth - offering, 2)
                                aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
                                if aid_eng and "aid_sacred_hearth_alms" in aid_eng.lodges:
                                    aid_eng.lodges["aid_sacred_hearth_alms"].treasury_balance = round(
                                        aid_eng.lodges["aid_sacred_hearth_alms"].treasury_balance + offering, 2
                                    )

                # 3. Parish Alms & Bread Distribution to Destitute
                aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
                if aid_eng and "aid_sacred_hearth_alms" in aid_eng.lodges:
                    parish_chest = aid_eng.lodges["aid_sacred_hearth_alms"]
                    for poor_citizen in context.npcs.values():
                        if poor_citizen.id != npc.id and getattr(poor_citizen, "is_alive", True):
                            if poor_citizen.location_id in (npc.location_id, "room_chapel", "room_village_square"):
                                if float(poor_citizen.wealth) < 5.0 and float(poor_citizen.needs.get("hunger", 0.0)) > 50.0:
                                    if parish_chest.treasury_balance >= 0.50:
                                        parish_chest.treasury_balance = round(parish_chest.treasury_balance - 0.50, 2)
                                        poor_citizen.needs["hunger"] = max(0.0, poor_citizen.needs.get("hunger", 0.0) - 35.0)
                                        poor_citizen.adjust_feeling("contentment", 8.0)
                                        poor_citizen.adjust_feeling("stress", -6.0)
                                        alms_given_count += 1
                                        poor_citizen.record_biographical_entry(
                                            tick, time_iso, "PARISH_ALMS_RECEIVED",
                                            f"Received parish bread sustenance distributed by Father {npc.name}."
                                        )
                                        break

                care_details = []
                if comforted_count > 0:
                    care_details.append(f"consoled {comforted_count} parishioners")
                if alms_given_count > 0:
                    care_details.append(f"distributed alms to {alms_given_count} destitute citizens")
                detail_str = f" ({', '.join(care_details)})" if care_details else ""

                npc.record_biographical_entry(
                    tick, time_iso, "PASTORAL_COMMUNITY_CARE",
                    f"Administered sacred liturgy and pastoral community care{detail_str} (living stipend: {actual_paid:.1f}g from parish tithes).",
                    {"stipend_gold": actual_paid, "source": "parish_member_levies"}
                )
            else:
                npc.record_biographical_entry(
                    tick, time_iso, "ECONOMIC_LABOR",
                    f"Worked as {job_role_title} ({labor_category.lower()}), earning {earned:.1f}g (multiplier: {wage_multiplier:.1f}x).",
                    {"earned_gold": earned, "labor_category": labor_category, "multiplier": wage_multiplier}
                )

        return earned

    @staticmethod
    def execute_private_intimacy(actor: NPC, partner: NPC, current_tick: int = 0, context: Optional[Any] = None) -> Dict[str, Any]:
        """
        Bilateral Consensual Intimacy Execution with Spatial Privacy and Scandal Radiance:
        1. Evaluates mutual consent, co-location, and partner somatic state.
        2. Applies emotional gains if consensual; applies rejection grief if refused.
        3. Emits ambient scandal waves if witnessed or breach of monogamy.
        """
        from src.society.romance import RomanceEngine
        rom_eng = context.get_service("romance_engine") if context and hasattr(context, "get_service") else RomanceEngine()

        consented, reason, details = rom_eng.evaluate_consent_and_privacy(actor, partner, "private_intimacy", context)
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        act_cfg = rom_cfg.get("actions", {}).get("private_intimacy", {})

        if not consented:
            rejection_grief = float(act_cfg.get("rejection_grief", 12.0))
            actor.adjust_feeling("grief", rejection_grief)
            actor.adjust_feeling("stress", 10.0)
            return {"success": False, "action": "PRIVATE_INTIMACY", "reason": reason, "details": details}

        p_gain = float(act_cfg.get("passion_gain", 35.0))
        t_gain = float(act_cfg.get("tenderness_gain", 30.0))
        s_relief = float(act_cfg.get("stress_relief", -25.0))
        l_relief = float(act_cfg.get("loneliness_relief", -30.0))
        soc_gain = float(act_cfg.get("social_gain", 35.0))

        actor.adjust_feeling("passion", p_gain)
        partner.adjust_feeling("passion", p_gain)
        actor.adjust_feeling("tenderness", t_gain)
        partner.adjust_feeling("tenderness", t_gain)
        actor.adjust_feeling("stress", s_relief)
        partner.adjust_feeling("stress", s_relief)
        actor.adjust_feeling("loneliness", l_relief)
        partner.adjust_feeling("loneliness", l_relief)
        actor.needs["social"] = min(100.0, actor.needs.get("social", 50.0) + soc_gain)
        partner.needs["social"] = min(100.0, partner.needs.get("social", 50.0) + soc_gain)

        # Bond enhancement
        bond = rom_eng.get_or_create_bond(actor.id, partner.id)
        bond.romantic_affection = min(100.0, bond.romantic_affection + 8.0)
        bond.physical_attraction = min(100.0, bond.physical_attraction + 5.0)
        bond.trust = min(100.0, bond.trust + 4.0)

        # Check Exhibitionist Thrill Bonus if public encounter was embraced
        if details.get("is_exhibitionist_act"):
            exh_cfg = rom_cfg.get("elastic_privacy_and_exhibitionism", {}).get("exhibitionist_thrill", {})
            p_bonus = float(exh_cfg.get("passion_bonus", 18.0))
            pride_bonus = float(exh_cfg.get("pride_bonus", 22.0))
            stress_bonus = float(exh_cfg.get("stress_relief_bonus", -12.0))

            actor.adjust_feeling("passion", p_bonus)
            partner.adjust_feeling("passion", p_bonus)
            actor.adjust_feeling("pride", pride_bonus)
            partner.adjust_feeling("pride", pride_bonus)
            actor.adjust_feeling("stress", stress_bonus)
            partner.adjust_feeling("stress", stress_bonus)

            if context and hasattr(context, "clock") and context.clock:
                tick = context.clock.current_tick
                time_iso = context.clock.current_virtual_time_iso
                actor.record_biographical_entry(
                    tick, time_iso, "EXHIBITIONIST_TRYST",
                    f"Indulged in a thrilling, uninhibited public intimate encounter at {actor.location_id}."
                )
                partner.record_biographical_entry(
                    tick, time_iso, "EXHIBITIONIST_TRYST",
                    f"Indulged in a thrilling, uninhibited public intimate encounter at {partner.location_id}."
                )

        # Check Town Guard intervention in open public squares
        room_id = (actor.location_id or "").lower()
        if not details.get("is_exhibitionist_act") and any(k in room_id for k in ("square", "plaza", "market")) and context and hasattr(context, "npcs"):
            guards_in_area = [
                n for n in context.npcs.values()
                if n.id not in (actor.id, partner.id) and n.location_id == actor.location_id
                and any(k in (n.occupation or "").lower() for k in ("guard", "sheriff", "constable", "watchman"))
                and getattr(n, "is_alive", True)
            ]
            if guards_in_area:
                guard = guards_in_area[0]
                actor.adjust_feeling("guilt", 15.0)
                partner.adjust_feeling("guilt", 15.0)
                actor.adjust_feeling("pride", -10.0)
                partner.adjust_feeling("pride", -10.0)
                guard.adjust_feeling("vigilance", 15.0)
                time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
                actor.record_biographical_entry(
                    current_tick, time_iso, "TOWN_GUARD_ADMONISHMENT",
                    f"Reprimanded by Watchman {guard.name} for indecent public exposure in {actor.location_id}; ordered to disperse to private quarters."
                )
                partner.record_biographical_entry(
                    current_tick, time_iso, "TOWN_GUARD_ADMONISHMENT",
                    f"Reprimanded by Watchman {guard.name} for indecent public exposure in {partner.location_id}; ordered to disperse to private quarters."
                )

        # Check and emit ambient scandal waves if witnessed or breach of marital fidelity
        scandal_outcome = None
        if context:
            scandal_outcome = rom_eng.check_and_emit_relational_scandals(actor, partner, details, context, current_tick)

        rom_eng.total_intimacy_acts += 1
        return {
            "success": True,
            "action": "PRIVATE_INTIMACY",
            "reason": reason,
            "details": details,
            "scandal_outcome": scandal_outcome
        }

    @staticmethod
    def court_with_gift(suitor: NPC, target: NPC, gift_item: ItemInstance, context: Optional[Any] = None) -> Dict[str, Any]:
        """Bilateral Courtship Gift Evaluation with Acceptance Thresholds."""
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        act_cfg = rom_cfg.get("actions", {}).get("court_with_gift", {})
        min_trust = float(act_cfg.get("min_target_trust", 25.0))

        from src.society.romance import RomanceEngine
        rom_eng = context.get_service("romance_engine") if context and hasattr(context, "get_service") else RomanceEngine()
        bond = rom_eng.get_or_create_bond(suitor.id, target.id)

        # Target must have basic trust to accept courtship gifts
        if bond.trust < min_trust:
            rejection_grief = float(act_cfg.get("rejection_grief", 8.0))
            suitor.adjust_feeling("grief", rejection_grief)
            return {"success": False, "action": "COURT_WITH_GIFT", "reason": f"{target.name} refused gift: insufficient trust ({bond.trust:.1f} < {min_trust:.1f})."}

        if gift_item in suitor.inventory:
            suitor.inventory.remove(gift_item)
            target.inventory.append(gift_item)

        s_gain = float(act_cfg.get("suitor_tenderness_gain", 20.0))
        t_gain = float(act_cfg.get("target_tenderness_gain", 25.0))
        suitor.adjust_feeling("tenderness", s_gain)
        target.adjust_feeling("tenderness", t_gain)

        bond.romantic_affection = min(100.0, bond.romantic_affection + 12.0)
        bond.trust = min(100.0, bond.trust + 8.0)
        return {"success": True, "action": "COURT_WITH_GIFT", "gift_accepted": True}

    @staticmethod
    def comfort_partner(actor: NPC, partner: NPC) -> Dict[str, Any]:
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        act_cfg = rom_cfg.get("actions", {}).get("comfort_partner", {})
        s_relief = float(act_cfg.get("stress_relief", -25.0))
        g_relief = float(act_cfg.get("grief_relief", -30.0))

        partner.adjust_feeling("stress", s_relief)
        partner.adjust_feeling("grief", g_relief)
        return {"success": True, "action": "COMFORT_PARTNER"}

    @staticmethod
    def public_affection_display(actor: NPC, partner: NPC, bond: Any = None, onlookers: List[NPC] = None, spouse_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        act_cfg = rom_cfg.get("actions", {}).get("public_affection", {})
        p_gain = float(act_cfg.get("pride_gain", 15.0))

        actor.adjust_feeling("pride", p_gain)
        partner.adjust_feeling("pride", p_gain)

        # Radiate ambient visual wave into room
        if context:
            info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
            if info_eng and actor.location_id:
                tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
                from src.society.information_networks import InformationChannelType, WaveMedium
                info_item = info_eng.publish_item(
                    channel=InformationChannelType.GOSSIP_AND_RUMORS,
                    topic="PUBLIC_AFFECTION",
                    headline=f"Village Sight: Public Affection Between {actor.name} and {partner.name}",
                    content=f"Onlookers observed an open display of romantic tenderness at {actor.location_id}.",
                    source_npc_id=actor.id,
                    target_location_id=actor.location_id,
                    current_tick=tick,
                    context=context
                )
                info_eng.emit_ambient_wave(
                    item=info_item,
                    origin_room_id=actor.location_id,
                    medium=WaveMedium.VISUAL_LINE_OF_SIGHT,
                    intensity=0.75,
                    context=context,
                    current_tick=tick
                )

        return {"success": True, "action": "PUBLIC_AFFECTION_DISPLAY"}

    @staticmethod
    def invite_to_private_quarters(actor: NPC, partner: NPC, context: Any) -> Dict[str, Any]:
        """
        Consensual courtship invitation respecting modesty:
        Actor invites partner to retire from public gaze into private quarters/bedroom.
        """
        from src.society.romance import RomanceEngine
        rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else RomanceEngine()
        bond = rom_eng.get_or_create_bond(actor.id, partner.id, context=context)

        p_energy = float(partner.needs.get("energy", 100.0))
        p_stress = float(partner.get_feeling("stress"))
        is_spouse = (
            partner.social_profile.get("spouse_id") == actor.id or
            actor.social_profile.get("spouse_id") == partner.id
        )

        if p_energy < 15.0 or p_stress > 80.0:
            return {"success": False, "reason": f"{partner.name} was too exhausted/stressed to retire to quarters."}

        if not is_spouse and bond.romantic_affection < 25.0 and bond.trust < 30.0 and bond.physical_attraction < 35.0:
            return {"success": False, "reason": f"{partner.name} declined invitation: insufficient romantic rapport."}

        from src.configuration.settings import SettingsRegistry
        rom_cfg = SettingsRegistry.get_instance().get("romance_and_bonds")
        priv_cfg = rom_cfg.get("privacy_and_space", {})

        bedchamber = None
        rendezvous_type = "HOME_BEDCHAMBER"
        rental_fee_paid = 0.0

        # 1. Check if either partner has an actual private home bedroom / quarters
        for candidate_loc in (actor.home_location_id, partner.home_location_id):
            if candidate_loc:
                c_low = candidate_loc.lower()
                if any(k in c_low for k in ("bedroom", "quarters", "chambers", "cottage_bedroom")):
                    bedchamber = candidate_loc
                    rendezvous_type = "HOME_BEDCHAMBER"
                    break

        # 2. If neither owns/resides in a private bedroom: Rent a short-term private room (e.g. Tavern Loft)
        rental_cfg = rom_cfg.get("short_term_room_rental", {})
        if not bedchamber and rental_cfg.get("enabled", True):
            rental_fee = float(rental_cfg.get("rental_fee_gold", 0.50))
            tavern_rooms = context.find_rooms_by_keyword("tavern") or context.find_rooms_by_keyword("inn") if context and hasattr(context, "find_rooms_by_keyword") else []
            rental_candidates = [r for r in tavern_rooms if any(k in r.lower() for k in ("bedroom", "loft", "guest"))]
            if not rental_candidates and context and hasattr(context, "find_rooms_by_keyword"):
                rental_candidates = context.find_rooms_by_keyword("loft") or context.find_rooms_by_keyword("bedroom")

            if rental_candidates:
                target_rental = rental_candidates[0]
                payer = actor if actor.wealth >= rental_fee else (partner if partner.wealth >= rental_fee else None)
                if payer:
                    payer.wealth = round(payer.wealth - rental_fee, 2)
                    rental_fee_paid = rental_fee
                    bldg = context.find_building_by_room_id(target_rental) if hasattr(context, "find_building_by_room_id") else None
                    owner = context.npcs.get(bldg.owner_id) if bldg and bldg.owner_id in context.npcs else None
                    if not owner and hasattr(context, "find_npc_by_role"):
                        owner = context.find_npc_by_role(["innkeeper", "barkeeper", "tavern"])
                    if owner and owner.id not in (actor.id, partner.id):
                        owner.wealth = round(owner.wealth + rental_fee, 2)
                        owner.record_stat("career_earnings_gold", rental_fee)
                    elif hasattr(context, "municipal_treasury") and context.municipal_treasury:
                        context.municipal_treasury.balance = round(context.municipal_treasury.balance + rental_fee, 2)

                    bedchamber = target_rental
                    rendezvous_type = "RENTED_ROOM"

        # 3. If neither has private quarters AND neither can afford to rent: Secluded unowned space
        secluded_cfg = rom_cfg.get("secluded_unowned_spaces", {})
        if not bedchamber and secluded_cfg.get("enabled", True):
            secluded_kws = secluded_cfg.get("secluded_room_keywords", ["loft", "hayloft", "cellar", "meadow", "orchard", "woods", "brook", "garden"])
            secluded_candidates = []
            if context and hasattr(context, "find_rooms_by_keyword"):
                for kw in secluded_kws:
                    for rm in context.find_rooms_by_keyword(kw):
                        if rm not in secluded_candidates:
                            secluded_candidates.append(rm)

            if secluded_candidates:
                bedchamber = secluded_candidates[0]
                rendezvous_type = "SECLUDED_SPOT"
                thrill = float(secluded_cfg.get("clandestine_thrill_passion", 8.0))
                actor.adjust_feeling("passion", thrill)
                partner.adjust_feeling("passion", thrill)

        # 4. Tier 3 Transgressive Seclusion: Indoor Trespassing into an unoccupied workshop after hours
        if not bedchamber and context and hasattr(context, "find_rooms_by_keyword"):
            trespass_candidates = []
            for kw in ("blacksmith", "carpenter", "windmill", "shop", "bakery"):
                for rm in context.find_rooms_by_keyword(kw):
                    # Verify owner is not currently in the room
                    bldg = context.find_building_by_room_id(rm) if hasattr(context, "find_building_by_room_id") else None
                    owner = context.npcs.get(bldg.owner_id) if bldg and bldg.owner_id in context.npcs else None
                    if not owner or owner.location_id != rm:
                        trespass_candidates.append(rm)
            if trespass_candidates:
                bedchamber = trespass_candidates[0]
                rendezvous_type = "TRESPASSING_INDOORS"
                actor.adjust_feeling("passion", 10.0)
                partner.adjust_feeling("passion", 10.0)
                actor.adjust_feeling("guilt", 18.0)
                partner.adjust_feeling("guilt", 18.0)
                actor.adjust_feeling("stress", 12.0)
                partner.adjust_feeling("stress", 12.0)

        # 5. Public Fallback if no private/secluded/unoccupied space could be reached
        if not bedchamber:
            bedchamber = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
            rendezvous_type = "PUBLIC_FALLBACK"

        actor.location_id = bedchamber
        partner.location_id = bedchamber
        actor.current_action = f"COMMUTE_TO_{bedchamber}"
        partner.current_action = f"COMMUTE_TO_{bedchamber}"

        actor.adjust_feeling("tenderness", 12.0)
        partner.adjust_feeling("tenderness", 12.0)

        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"

        if rendezvous_type == "RENTED_ROOM":
            desc_a = f"Rented private quarters at {bedchamber} for intimate seclusion with {partner.name} (paid {rental_fee_paid:.2f}g)."
            desc_p = f"Joined {actor.name} in rented private quarters at {bedchamber}."
        elif rendezvous_type == "SECLUDED_SPOT":
            desc_a = f"Retreated to secluded space at {bedchamber} for a clandestine rendezvous with {partner.name}."
            desc_p = f"Joined {actor.name} for a secluded rendezvous at {bedchamber}."
        elif rendezvous_type == "TRESPASSING_INDOORS":
            desc_a = f"Slipped into unmonitored building at {bedchamber} for an illicit clandestine tryst with {partner.name}."
            desc_p = f"Joined {actor.name} for an illicit rendezvous inside {bedchamber}."
        else:
            desc_a = f"Invited {partner.name} to retire to private quarters at {bedchamber}."
            desc_p = f"Accepted {actor.name}'s invitation to retire to private quarters at {bedchamber}."

        actor.record_biographical_entry(tick, time_iso, "COURTSHIP_INVITATION", desc_a)
        partner.record_biographical_entry(tick, time_iso, "COURTSHIP_INVITATION", desc_p)

        return {
            "success": True,
            "action": "INVITE_TO_PRIVATE_QUARTERS",
            "destination": bedchamber,
            "rendezvous_type": rendezvous_type,
            "rental_fee_paid": rental_fee_paid
        }


    @staticmethod
    def vocational_study(npc: NPC, context: Any) -> Dict[str, Any]:
        """NPC engages in vocational study to advance towards an aspirational career."""
        volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        if volition_eng:
            return volition_eng.advance_vocational_skill_bridging(npc, method="STUDY", context=context, current_tick=tick)
        return {"success": False, "reason": "No volition engine"}

    @staticmethod
    def observe_master_artisan(npc: NPC, master: NPC, context: Any) -> Dict[str, Any]:
        """NPC observes master craftsman at work to accelerate skill acquisition."""
        volition_eng = context.get_service("means_end_volition_engine") if hasattr(context, "get_service") else None
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        if volition_eng:
            res = volition_eng.advance_vocational_skill_bridging(npc, method="OBSERVE", context=context, current_tick=tick)
            if res.get("success"):
                time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
                master.adjust_feeling("pride", 6.0)
                master.record_biographical_entry(
                    tick, time_iso, "APPRENTICE_OBSERVATION",
                    f"Observed in workshop by aspiring craftsperson {npc.name} eager to learn the trade."
                )
            return res
        return {"success": False, "reason": "No volition engine"}

    @staticmethod
    def declare_betrothal(suitor: NPC, betrothed: NPC, context: Any) -> Dict[str, Any]:
        """Formal Declarative Speech Act of Betrothal registered with Civic Notice Board."""
        from src.society.romance import RomanceEngine, RelationshipStage
        rom_eng = context.get_service("romance_engine") if hasattr(context, "get_service") else RomanceEngine()
        bond = rom_eng.get_or_create_bond(suitor.id, betrothed.id)

        bond.stage = RelationshipStage.BETROTHED
        suitor.social_profile["partner_id"] = betrothed.id
        betrothed.social_profile["partner_id"] = suitor.id

        # Publish formal notice to civic board
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else None
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        if info_eng:
            public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
            info_eng.publish_item(
                channel="CIVIC_NOTICES",
                topic="BETROTHAL_ANNOUNCEMENT",
                headline=f"Public Banns: Betrothal of {suitor.name} and {betrothed.name}",
                content=f"Notice is hereby given of the betrothal contract entered into by {suitor.name} and {betrothed.name}.",
                source_npc_id=suitor.id,
                target_location_id=public_plaza,
                current_tick=tick,
                custom_duration=14400
            )

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        suitor.record_biographical_entry(tick, time_iso, "BETROTHAL_DECLARED", f"Formally pledged betrothal vows with {betrothed.name}.")
        betrothed.record_biographical_entry(tick, time_iso, "BETROTHAL_DECLARED", f"Formally pledged betrothal vows with {suitor.name}.")
        return {"success": True, "action": "DECLARE_BETROTHAL", "stage": "BETROTHED"}

    @staticmethod
    def read_notice_board(reader: NPC, context: Any) -> Dict[str, Any]:
        from src.society.information_networks import UnifiedInformationEngine
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else UnifiedInformationEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        room_id = reader.location_id or (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")
        items = info_eng.read_notice_board(reader, room_id, context, tick)
        return {"success": True, "action": "READ_NOTICE_BOARD", "learned_items_count": len(items)}

    @staticmethod
    def share_gossip_with_peer(speaker: NPC, listener: NPC, context: Any) -> Dict[str, Any]:
        from src.society.information_networks import UnifiedInformationEngine
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else UnifiedInformationEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        shared = info_eng.share_gossip(speaker, listener, context, tick)
        return {"success": True, "action": "SHARE_GOSSIP", "shared_items_count": len(shared)}

    @staticmethod
    def report_crime_to_watch(informant: NPC, guard: NPC, crime_topic: str, crime_desc: str, suspect_id: Optional[str], context: Any) -> Dict[str, Any]:
        from src.society.information_networks import UnifiedInformationEngine
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else UnifiedInformationEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        incident_room = informant.location_id or (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")
        item = info_eng.report_crime_to_watch(informant, guard, crime_topic, crime_desc, suspect_id, incident_room, context, tick)
        return {"success": True, "action": "REPORT_CRIME_TO_WATCH", "report_item_id": item.item_id}

    @staticmethod
    def appraise_wealthy_mark(rogue: NPC, context: Any) -> Dict[str, Any]:
        from src.society.information_networks import UnifiedInformationEngine
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else UnifiedInformationEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        item = info_eng.appraise_wealthy_mark(rogue, context, tick)
        return {"success": item is not None, "action": "APPRAISE_WEALTHY_MARK", "target_item": item.to_dict() if item else None}

    @staticmethod
    def teach_apprentice_skill(master: NPC, apprentice: NPC, skill_name: str, context: Any) -> Dict[str, Any]:
        from src.society.information_networks import UnifiedInformationEngine
        info_eng = context.get_service("unified_information_engine") if hasattr(context, "get_service") else UnifiedInformationEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        res = info_eng.teach_vocational_skill(master, apprentice, skill_name, context, tick)
        return res

    @staticmethod
    def play_recreation_game(actor: NPC, opponent: NPC, game_id: str, context: Any, custom_wager: Optional[float] = None) -> Dict[str, Any]:
        """Bilateral recreation contest with attribute-derived win probabilities and wager transfers."""
        from src.society.recreation_games import RecreationGameEngine
        game_eng = context.get_service("recreation_game_engine") if hasattr(context, "get_service") else RecreationGameEngine.get_instance()
        can_play, reason = game_eng.evaluate_game_invitation(actor, opponent, game_id, context)
        if not can_play:
            return {"success": False, "action": "PLAY_RECREATION_GAME", "reason": reason}

        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        return game_eng.execute_contest(actor, opponent, game_id, context, tick=tick, custom_wager=custom_wager)

    @staticmethod
    def seek_spiritual_confession(penitent: NPC, priest: NPC, context: Any) -> Dict[str, Any]:
        """Penitent seeks spiritual confession in chapel with priest to absolve guilt."""
        from src.society.dilemmas_and_confession import MoralDilemmaEngine
        dil_eng = context.get_service("moral_dilemma_engine") if hasattr(context, "get_service") else MoralDilemmaEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        return dil_eng.seek_spiritual_confession(penitent, priest, context, tick=tick)

    @staticmethod
    def confide_secret(confider: NPC, confidant: NPC, secret_topic: str, context: Any) -> Dict[str, Any]:
        """Confides an agonizing secret with companion, relieving guilt with latent gossip leak risk."""
        from src.society.dilemmas_and_confession import MoralDilemmaEngine
        dil_eng = context.get_service("moral_dilemma_engine") if hasattr(context, "get_service") else MoralDilemmaEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        return dil_eng.confide_in_companion(confider, confidant, secret_topic, context, tick=tick)

    @staticmethod
    def participate_in_club(member: NPC, club_id: str, context: Any) -> Dict[str, Any]:
        """Participates in fraternal club gathering in designated meeting room."""
        from src.society.social_clubs import SocialClubEngine
        club_eng = context.get_service("social_club_engine") if hasattr(context, "get_service") else SocialClubEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        room_id = member.location_id or "room_tavern"
        res = club_eng.evaluate_club_gathering(club_id, room_id, context, tick)
        if res:
            return res
        return {"success": False, "action": "PARTICIPATE_IN_CLUB", "reason": "Insufficient members or outside meeting window"}
    @staticmethod
    def read_inscribed_carrier(reader: NPC, item_instance: ItemInstance, context: Any) -> Dict[str, Any]:
        """Reads an inscribed physical carrier (book, ledger, letter, note) and acquires knowledge."""
        from src.society.epistemic_engine import EpistemicEngine
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else EpistemicEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        return ep_eng.read_inscribed_carrier(reader, item_instance, context, current_tick=tick)

    @staticmethod
    def inscribe_note_or_letter(
        author: NPC,
        title: str,
        content: str,
        carrier_type_name: str,
        visibility_name: str,
        context: Any,
        recipient_id: Optional[str] = None,
        item_instance: Optional[ItemInstance] = None
    ) -> Dict[str, Any]:
        """Inscribes a physical note, letter, or ledger entry with structured epistemic atoms."""
        from src.society.epistemic_engine import EpistemicEngine, EpistemicStatus, VisibilityTier, CarrierType
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else EpistemicEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0

        c_type = CarrierType(carrier_type_name.upper()) if isinstance(carrier_type_name, str) else CarrierType.NOTE
        vis = VisibilityTier(visibility_name.upper()) if isinstance(visibility_name, str) else VisibilityTier.PRIVATE_DYADIC

        atom = ep_eng.create_atom(
            title=title,
            content=content,
            status=EpistemicStatus.FACT,
            visibility=vis,
            carrier_type=c_type,
            actor_id=author.id,
            subject_id=recipient_id,
            location_id=author.location_id,
            created_tick=tick,
            tags=["written", c_type.value.lower()]
        )
        ep_eng.impart_knowledge(author, atom, tick, salience=1.0)

        inst = item_instance
        if not inst:
            def_id = "parchment_letter" if c_type == CarrierType.LETTER else "smuggler_cipher_note"
            inst = ItemInstance(instance_id=f"item_{uuid.uuid4().hex[:8]}", item_def_id=def_id)
            author.inventory.append(inst)

        carrier = ep_eng.inscribe_physical_carrier(
            item_instance=inst,
            title=title,
            carrier_type=c_type,
            atoms=[atom],
            author_id=author.id,
            created_tick=tick
        )
        return {"success": True, "action": "INSCRIBE_CARRIER", "carrier": carrier.to_dict(), "item_instance": inst.to_dict()}

    @staticmethod
    def investigate_crime_scene(investigator: NPC, location_id: str, context: Any) -> Dict[str, Any]:
        """Investigates crime scene for physical forensic clues and forms suspect inferences."""
        from src.society.epistemic_engine import EpistemicEngine
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else EpistemicEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        clues = ep_eng.investigate_crime_scene(investigator, location_id, context, tick)
        return {"success": len(clues) > 0, "action": "INVESTIGATE_CRIME_SCENE", "clues_discovered_count": len(clues)}

    @staticmethod
    def reminisce_life_event(npc: NPC, context: Any) -> Dict[str, Any]:
        """Introspects and reminisces over pivotal high-emotion life event anchors."""
        from src.society.epistemic_engine import EpistemicEngine
        ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else EpistemicEngine.get_instance()
        tick = context.clock.current_tick if hasattr(context, "clock") and context.clock else 0
        outcome = ep_eng.reminisce_life_event(npc, context, tick)
        return {"success": outcome is not None, "action": "REMINISCE_PAST", "outcome": outcome}

