"""
Dynamic Life Goals, Long-Term Aspirations, and Aspirational Steering.
Operates 100% on declarative configurations from data/settings/life_goals.json.
Models multi-attribute goal progression, fulfillment milestone awards,
ongoing lifelong maintenance aspirations (e.g. Devoted Spouse), and continuous utility steering biases.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

@dataclass
class LifeGoalSpec:
    goal_id: str
    name: str
    description: str
    goal_type: str = "ACHIEVEMENT"       # "ACHIEVEMENT" or "ONGOING_MAINTENANCE"
    target_wealth_gold: float = 0.0
    target_primary_skill: float = 0.0
    target_crafted_goods: int = 0
    target_trades_count: int = 0
    target_civic_standing: float = 0.0
    target_piety_standing: float = 0.0
    target_spousal_affection: float = 0.0
    target_contentment: float = 0.0
    target_crimes_committed: int = 0
    target_career_earnings_gold: float = 0.0
    max_tolerated_spousal_resentment: float = 15.0
    daily_maintenance_pride: float = 8.0
    utility_modifiers: Dict[str, float] = field(default_factory=dict)
    fulfillment_points_on_completion: float = 30.0

    @property
    def id(self) -> str:
        return self.goal_id


class LifeGoalEngine:
    """
    Central Life Goals & Aspirational Engine.
    Assigns character aspirations, calculates continuous completion percentages,
    tracks ongoing maintenance goals (Devoted Spouse, Community Pillar),
    applies aspirational utility steering modifiers, and grants fulfillment achievements.
    """
    _instance: Optional["LifeGoalEngine"] = None

    @classmethod
    def get_instance(cls) -> "LifeGoalEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.goals: Dict[str, LifeGoalSpec] = {}
        self.agent_goals: Dict[str, str] = {} # npc_id -> goal_id
        self.completed_milestones: Dict[str, Set[str]] = {} # npc_id -> set of milestone_ids
        self.ongoing_days_maintained: Dict[str, int] = {} # npc_id -> days maintained
        self.total_milestones_achieved: int = 0
        self.total_ongoing_cycles_maintained: int = 0
        self.total_aspiration_strains_count: int = 0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        cfg = SettingsRegistry.get_instance().get("life_goals")
        g_defs = cfg.get("life_goals", {})
        self.goals.clear()

        for g_id, data in g_defs.items():
            self.goals[g_id] = LifeGoalSpec(
                goal_id=g_id,
                name=data.get("name", "Life Aspiration"),
                description=data.get("description", ""),
                goal_type=data.get("goal_type", "ACHIEVEMENT"),
                target_wealth_gold=float(data.get("target_wealth_gold", 0.0)),
                target_primary_skill=float(data.get("target_primary_skill", 0.0)),
                target_crafted_goods=int(data.get("target_crafted_goods", 0)),
                target_trades_count=int(data.get("target_trades_count", 0)),
                target_civic_standing=float(data.get("target_civic_standing", 0.0)),
                target_piety_standing=float(data.get("target_piety_standing", 0.0)),
                target_spousal_affection=float(data.get("target_spousal_affection", 0.0)),
                target_contentment=float(data.get("target_contentment", 0.0)),
                target_crimes_committed=int(data.get("target_crimes_committed", 0)),
                target_career_earnings_gold=float(data.get("target_career_earnings_gold", 0.0)),
                max_tolerated_spousal_resentment=float(data.get("max_tolerated_spousal_resentment", 15.0)),
                daily_maintenance_pride=float(data.get("daily_maintenance_pride", 8.0)),
                utility_modifiers=dict(data.get("utility_modifiers", {})),
                fulfillment_points_on_completion=float(data.get("fulfillment_points_on_completion", 30.0))
            )

    def assign_goals(self, context: Any) -> None:
        """Assigns continuous life aspirations based on character vocation, personality, and social role."""
        if not hasattr(context, "npcs") or not context.npcs:
            return
        if not self.goals:
            self._load_from_settings()

        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            if npc.id in self.agent_goals:
                continue

            occ = (getattr(npc, "occupation", "") or "").lower()
            vices = getattr(npc, "vices", {}) or {}
            sp = getattr(npc, "social_profile", {}) or {}
            crime_prop = float(vices.get("crime_propensity", 0.0))
            has_partner = bool(sp.get("spouse_id") or sp.get("partner_id"))

            chosen_goal = "DEVOTED_SPOUSE" if has_partner else "PILLAR_OF_THE_COMMUNITY"

            if crime_prop >= 40.0 or any(k in occ for k in ("smuggler", "scavenger", "outlaw", "thief")):
                chosen_goal = "OUTLAW_KINGPIN"
            elif any(k in occ for k in ("merchant", "trader", "innkeeper", "shop")):
                chosen_goal = "DYNASTIC_MERCHANT"
            elif any(k in occ for k in ("smith", "blacksmith", "carpenter", "baker", "miller", "farmer", "weaver", "mason")):
                chosen_goal = "MASTER_ARTISAN"
            elif any(k in occ for k in ("mayor", "notary", "clerk", "guard", "sheriff")):
                chosen_goal = "CIVIC_PATRICIAN"
            elif any(k in occ for k in ("priest", "healer", "midwife")):
                chosen_goal = "PILLAR_OF_THE_COMMUNITY"
            elif has_partner:
                chosen_goal = "DEVOTED_SPOUSE"

            self.agent_goals[npc.id] = chosen_goal

    def get_agent_goal(self, npc_id: str) -> Optional[LifeGoalSpec]:
        g_id = self.agent_goals.get(npc_id)
        # Backward compatibility for DEVOTED_HOUSEHOLD -> DEVOTED_SPOUSE
        if g_id == "DEVOTED_HOUSEHOLD" and "DEVOTED_SPOUSE" in self.goals:
            return self.goals["DEVOTED_SPOUSE"]
        return self.goals.get(g_id) if g_id else None

    def calculate_progress(self, npc: Any, context: Optional[Any] = None) -> float:
        """
        Calculates continuous progress toward the NPC's life aspiration (0.0 to 1.0).
        """
        goal = self.get_agent_goal(npc.id)
        if not goal:
            return 0.0

        ratios: List[float] = []

        if goal.target_wealth_gold > 0:
            ratios.append(min(1.0, float(getattr(npc, "wealth", 0.0)) / goal.target_wealth_gold))

        if goal.target_career_earnings_gold > 0:
            earnings = float(getattr(npc, "career_statistics", {}).get("career_earnings_gold", 0.0))
            ratios.append(min(1.0, earnings / goal.target_career_earnings_gold))

        if goal.target_primary_skill > 0:
            skills = getattr(npc, "skills", {}) or {}
            top_skill = max(skills.values()) if skills else 15.0
            ratios.append(min(1.0, top_skill / goal.target_primary_skill))

        if goal.target_crafted_goods > 0:
            crafted = int(getattr(npc, "career_statistics", {}).get("goods_crafted_count", 0))
            ratios.append(min(1.0, crafted / goal.target_crafted_goods))

        if goal.target_crimes_committed > 0:
            crimes = int(getattr(npc, "career_statistics", {}).get("crimes_committed", 0))
            ratios.append(min(1.0, crimes / goal.target_crimes_committed))

        if goal.target_civic_standing > 0:
            sp = getattr(npc, "social_profile", {}) or {}
            standing = float(sp.get("reputation_facets", {}).get("civic_standing", 50.0))
            ratios.append(min(1.0, standing / goal.target_civic_standing))

        if goal.target_piety_standing > 0:
            sp = getattr(npc, "social_profile", {}) or {}
            piety = float(sp.get("reputation_facets", {}).get("moral_piety", 50.0))
            ratios.append(min(1.0, piety / goal.target_piety_standing))

        if goal.target_contentment > 0:
            cont = float(getattr(npc, "feelings", {}).get("contentment", 50.0))
            ratios.append(min(1.0, cont / goal.target_contentment))

        # Ongoing Devoted Spouse & Household Harmony Evaluation
        if goal.target_spousal_affection > 0:
            sp = getattr(npc, "social_profile", {}) or {}
            spouse_id = sp.get("spouse_id") or sp.get("partner_id")
            if context and hasattr(context, "npcs") and spouse_id and spouse_id in context.npcs:
                rom_eng = context.get_service("romance_engine")
                if rom_eng and hasattr(rom_eng, "get_or_create_bond"):
                    bond = rom_eng.get_or_create_bond(npc.id, spouse_id, context=context)
                    affect_ratio = min(1.0, bond.romantic_affection / goal.target_spousal_affection)

                    spouse = context.npcs[spouse_id]
                    s_resent = float(spouse.get_feeling("resentment")) if hasattr(spouse, "get_feeling") else 0.0
                    if s_resent > goal.max_tolerated_spousal_resentment:
                        penalty = (s_resent - goal.max_tolerated_spousal_resentment) / 30.0
                        affect_ratio = max(0.0, affect_ratio - penalty)

                    s_grief = float(spouse.get_feeling("grief")) if hasattr(spouse, "get_feeling") else 0.0
                    if s_grief > 25.0:
                        affect_ratio *= 0.70

                    ratios.append(round(affect_ratio, 3))
                    # Spousal harmony ratio (penalized directly by spouse's resentment)
                    harmony_ratio = max(0.0, 1.0 - (s_resent / 40.0))
                    ratios.append(round(harmony_ratio, 3))
                else:
                    ratios.append(0.50)
            else:
                # No spouse -> cannot fulfill devoted spouse aspiration
                ratios.append(0.0)

        if not ratios:
            return 0.50

        return round(sum(ratios) / len(ratios), 3)

    def get_utility_steering_modifiers(self, npc: Any) -> Dict[str, float]:
        """Returns multiplicative utility steering modifiers declared for this character's life goal."""
        goal = self.get_agent_goal(npc.id)
        if not goal:
            return {}
        return dict(goal.utility_modifiers)

    def evaluate_milestones(self, context: Any, current_tick: int) -> List[Dict[str, Any]]:
        """
        Evaluates long-term aspiration progression:
        - For Achievement goals: awards 50% Halfway and 100% Completion milestones.
        - For Ongoing Maintenance goals: awards daily sustained fulfillment or triggers aspiration strain on lapse.
        """
        if not hasattr(context, "npcs") or not context.npcs:
            return []

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"
        achievements = []

        cfg = SettingsRegistry.get_instance().get("life_goals").get("aspiration_dynamics", {})
        maint_thresh = float(cfg.get("ongoing_maintenance_threshold", 0.80))
        strain_thresh = float(cfg.get("ongoing_strain_threshold", 0.40))

        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            goal = self.get_agent_goal(npc.id)
            if not goal:
                continue

            progress = self.calculate_progress(npc, context)
            milestones = self.completed_milestones.setdefault(npc.id, set())

            # -------------------------------------------------------------
            # A. Ongoing Lifelong Maintenance Goals (Devoted Spouse, Pillar)
            # -------------------------------------------------------------
            if goal.goal_type == "ONGOING_MAINTENANCE":
                if progress >= maint_thresh:
                    # Successfully sustained today!
                    days = self.ongoing_days_maintained.get(npc.id, 0) + 1
                    self.ongoing_days_maintained[npc.id] = days
                    self.total_ongoing_cycles_maintained += 1

                    npc.adjust_feeling("pride", goal.daily_maintenance_pride)
                    npc.adjust_feeling("contentment", 6.0)
                    if hasattr(npc, "fulfillment") and hasattr(npc.fulfillment, "add_score"):
                        npc.fulfillment.add_score("legacy", 0.5)

                    if days % 7 == 0:
                        npc.record_biographical_entry(
                            current_tick, time_iso, "ONGOING_GOAL_MAINTAINED",
                            f"Faithfully maintained lifelong aspiration as '{goal.name}' for {days} days (progress: {progress * 100:.1f}%)."
                        )
                        achievements.append({"npc_id": npc.id, "type": "ONGOING_MAINTAINED", "goal": goal.name, "days": days})

                elif progress < strain_thresh:
                    # Aspiration Strain / Crisis!
                    self.total_aspiration_strains_count += 1
                    self.ongoing_days_maintained[npc.id] = 0
                    npc.adjust_feeling("stress", 12.0)
                    npc.adjust_feeling("guilt", 10.0)
                    npc.record_biographical_entry(
                        current_tick, time_iso, "ASPIRATION_STRAIN",
                        f"Suffered agonizing strain in lifelong aspiration '{goal.name}': domestic friction and unmet standards (progress: {progress * 100:.1f}%)."
                    )
                    achievements.append({"npc_id": npc.id, "type": "ASPIRATION_STRAIN", "goal": goal.name, "progress": progress})

            # -------------------------------------------------------------
            # B. Standard Achievement Milestones (Guildmaster, Patrician)
            # -------------------------------------------------------------
            else:
                # Halfway milestone (50%)
                if progress >= 0.50 and "HALFWAY" not in milestones:
                    milestones.add("HALFWAY")
                    npc.adjust_feeling("contentment", 15.0)
                    npc.adjust_feeling("pride", 15.0)
                    self.total_milestones_achieved += 1
                    npc.record_biographical_entry(
                        current_tick, time_iso, "LIFE_MILESTONE_ACHIEVED",
                        f"Surpassed halfway mark (50%) toward life aspiration '{goal.name}'."
                    )
                    achievements.append({"npc_id": npc.id, "milestone": "HALFWAY", "goal": goal.name})

                # Full completion milestone (100%)
                if progress >= 1.0 and "COMPLETED" not in milestones:
                    milestones.add("COMPLETED")
                    npc.adjust_feeling("contentment", 25.0)
                    npc.adjust_feeling("pride", 30.0)
                    if hasattr(npc, "fulfillment") and hasattr(npc.fulfillment, "add_score"):
                        npc.fulfillment.add_score("legacy", goal.fulfillment_points_on_completion)
                    self.total_milestones_achieved += 1
                    npc.record_biographical_entry(
                        current_tick, time_iso, "LIFE_GOAL_FULFILLED",
                        f"Triumphantly fulfilled lifelong aspiration '{goal.name}'! Awarded {goal.fulfillment_points_on_completion} fulfillment points."
                    )
                    achievements.append({"npc_id": npc.id, "milestone": "COMPLETED", "goal": goal.name})

        return achievements
