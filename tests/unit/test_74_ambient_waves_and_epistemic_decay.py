"""
Unit Test Suite 74: Ambient Spatial Waves, Epistemic Decay & Receiver Receptivity.
Verifies the advanced communication layer features:
1. Ambient spatial affordance waves (visual line-of-sight & acoustic doorway spillover).
2. Continuous epistemic forgetting curve (Borchert memory half-life) and salience eviction.
3. Receiver-centric cognitive load filtering (exhaustion/stress filters out idle gossip).
4. Emotional and moral biases in information absorption.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.society.information_networks import (
    UnifiedInformationEngine,
    InformationChannelType,
    WaveMedium,
)

class TestAmbientWavesAndEpistemicDecay(unittest.TestCase):
    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.engine.start()
        self.info_eng: UnifiedInformationEngine = self.engine.context.get_service("unified_information_engine")

    def test_01_ambient_visual_wave_perception(self):
        """Verify that co-located citizens passively perceive visual waves in a room."""
        citizen = self.engine.npcs["npc_citizen_01"]
        citizen.location_id = "room_village_square"
        citizen.needs["energy"] = 90.0
        citizen.feelings["stress"] = 10.0

        item = self.info_eng.publish_item(
            channel=InformationChannelType.CIVIC_NOTICES,
            topic="PLAZA_STATUE_DEDICATION",
            headline="New Stone Fountain Dedicated in Village Square",
            content="The stone fountain is now flowing with fresh spring water.",
            target_location_id="room_village_square",
            current_tick=100,
            context=self.engine.context
        )

        # Verify a visual wave exists in the room
        waves = [w for w in self.info_eng.active_waves if w.item_id == item.item_id and w.current_room_id == "room_village_square"]
        self.assertGreaterEqual(len(waves), 1)
        self.assertEqual(waves[0].medium, WaveMedium.VISUAL_LINE_OF_SIGHT)

        # Process ambient wave perception
        perceived = self.info_eng.process_ambient_wave_perception(self.engine.context, current_tick=100)
        self.assertGreaterEqual(perceived, 1)

        # Citizen should now know the item without calling read_notice_board manually
        self.assertIn(item.item_id, self.info_eng.npc_knowledge_ledger[citizen.id])

    def test_02_ambient_acoustic_wave_doorway_propagation(self):
        """Verify that acoustic sound waves spill over connected room portals with attenuation."""
        item = self.info_eng.publish_item(
            channel=InformationChannelType.GOSSIP_AND_RUMORS,
            topic="TAVERN_BRAWL_COMMOTION",
            headline="Loud Shouting and Shattered Flagons in the Taproom",
            content="An uproar broke out over an arm-wrestling wager.",
            target_location_id="room_tavern",
            current_tick=200,
            context=self.engine.context
        )

        # Active waves should include the primary wave in room_tavern
        primary_waves = [w for w in self.info_eng.active_waves if w.item_id == item.item_id and w.current_room_id == "room_tavern"]
        self.assertEqual(len(primary_waves), 1)
        self.assertEqual(primary_waves[0].medium, WaveMedium.ACOUSTIC_SOUND)

        # And spillover waves in connected rooms (e.g. room_village_square)
        spillover_waves = [w for w in self.info_eng.active_waves if w.item_id == item.item_id and w.current_room_id != "room_tavern"]
        self.assertGreaterEqual(len(spillover_waves), 1)
        # Intensity should be attenuated (0.80 * 0.50 = 0.40)
        self.assertLess(spillover_waves[0].intensity, primary_waves[0].intensity)
        self.assertEqual(spillover_waves[0].hops, 1)

    def test_03_epistemic_forgetting_salience_decay_and_eviction(self):
        """Verify continuous exponential salience decay and eviction of forgotten memories."""
        aldous = self.engine.npcs["npc_aldous"]

        # Aldous learns a trivial rumor at tick 100
        rumor = self.info_eng.publish_item(
            channel=InformationChannelType.GOSSIP_AND_RUMORS,
            topic="WEATHER_OBSERVATION",
            headline="Overcast Morning Over North Hills",
            content="A slight morning mist was observed rolling down the valley.",
            current_tick=100
        )
        self.info_eng.record_learned_item(aldous.id, rumor.item_id, current_tick=100)
        self.assertIn(rumor.item_id, self.info_eng.npc_knowledge_ledger[aldous.id])

        trace = self.info_eng.npc_memory_traces[aldous.id][rumor.item_id]
        self.assertEqual(trace.salience, 1.0)

        # Advance tick to 15,000 (elapsed ~14,900 ticks -> exp(-0.0003 * 14900) = exp(-4.47) = 0.011 < 0.10)
        evicted = self.info_eng.evict_decayed_memories(current_tick=15000)
        self.assertGreaterEqual(evicted, 1)

        # Trivial rumor has decayed below threshold and is evicted
        self.assertNotIn(rumor.item_id, self.info_eng.npc_knowledge_ledger[aldous.id])
        self.assertNotIn(rumor.item_id, self.info_eng.npc_memory_traces[aldous.id])

        # Permanent municipal welcome notice is protected from eviction
        welcome_items = [i for i in self.info_eng.active_items.values() if i.topic == "MUNICIPAL_WELCOME"]
        if welcome_items:
            w_id = welcome_items[0].item_id
            self.info_eng.record_learned_item(aldous.id, w_id, current_tick=100)
            self.info_eng.evict_decayed_memories(current_tick=15000)
            # Welcome notice should still be retained
            self.assertIn(w_id, self.info_eng.npc_knowledge_ledger[aldous.id])

    def test_04_receiver_cognitive_load_filtering(self):
        """Verify that exhausted or acute-stressed citizens filter out idle gossip."""
        citizen = self.engine.npcs["npc_citizen_02"]
        item_gossip = self.info_eng.publish_item(
            channel=InformationChannelType.GOSSIP_AND_RUMORS,
            topic="LOCAL_CHATTER",
            headline="Someone Saw a Red Fox Near the Barn",
            content="A fox was spotted near the chicken coop.",
            current_tick=100
        )
        item_crime = self.info_eng.publish_item(
            channel=InformationChannelType.CRIME_AND_JUSTICE,
            topic="BURGLARY_ALERT",
            headline="Alarm: Mill Storehouse Break-in",
            content="Grain store broken into overnight.",
            current_tick=100
        )

        # Rested citizen accepts both
        citizen.needs["energy"] = 80.0
        citizen.feelings["stress"] = 15.0
        rec_gossip, _ = self.info_eng.evaluate_receiver_receptivity(citizen, item_gossip, self.engine.context)
        rec_crime, _ = self.info_eng.evaluate_receiver_receptivity(citizen, item_crime, self.engine.context)
        self.assertTrue(rec_gossip)
        self.assertTrue(rec_crime)

        # Exhausted citizen (energy = 10) rejects idle gossip, but receives crime alert
        citizen.needs["energy"] = 10.0
        rec_gossip_tired, _ = self.info_eng.evaluate_receiver_receptivity(citizen, item_gossip, self.engine.context)
        rec_crime_tired, _ = self.info_eng.evaluate_receiver_receptivity(citizen, item_crime, self.engine.context)
        self.assertFalse(rec_gossip_tired)
        self.assertTrue(rec_crime_tired)

    def test_05_emotional_bias_affinity(self):
        """Verify that emotional state and moral profile shape information absorption affinity."""
        bitter_citizen = self.engine.npcs["npc_citizen_03"]
        bitter_citizen.needs["energy"] = 80.0
        bitter_citizen.feelings["stress"] = 20.0
        bitter_citizen.feelings["resentment"] = 65.0  # High bitterness/suspicion

        item_scandal = self.info_eng.publish_item(
            channel=InformationChannelType.GOSSIP_AND_RUMORS,
            topic="MAYOR_SCANDAL",
            headline="Whisper of Misallocated Town Hall Ledger Funds",
            content="Rumors of questionable ledger accounting.",
            current_tick=100
        )

        _, mult_bitter = self.info_eng.evaluate_receiver_receptivity(bitter_citizen, item_scandal, self.engine.context)

        calm_citizen = self.engine.npcs["npc_citizen_04"]
        calm_citizen.needs["energy"] = 80.0
        calm_citizen.feelings["stress"] = 20.0
        calm_citizen.feelings["resentment"] = 0.0

        _, mult_calm = self.info_eng.evaluate_receiver_receptivity(calm_citizen, item_scandal, self.engine.context)

        # Bitter citizen has significantly higher receptivity for scandal news
        self.assertGreater(mult_bitter, mult_calm)

if __name__ == "__main__":
    unittest.main()
