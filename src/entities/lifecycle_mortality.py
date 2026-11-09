"""
Continuous Somatic Mortality, Demise, and Inheritance Succession Engine.
Operates on continuous physiological thresholds (starvation, freezing exposure, cardiovascular collapse)
without artificial invulnerability.
"""
from typing import Any, Dict, List, Optional
import math

class DemiseEngine:
    """
    Evaluates mortal biological hazards and handles inheritance, grief,
    and municipal obituary notices when citizens succumb.
    """
    _instance: Optional["DemiseEngine"] = None

    @classmethod
    def get_instance(cls) -> "DemiseEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.demise_history: List[Dict[str, Any]] = []
        self.total_deaths_count: int = 0

    def evaluate_mortal_risks(
        self,
        npc: Any,
        tick: int,
        context: Any,
        delta_ticks: int = 1
    ) -> Optional[str]:
        """
        Continuous mortality hazard assessment:
        1. Prolonged Acute Starvation (hunger >= 95.0)
        2. Severe Hypothermic Exposure (unheated freezing room < -2°C + exhaustion)
        3. Extreme Somatic Shock (stress >= 98.0 + exhaustion <= 2.0)
        """
        if not getattr(npc, "is_alive", True):
            return None

        hunger = float(npc.needs.get("hunger", 0.0))
        energy = float(npc.needs.get("energy", 100.0))
        stress = float(npc.get_feeling("stress"))
        room_temp = getattr(npc, "_current_room_temperature", 18.0)

        # 1. Starvation hazard
        if hunger >= 95.0:
            deficit = (hunger - 95.0) / 5.0
            hazard = (deficit ** 1.5) * 0.04 * (delta_ticks / 60.0)
            if context.random.random() < hazard:
                return "STARVATION"

        # 2. Hypothermic Freezing Exposure
        if room_temp < -2.0 and energy <= 5.0:
            freeze_severity = abs(room_temp) / 10.0
            hazard = freeze_severity * 0.05 * (delta_ticks / 60.0)
            if context.random.random() < hazard:
                return "HYPOTHERMIC_EXPOSURE"

        # 3. Cardiovascular Shock
        if stress >= 98.0 and energy <= 2.0:
            hazard = 0.03 * (delta_ticks / 60.0)
            if context.random.random() < hazard:
                return "CARDIAC_COLLAPSE"

        return None

    def execute_demise_and_succession(
        self,
        npc: Any,
        cause: str,
        tick: int,
        context: Any
    ) -> Dict[str, Any]:
        """
        Executes mortal demise:
        1. Sets state to DECEASED and clears action horizons.
        2. Liquidates estate / transfers inheritance to spouse or escheat to Treasury.
        3. Inflicts bereavement grief on surviving spouse and close acquaintances.
        4. Publishes public obituary to civic notice boards.
        """
        npc.current_state = "DECEASED"
        npc.current_action = "DECEASED"
        if hasattr(npc, "intent_horizon"):
            npc.intent_horizon = None

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        loc_id = npc.location_id or "room_village_square"

        # 1. Biographical record
        npc.record_biographical_entry(
            tick, time_iso, "DEMISE",
            f"Passed away due to {cause.lower().replace('_', ' ')} at {loc_id}."
        )

        # 2. Inheritance and estate transfer
        estate_wealth = float(getattr(npc, "wealth", 0.0))
        heir_name = "None"
        spouse_id = npc.social_profile.get("spouse_id") if hasattr(npc, "social_profile") else None
        spouse = context.npcs.get(spouse_id) if (spouse_id and hasattr(context, "npcs")) else None

        if estate_wealth > 0:
            if spouse and getattr(spouse, "is_alive", True):
                spouse.wealth = round(spouse.wealth + estate_wealth, 2)
                heir_name = spouse.name
                spouse.record_biographical_entry(
                    tick, time_iso, "INHERITANCE_RECEIVED",
                    f"Inherited the estate of {estate_wealth:.2f}g following the passing of spouse {npc.name}."
                )
            elif hasattr(context, "municipal_treasury") and context.municipal_treasury:
                treasury = context.municipal_treasury
                treasury.balance = round(treasury.balance + estate_wealth, 2)
                heir_name = "Municipal Treasury (Escheat)"

            npc.wealth = 0.0

        # 3. Lodge Bereavement Benefits
        aid_eng = context.get_service("fraternal_aid_engine") if hasattr(context, "get_service") else None
        if aid_eng and hasattr(aid_eng, "disburse_bereavement_benefit") and spouse:
            aid_eng.disburse_bereavement_benefit(npc, spouse, context, tick)

        # 4. Bereavement grief to relations
        if spouse and getattr(spouse, "is_alive", True):
            spouse.adjust_feeling("grief", 65.0)
            spouse.adjust_feeling("loneliness", 50.0)
            spouse.adjust_feeling("stress", 30.0)

        if hasattr(context, "npcs"):
            op_eng = context.get_service("directional_opinion_engine")
            for other in context.npcs.values():
                if other.id != npc.id and getattr(other, "is_alive", True):
                    affinity = op_eng.get_net_opinion(other.id, npc.id) if op_eng and hasattr(op_eng, "get_net_opinion") else 0.0
                    if affinity > 40.0:
                        other.adjust_feeling("grief", 25.0)

        # 4. Public Obituary Notice on Civic Notice Board
        info_eng = context.get_service("unified_information_engine")
        if info_eng and hasattr(info_eng, "publish_item"):
            public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
            from src.society.information_networks import InformationChannelType
            info_eng.publish_item(
                channel=InformationChannelType.CIVIC_NOTICES,
                topic="MUNICIPAL_OBITUARY",
                headline=f"Town Obituary: Passing of {npc.name}",
                content=f"The settlement mourns {npc.name} ({npc.occupation}), who succumbed to {cause.lower().replace('_', ' ')} at {loc_id}.",
                source_npc_id=None,
                target_location_id=public_plaza,
                current_tick=tick,
                custom_duration=14400,
                context=context
            )

        demise_record = {
            "npc_id": npc.id,
            "name": npc.name,
            "occupation": npc.occupation,
            "cause": cause,
            "tick": tick,
            "estate_wealth": estate_wealth,
            "heir": heir_name
        }
        self.demise_history.append(demise_record)
        self.total_deaths_count += 1
        return demise_record
