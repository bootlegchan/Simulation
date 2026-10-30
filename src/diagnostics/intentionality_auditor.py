"""
Intentionality Auditor:
Verifies that engine functions achieve their intended behavioral and social outcomes
(the 'WHY' and 'SO WHAT') rather than merely executing without syntax errors.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from src.entities.npc import NPC
from src.society.romance import InterpersonalBond, RelationshipStage
from src.society.affairs import ClandestineRendezvous, CommunitySideTakingEngine, AffairState
from src.society.friendships import FriendshipLifecycle
from src.society.cliques import Clique, CliqueManager
from src.society.domestic import HouseholdDynamics
from src.society.relationships import SocialNetwork
from src.npc.traits import PersonalityEvolution, RedemptionJourney
from src.economy.bargaining import OrderBook, OrderBookEntry, BargainingEngine
from src.economy.pricing import DynamicPricingEngine
from src.ai.utility import UtilityEvaluator

@dataclass
class IntentionalityAuditResult:
    subsystem_name: str
    target_function: str
    intended_behavioral_outcome: str
    test_scenario_description: str
    passed: bool
    observed_metrics: Dict[str, Any]
    failure_analysis: Optional[str] = None

class IntentionalityAuditor:
    """Evaluates whether core functions achieve their intended behavioral, social, and economic goals."""

    def __init__(self):
        self.results: List[IntentionalityAuditResult] = []

    def audit_affair_and_side_taking_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Exposed affair must trigger trust collapse, jealousy, and community side-taking."""
        betrayed = NPC("npc_aldous", "Aldous Miller", personality={"conscientiousness": 0.8, "openness": 0.4})
        culprit = NPC("npc_beatrice", "Beatrice Vance", personality={"conscientiousness": 0.4, "openness": 0.7})
        lover = NPC("npc_silas", "Silas Tavernier", personality={"conscientiousness": 0.3, "openness": 0.8})
        friend = NPC("npc_eamon", "Eamon Forge", personality={"conscientiousness": 0.9, "openness": 0.5})

        npcs = {npc.id: npc for npc in [betrayed, culprit, lover, friend]}
        social_net = SocialNetwork()
        social_net.set_relationship(friend.id, betrayed.id, 60.0)
        social_net.set_relationship(friend.id, culprit.id, 40.0)

        # 1. Rendezvous discovery
        rendezvous = ClandestineRendezvous(culprit.id, lover.id, secret_location_id="room_chapel_vault")
        discovery = rendezvous.evaluate_discovery_risk(
            current_room_id="room_village_square",
            co_located_npc_ids=[culprit.id, lover.id, betrayed.id],
            primary_partner_ids=[betrayed.id]
        )

        # 2. Side-taking
        sides = CommunitySideTakingEngine.resolve_community_reaction(
            betrayed_id=betrayed.id,
            culprit_id=culprit.id,
            mutual_friend_ids=[friend.id],
            npcs=npcs,
            social_network=social_net
        )

        # Intent Verification
        is_exposed = discovery["is_exposed"] and discovery["caught_by_partner"]
        friend_sided_with_betrayed = friend.id in sides[betrayed.id]
        culprit_rel_damaged = social_net.get_relationship(friend.id, culprit.id) < 40.0

        passed = is_exposed and friend_sided_with_betrayed and culprit_rel_damaged

        metrics = {
            "is_exposed": is_exposed,
            "friend_sides": sides,
            "culprit_relationship_after": social_net.get_relationship(friend.id, culprit.id)
        }

        result = IntentionalityAuditResult(
            subsystem_name="Society / Romance & Affairs",
            target_function="ClandestineRendezvous.evaluate_discovery_risk & CommunitySideTakingEngine.resolve_community_reaction",
            intended_behavioral_outcome="Exposed affair triggers direct partner discovery and causes conscientious friends to side with betrayed party.",
            test_scenario_description="Spouse catches partner in affair; mutual friend Eamon evaluates who to support.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Affair exposure failed to trigger partner discovery or community side-taking."
        )
        self.results.append(result)
        return result

    def audit_friendship_drifting_and_milestones_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Social drifting decays unmaintained friendships, but crisis milestones act as a protective cushion."""
        bond_normal = FriendshipLifecycle("npc_a", "npc_b")
        bond_milestone = FriendshipLifecycle("npc_a", "npc_c")

        # Record a shared crisis milestone (e.g. surviving a winter famine together)
        bond_milestone.record_crisis_milestone("Survived Winter Famine", tick=100, bonus=30.0)

        # Simulate 20 days of drifting
        for _ in range(20):
            bond_normal.apply_social_drifting()
            bond_milestone.apply_social_drifting()

        # Intent Verification: The milestone bond must retain higher strength than normal bond
        passed = bond_milestone.bond_strength > bond_normal.bond_strength

        metrics = {
            "normal_bond_strength_after_20_days": round(bond_normal.bond_strength, 2),
            "milestone_bond_strength_after_20_days": round(bond_milestone.bond_strength, 2)
        }

        result = IntentionalityAuditResult(
            subsystem_name="Society / Friendship Lifecycles",
            target_function="FriendshipLifecycle.apply_social_drifting & record_crisis_milestone",
            intended_behavioral_outcome="Friendship strength decays without interaction, but shared crisis milestones provide permanent retention cushioning.",
            test_scenario_description="Compare 20 days of social drifting between a standard friendship and a crisis-bonded friendship.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Milestone bond did not retain higher strength than normal drifting bond."
        )
        self.results.append(result)
        return result

    def audit_clique_peer_pressure_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Clique consensus forces individual members to conform, shifting personal stances toward group norm."""
        leader = NPC("npc_devon", "Devon Blackwood", personality={"conscientiousness": 0.8})
        member = NPC("npc_roderick", "Roderick Steel", personality={"conscientiousness": 0.9})
        target = NPC("npc_eamon", "Eamon Forge", personality={"conscientiousness": 0.5})

        npcs = {n.id: n for n in [leader, member, target]}
        social_net = SocialNetwork()
        social_net.set_relationship(leader.id, target.id, -80.0)  # Leader hates target
        social_net.set_relationship(member.id, target.id, 20.0)   # Member originally neutral/friendly

        clique = Clique("clique_council", "Elite Council", leader_id=leader.id, member_ids=[leader.id, member.id])
        clique.update_consensus(target.id, npcs, social_net)

        pressure_res = clique.evaluate_peer_pressure(member.id, target.id, npcs, social_net)

        # Intent Verification: Member's relationship score toward target must shift negatively toward group consensus
        new_rel = social_net.get_relationship(member.id, target.id)
        passed = pressure_res["conformed"] and new_rel < 20.0

        metrics = {
            "leader_stance": -80.0,
            "member_stance_before": 20.0,
            "member_stance_after": new_rel,
            "opinion_shift": pressure_res.get("opinion_shift", 0.0)
        }

        result = IntentionalityAuditResult(
            subsystem_name="Society / Cliques & Peer Pressure",
            target_function="Clique.evaluate_peer_pressure & update_consensus",
            intended_behavioral_outcome="Group consensus led by clique leader pressures individual members to conform, shifting their individual relationships toward group stance.",
            test_scenario_description="Elite Council leader dislikes Eamon (-80); member Roderick is pressured to conform.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Peer pressure failed to shift member's stance toward clique consensus."
        )
        self.results.append(result)
        return result

    def audit_domestic_friction_and_eviction_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Incompatible personalities + high need stress causes domestic friction, culminating in breakup and eviction."""
        npc_a = NPC("npc_devon", "Mayor Devon", wealth=100.0, personality={"conscientiousness": 0.9, "openness": 0.2})
        npc_b = NPC("npc_silas", "Silas Bard", wealth=20.0, personality={"conscientiousness": 0.1, "openness": 0.9})
        npcs = {npc_a.id: npc_a, npc_b.id: npc_b}

        # Apply high need stress (fatigue + hunger)
        npc_a.needs = {"hunger": 80.0, "energy": 20.0, "social": 50.0}
        npc_b.needs = {"hunger": 80.0, "energy": 20.0, "social": 50.0}

        household = HouseholdDynamics("room_vance_manor", [npc_a.id, npc_b.id])
        friction = household.evaluate_domestic_harmony(npcs)

        eviction_res = household.process_breakup_and_eviction(npc_a, npc_b, lodging_fallback_id="room_tavern_lodging")

        # Intent Verification: Incompatible traits under stress produce friction > 50; lower-prestige/wealth partner is evicted
        passed = friction >= 50.0 and eviction_res["evicted_npc_id"] == npc_b.id and npc_b.home_location_id == "room_tavern_lodging"

        metrics = {
            "domestic_friction_score": friction,
            "evicted_npc": eviction_res["evicted_npc_name"],
            "evicted_new_home": npc_b.home_location_id
        }

        result = IntentionalityAuditResult(
            subsystem_name="Society / Domestic Living Dynamics",
            target_function="HouseholdDynamics.evaluate_domestic_harmony & process_breakup_and_eviction",
            intended_behavioral_outcome="Household trait mismatches under need stress create high domestic friction, leading to eviction of the lower-prestige partner to tavern lodgings.",
            test_scenario_description="Mayor Devon (high conscientiousness) lives with Silas (low conscientiousness) under hunger/fatigue stress.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Domestic friction failed to score high or lower-prestige partner was not evicted properly."
        )
        self.results.append(result)
        return result

    def audit_trait_evolution_and_redemption_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Surviving betrayal trauma permanently shifts personality traits; public penance/apologies decay social hostility."""
        npc = NPC("npc_aldous", "Aldous Miller", personality={"openness": 0.6, "conscientiousness": 0.5}, wealth=100.0)
        social_net = SocialNetwork()
        social_net.set_relationship("npc_victim", npc.id, -60.0)

        # 1. Trait shift from betrayal
        new_traits = PersonalityEvolution.process_betrayal_trauma(npc, betrayal_severity=80.0)

        # 2. Redemption journey
        redemption = RedemptionJourney(npc.id)
        apology_res = redemption.offer_public_apology("npc_victim", social_net)

        # Intent Verification: Openness drops due to betrayal; apology increases relationship score
        openness_decreased = new_traits["openness"] < 0.6
        relationship_improved = social_net.get_relationship("npc_victim", npc.id) > -60.0

        passed = openness_decreased and relationship_improved

        metrics = {
            "openness_before": 0.6,
            "openness_after": new_traits["openness"],
            "victim_relationship_after_apology": social_net.get_relationship("npc_victim", npc.id)
        }

        result = IntentionalityAuditResult(
            subsystem_name="NPC / Personality Evolution & Redemption",
            target_function="PersonalityEvolution.process_betrayal_trauma & RedemptionJourney.offer_public_apology",
            intended_behavioral_outcome="Betrayal trauma reduces openness (increasing paranoia/caution), while public apologies restore victim relationship standing.",
            test_scenario_description="Aldous suffers betrayal trauma, then undertakes public penance to restore social standing.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Trait evolution failed to shift openness or apology failed to improve relationship."
        )
        self.results.append(result)
        return result

    def audit_utility_override_intent(self) -> IntentionalityAuditResult:
        """Intended Goal: Extreme hunger/fatigue urgency must dynamically override routine work schedules."""
        needs_starving = {"hunger": 95.0, "energy": 50.0, "social": 50.0}
        utilities = UtilityEvaluator.evaluate_drives(needs_starving)

        # Convert to Softmax probabilities
        probs = UtilityEvaluator.calculate_softmax_probabilities(utilities)

        # Intent Verification: Hunger drive probability must dominate (> 80%) over other drives
        passed = probs.get("satisfy_hunger", 0.0) > 0.80

        metrics = {
            "hunger_utility": round(utilities.get("satisfy_hunger", 0.0), 2),
            "hunger_choice_probability": f"{round(probs.get('satisfy_hunger', 0.0) * 100, 1)}%",
            "rest_choice_probability": f"{round(probs.get('rest', 0.0) * 100, 1)}%"
        }

        result = IntentionalityAuditResult(
            subsystem_name="AI / Utility Evaluator & Softmax Choice",
            target_function="UtilityEvaluator.evaluate_drives & calculate_softmax_probabilities",
            intended_behavioral_outcome="Critical biological need levels (95/100 hunger) yield > 80% choice probability, overriding routine work goals.",
            test_scenario_description="Evaluate Softmax choice probabilities for an NPC experiencing 95/100 hunger.",
            passed=passed,
            observed_metrics=metrics,
            failure_analysis=None if passed else "Critical hunger failed to yield > 80% Softmax choice probability."
        )
        self.results.append(result)
        return result

    def run_all_intentionality_audits(self) -> List[IntentionalityAuditResult]:
        """Execute complete suite of behavioral intentionality audits."""
        self.results.clear()
        self.audit_affair_and_side_taking_intent()
        self.audit_friendship_drifting_and_milestones_intent()
        self.audit_clique_peer_pressure_intent()
        self.audit_domestic_friction_and_eviction_intent()
        self.audit_trait_evolution_and_redemption_intent()
        self.audit_utility_override_intent()
        return self.results
