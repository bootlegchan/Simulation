"""
Consolidated Test Suite 12: Adaptive Building Repurposing & Responsive Civic Crisis Planning.
Verifies functional mutation of failing businesses into illicit dens, ruined buildings into occult sanctums,
and responsive civic emergency construction (emergency clinics, fire watchtowers, security checkpoints).
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.core.events import DomainEvent
from src.simulation.engine import SimulationEngine
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.world.urban_growth import (
    UrbanGrowthEngine,
    BuildingRepurposingEngine,
    ResponsiveCivicPlanningEngine,
    BuildingCondition,
)
from src.society.information_channels import NoticeBoardEngine


class TestAdaptiveUrbanRepurposing(unittest.TestCase):
    """Verifies adaptive functional mutations and responsive civic urban planning."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.settlement = self.engine.settlements["settlement_oakwood"]

    def test_01_mutation_rules_and_civic_policies_loaded(self):
        """Verify that mutation rules and civic crisis policies are loaded from external JSON files."""
        content = self.engine.loader.loaded_data
        self.assertIn("mutation_rules", content)
        self.assertIn("civic_crisis_policies", content)

        rules = content["mutation_rules"].get("mutation_rules", {})
        self.assertIn("FAILING_TAVERN_TO_GAMBLING_SPEAKEASY", rules)
        self.assertIn("FAILING_APOTHECARY_TO_CONTRABAND_LAB", rules)
        self.assertIn("CONDEMNED_RUIN_TO_OCCULT_SANCTUM", rules)
        self.assertIn("PROSPERITY_GENTRIFICATION", rules)

        policies = content["civic_crisis_policies"].get("civic_crisis_policies", {})
        self.assertIn("CRISIS_MEDICAL_DEFICIT", policies)
        self.assertIn("CRISIS_FIRE_HAZARD", policies)
        self.assertIn("CRISIS_CRIME_EPIDEMIC", policies)

    def test_02_failing_business_to_illicit_speakeasy(self):
        """Verify that a financially distressed tavern mutates into an illicit gambling speakeasy."""
        tavern = self.settlement.buildings.get("bldg_tavern")
        self.assertIsNotNone(tavern)
        tavern.owner_id = "npc_silas"
        silas = self.engine.npcs["npc_silas"]

        # Induce economic distress & structural wear
        silas.wealth = 5.0  # Poverty threshold <= 15.0
        tavern.structural_integrity = 45.0  # Condition <= 60.0

        repurpose_engine = BuildingRepurposingEngine(self.engine.loader.loaded_data.get("mutation_rules"))
        res = repurpose_engine.evaluate_and_repurpose_building(
            building=tavern,
            owner=silas,
            settlement=self.settlement,
            objects_dict=self.engine.objects,
            npcs=self.engine.npcs,
            current_tick=1440
        )

        self.assertIsNotNone(res)
        self.assertTrue(res["mutated"])
        self.assertEqual(res["rule_id"], "FAILING_TAVERN_TO_GAMBLING_SPEAKEASY")
        self.assertEqual(tavern.category, "UNDERWORLD")
        self.assertIn("Speakeasy", tavern.name)

        # Verify installed vice objects (gambling pit or moonshine still)
        installed_objs = [self.engine.objects[oid] for oid in res["installed_objects"]]
        has_gambling = any(obj.has_capability("gamble") or obj.has_capability("underground_betting") for obj in installed_objs)
        has_still = any(obj.has_capability("distill_spirits") or obj.has_capability("brew_moonshine") for obj in installed_objs)
        self.assertTrue(has_gambling or has_still)

        # Verify owner's crime propensity increased
        self.assertGreater(silas.vices.get("crime_propensity", 0.0), 20.0)

    def test_03_ruined_building_to_occult_sanctum(self):
        """Verify that an abandoned ruined building adapts into a clandestine occult sanctum."""
        # Create an abandoned ruined building
        abandoned_bldg = self.engine.urban_growth_engine.execute_intelligent_construction(
            settlement=self.settlement,
            blueprint_id="blueprint_underworld_hideaway",
            spatial_graph=self.engine.spatial_graph,
            objects_dict=self.engine.objects,
            owner_id=None
        )
        bldg_id = abandoned_bldg["building_id"]
        bldg = self.settlement.buildings[bldg_id]

        # Collapse to ruins
        bldg.structural_integrity = 5.0
        bldg.condition_state = BuildingCondition.CONDEMNED.value

        repurpose_engine = BuildingRepurposingEngine(self.engine.loader.loaded_data.get("mutation_rules"))
        res = repurpose_engine.evaluate_and_repurpose_building(
            building=bldg,
            owner=None,
            settlement=self.settlement,
            objects_dict=self.engine.objects,
            npcs=self.engine.npcs,
            current_tick=2880
        )

        self.assertIsNotNone(res)
        self.assertTrue(res["mutated"])
        self.assertEqual(res["rule_id"], "CONDEMNED_RUIN_TO_OCCULT_SANCTUM")
        self.assertIn("Occult Sanctum", bldg.name)

        # Verify occult altar installed
        installed_objs = [self.engine.objects[oid] for oid in res["installed_objects"]]
        has_altar = any(obj.has_capability("perform_cult_rite") for obj in installed_objs)
        self.assertTrue(has_altar)

    def test_04_medical_deficit_triggers_emergency_clinic(self):
        """Verify that destroying the town apothecary triggers responsive emergency clinic construction."""
        # Destroy existing apothecary to create medical deficit
        self.settlement.buildings.pop("bldg_apothecary", None)
        self.assertEqual(sum(1 for b in self.settlement.buildings.values() if b.category == "MEDICAL"), 0)

        self.engine.municipal_treasury.balance = 100.0
        civic_engine = ResponsiveCivicPlanningEngine(
            civic_policies_config=self.engine.loader.loaded_data.get("civic_crisis_policies"),
            urban_growth_engine=self.engine.urban_growth_engine
        )

        mitigations = civic_engine.evaluate_and_mitigate_crises(
            settlement=self.settlement,
            municipal_treasury=self.engine.municipal_treasury,
            npcs=self.engine.npcs,
            objects_dict=self.engine.objects,
            spatial_graph=self.engine.spatial_graph,
            event_history=[],
            current_tick=1440
        )

        med_mitigations = [m for m in mitigations if m["crisis_id"] == "CRISIS_MEDICAL_DEFICIT"]
        self.assertEqual(len(med_mitigations), 1)
        med_mitigation = med_mitigations[0]
        self.assertEqual(med_mitigation["crisis_id"], "CRISIS_MEDICAL_DEFICIT")
        self.assertEqual(med_mitigation["blueprint_constructed"], "blueprint_emergency_clinic")

        # Verify new clinic exists in settlement and belongs to MEDICAL category
        new_bldg = self.settlement.buildings.get(med_mitigation["building_id"])
        self.assertIsNotNone(new_bldg)
        self.assertEqual(new_bldg.category, "MEDICAL")

        # Verify sickbeds were placed inside
        sickbeds = [obj for obj in self.engine.objects.values() if obj.has_capability("triage")]
        self.assertGreaterEqual(len(sickbeds), 1)

    def test_05_fire_disaster_triggers_watchtower_brigade(self):
        """Verify that building destruction by fire triggers civic construction of watchtower & fire brigade."""
        self.engine.municipal_treasury.balance = 150.0
        fire_event = DomainEvent(
            event_type="building_destroyed",
            tick=100,
            source_id="arson_event",
            payload={"building_name": "Old Granary", "reason": "arson"}
        )

        civic_engine = ResponsiveCivicPlanningEngine(
            civic_policies_config=self.engine.loader.loaded_data.get("civic_crisis_policies"),
            urban_growth_engine=self.engine.urban_growth_engine
        )

        mitigations = civic_engine.evaluate_and_mitigate_crises(
            settlement=self.settlement,
            municipal_treasury=self.engine.municipal_treasury,
            npcs=self.engine.npcs,
            objects_dict=self.engine.objects,
            spatial_graph=self.engine.spatial_graph,
            event_history=[fire_event],
            current_tick=2880
        )

        fire_mitigations = [m for m in mitigations if m["crisis_id"] == "CRISIS_FIRE_HAZARD"]
        self.assertEqual(len(fire_mitigations), 1)
        self.assertEqual(fire_mitigations[0]["blueprint_constructed"], "blueprint_watchtower_brigade")

        # Verify watchtower alarm bell and water reservoir trough were placed
        alarm_bells = [obj for obj in self.engine.objects.values() if obj.has_capability("fire_watch")]
        water_troughs = [obj for obj in self.engine.objects.values() if obj.has_capability("firefighting_reservoir")]
        self.assertGreaterEqual(len(alarm_bells), 1)
        self.assertGreaterEqual(len(water_troughs), 1)

    def test_06_crime_epidemic_triggers_garrison_checkpoint(self):
        """Verify that high underworld density triggers municipal security checkpoint construction."""
        self.engine.municipal_treasury.balance = 150.0

        # Current settlement has 2 underworld buildings (vice den, outlaw hideout)
        underworld_count = sum(1 for b in self.settlement.buildings.values() if b.category == "UNDERWORLD")
        self.assertGreaterEqual(underworld_count, 2)

        civic_engine = ResponsiveCivicPlanningEngine(
            civic_policies_config=self.engine.loader.loaded_data.get("civic_crisis_policies"),
            urban_growth_engine=self.engine.urban_growth_engine
        )

        mitigations = civic_engine.evaluate_and_mitigate_crises(
            settlement=self.settlement,
            municipal_treasury=self.engine.municipal_treasury,
            npcs=self.engine.npcs,
            objects_dict=self.engine.objects,
            spatial_graph=self.engine.spatial_graph,
            event_history=[],
            current_tick=4320
        )

        crime_mitigations = [m for m in mitigations if m["crisis_id"] == "CRISIS_CRIME_EPIDEMIC"]
        self.assertEqual(len(crime_mitigations), 1)
        self.assertEqual(crime_mitigations[0]["blueprint_constructed"], "blueprint_garrison_checkpoint")

        # Verify street lanterns were placed in the district
        lanterns = [obj for obj in self.engine.objects.values() if obj.has_capability("illuminate_street")]
        self.assertGreaterEqual(len(lanterns), 1)

    def test_07_prosperity_gentrification(self):
        """Verify that a wealthy homeowner gentrifies their property into a gilded salon."""
        manor = self.settlement.buildings.get("bldg_vance_manor")
        self.assertIsNotNone(manor)
        marcus = self.engine.npcs["npc_marcus_vance"]
        marcus.wealth = 300.0  # Wealth > 180.0
        manor.structural_integrity = 95.0

        repurpose_engine = BuildingRepurposingEngine(self.engine.loader.loaded_data.get("mutation_rules"))
        res = repurpose_engine.evaluate_and_repurpose_building(
            building=manor,
            owner=marcus,
            settlement=self.settlement,
            objects_dict=self.engine.objects,
            npcs=self.engine.npcs,
            current_tick=5760
        )

        self.assertIsNotNone(res)
        self.assertTrue(res["mutated"])
        self.assertEqual(res["rule_id"], "PROSPERITY_GENTRIFICATION")
        self.assertIn("Gentrified", manor.name)


if __name__ == "__main__":
    unittest.main()
