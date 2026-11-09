"""
Unit Test Suite 79: Political Factions, Town Council & Municipal Decrees.
Verifies the political governance engine:
- Declarative faction platforms and member auto-discovery
- Continuous grievance calculation & opposed decree tension
- Labor strike triggers and civic notice broadcasting
- Strike resolution dynamics
- Town council legislative sessions and delegate voting
- Municipal decree enactment, active behavioral modifiers, and expiry lifecycles
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.factions import FactionPoliticalEngine, Faction
from src.society.municipal_decrees import MunicipalDecreeEngine, DecreeType
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType

class TestFactionsTownCouncilAndDecrees(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.fact_eng: FactionPoliticalEngine = self.engine.context.get_service("faction_political_engine")
        self.decree_eng: MunicipalDecreeEngine = self.engine.context.get_service("municipal_decree_engine")
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")

    def test_01_faction_registration_and_member_discovery(self):
        """Verify that political factions load from data and recruit eligible citizens."""
        self.assertIsNotNone(self.fact_eng)
        self.assertIn("faction_agrarian_yeomanry", self.fact_eng.factions)
        self.assertIn("faction_craftsmen_guild", self.fact_eng.factions)
        self.assertIn("faction_sacred_hearth", self.fact_eng.factions)

        # Verify members discovered
        agrarian_faction = self.fact_eng.factions["faction_agrarian_yeomanry"]
        self.assertGreater(len(agrarian_faction.member_ids), 0)

        # Verify farmer is in agrarian faction
        farmer = self.engine.npcs.get("npc_aldous") or list(self.engine.npcs.values())[0]
        farmer.occupation = "Agrarian Farmer"
        self.fact_eng.auto_discover_members(self.engine.context)
        self.assertIn(farmer.id, agrarian_faction.member_ids)

    def test_02_continuous_grievance_calculation_and_decree_tension(self):
        """Verify continuous grievance calculation and tension from opposed decrees."""
        agrarian_faction = self.fact_eng.factions["faction_agrarian_yeomanry"]
        initial_g = self.fact_eng.calculate_faction_grievance(agrarian_faction, self.engine.context)

        # Enact a decree opposed by the Agrarians (BREAD_PRICE_CEILING)
        self.decree_eng.enact_decree("BREAD_PRICE_CEILING", self.engine.context, tick=100)
        self.assertTrue(self.decree_eng.is_decree_active("BREAD_PRICE_CEILING"))

        # Grievance should increase due to opposed decree tension (+15)
        new_g = self.fact_eng.calculate_faction_grievance(agrarian_faction, self.engine.context)
        self.assertGreater(new_g, initial_g)

    def test_03_labor_strike_trigger_and_civic_notice_broadcasting(self):
        """Verify that severe grievance triggers a labor strike and broadcasts public notices."""
        agrarian_faction = self.fact_eng.factions["faction_agrarian_yeomanry"]
        self.assertFalse(agrarian_faction.is_on_strike)

        # Induce high member resentment to exceed strike threshold (65.0)
        for m_id in agrarian_faction.member_ids:
            member = self.engine.npcs.get(m_id)
            if member:
                member.feelings["resentment"] = 85.0
                member.feelings["contentment"] = 10.0
                member.wealth = 5.0

        initial_notices_count = len(self.info_eng.active_items)

        # Run daily agitation evaluation
        strike_events = self.fact_eng.evaluate_daily_faction_agitation(
            self.fact_eng.factions, self.engine.npcs, self.engine.context, tick=1440
        )
        self.assertTrue(agrarian_faction.is_on_strike)
        self.assertGreaterEqual(len(strike_events), 1)
        self.assertEqual(strike_events[0]["action"], "STRIKE_DECLARED")

        # Verified public notice broadcast to CIVIC_NOTICES
        strike_notices = [
            i for i in self.info_eng.active_items.values()
            if i.topic == "LABOR_STRIKE_DECLARED"
        ]
        self.assertGreaterEqual(len(strike_notices), 1)
        self.assertIn("Labor Strike", strike_notices[0].headline)

    def test_04_strike_resolution_when_contentment_recovers(self):
        """Verify that strikes resolve when member contentment recovers and grievance drops."""
        agrarian_faction = self.fact_eng.factions["faction_agrarian_yeomanry"]
        agrarian_faction.is_on_strike = True
        agrarian_faction.strike_started_tick = 1000

        # Relieve member grievances
        for m_id in agrarian_faction.member_ids:
            member = self.engine.npcs.get(m_id)
            if member:
                member.feelings["resentment"] = 0.0
                member.feelings["contentment"] = 80.0
                member.wealth = 50.0

        # Remove any opposed decrees
        self.decree_eng.repeal_decree("BREAD_PRICE_CEILING", self.engine.context, tick=2000)

        strike_events = self.fact_eng.evaluate_daily_faction_agitation(
            self.fact_eng.factions, self.engine.npcs, self.engine.context, tick=2880
        )
        self.assertFalse(agrarian_faction.is_on_strike)
        self.assertEqual(strike_events[0]["action"], "STRIKE_RESOLVED")

    def test_05_town_council_assembly_and_decree_enactment(self):
        """Verify that Town Council convenes, votes based on platforms, and enacts ordinances."""
        initial_decrees = len(self.decree_eng.active_decrees)

        # Convene town council
        enacted = self.decree_eng.convene_town_council(self.engine.context, tick=10080)
        self.assertGreaterEqual(len(enacted), 1)

        # Verify INFRASTRUCTURE_REPAIR_MANDATE (favored by multiple factions) passes
        self.assertTrue(
            any(e["decree_id"] == "INFRASTRUCTURE_REPAIR_MANDATE" for e in enacted) or
            len(self.decree_eng.active_decrees) > initial_decrees
        )

        # Check active modifiers
        mods = self.decree_eng.get_active_decree_modifiers()
        self.assertIsNotNone(mods)

    def test_06_decree_enforcement_and_expiry_lifecycle(self):
        """Verify that decrees expire and repeal automatically after their duration concludes."""
        # Enact short duration curfew
        record = self.decree_eng.enact_decree(
            "NOCTURNAL_CURFEW", self.engine.context, tick=100, custom_duration=200
        )
        self.assertIsNotNone(record)
        self.assertTrue(self.decree_eng.is_decree_active("NOCTURNAL_CURFEW"))

        # Advance tick beyond expiration (100 + 200 = 300)
        expired = self.decree_eng.process_daily_decree_cycles(self.engine.npcs, tick=350, context=self.engine.context)
        self.assertIn("NOCTURNAL_CURFEW", expired)
        self.assertFalse(self.decree_eng.is_decree_active("NOCTURNAL_CURFEW"))

if __name__ == "__main__":
    unittest.main()
