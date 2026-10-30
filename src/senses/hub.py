"""
Modular Multi-Modal Sensory Hub.
Aggregates direct visual perception, acoustic auditory sensing, conversational rumor propagation,
and interest-driven Q&A inquiry into a unified sensory pipeline.
"""
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.senses.perception import PerceptionSystem, Observation
from src.senses.communication import CommunicationChannel
from src.senses.inquiry import ConversationalInquiryEngine, InquiryQueryResult
from src.npc.memory import MemorySystem
from src.world.model import Room

class SensoryHub:
    """Unified sensory perception pipeline for autonomous NPCs."""

    def __init__(self):
        self.perception_system = PerceptionSystem()
        self.communication_channel = CommunicationChannel()
        self.inquiry_engine = ConversationalInquiryEngine()

    def process_room_direct_perception(
        self,
        room: Room,
        observer: NPC,
        current_tick: int,
        memory_system: MemorySystem,
        adjacent_rooms: Optional[List[Room]] = None,
        acoustic_events: Optional[List[Dict[str, Any]]] = None
    ) -> List[Observation]:
        """
        Processes multi-modal sensory perception:
        1. Visual observation of co-located occupants, interactables, and items.
        2. Auditory sensing of loud acoustic events in current or adjacent nodes.
        3. Records raw input into Sensory Buffer, Episodic Memory, and Semantic Belief Graph.
        """
        # 1. Visual Observations
        visual_obs = self.perception_system.observe_room(room, observer.id, current_tick)
        
        # 2. Auditory Sensing
        auditory_obs = []
        if adjacent_rooms and acoustic_events:
            auditory_obs = self.perception_system.sense_auditory_events(
                observer_room=room,
                adjacent_rooms=adjacent_rooms,
                observer_id=observer.id,
                acoustic_events=acoustic_events,
                current_tick=current_tick
            )

        all_observations = visual_obs + auditory_obs

        # 3. Update Observer's Mental Map and Semantic Beliefs
        if not hasattr(observer, "mental_map") or observer.mental_map is None:
            observer.mental_map = {}
            
        observer.mental_map[room.id] = {
            "last_visited_tick": current_tick,
            "occupant_ids": list(room.occupant_ids),
            "contained_object_ids": list(room.contained_object_ids),
        }

        memory_system.update_semantic_belief(
            fact_key=f"location_mental_map:{room.id}",
            knowledge_payload={
                "occupants": list(room.occupant_ids),
                "objects": list(room.contained_object_ids),
            },
            confidence_score=1.0,
            source_attribution="direct_observation",
            current_tick=current_tick
        )

        # 4. Record into Sensory Buffer & Episodic Memory
        for obs in all_observations:
            memory_system.record_sensory_input(
                event_type=obs.event_type,
                subject_id=obs.subject_id,
                tick=current_tick,
                payload={"location_id": obs.location_id, "modality": obs.sensory_modality, "volume": obs.decibel_volume}
            )

            memory_system.record(
                memory_id=f"mem_obs_{current_tick}_{observer.id}_{obs.subject_id}",
                event_type=obs.event_type,
                subject_id=obs.subject_id,
                tick=current_tick,
                payload={"location_id": obs.location_id, "modality": obs.sensory_modality},
                salience=2.5 if obs.sensory_modality == "AUDITORY" else 1.0
            )

        return all_observations

    def process_conversational_exchange(
        self,
        speaker: NPC,
        listener: NPC,
        speaker_memory: MemorySystem,
        listener_memory: MemorySystem,
        current_tick: int,
        topic_of_interest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a two-way conversational exchange:
        1. Speaker shares rumor/gossip.
        2. Listener asks targeted inquiry question based on personal curiosity.
        3. Updates both Episodic Memory and Semantic Belief Graph.
        """
        # Step 1: Rumor Propagation
        shared_rumor = {
            "claim": f"{speaker.name} met at {speaker.location_id}",
            "speaker_id": speaker.id,
            "tick": current_tick
        }
        propagated = self.communication_channel.propagate_rumor(speaker.id, listener.id, shared_rumor)

        # Step 2: Conversational Inquiry
        inquiry_result = self.inquiry_engine.evaluate_and_execute_inquiry(
            inquirer=listener,
            respondent=speaker,
            inquirer_memory=listener_memory,
            respondent_memory=speaker_memory,
            current_tick=current_tick,
            topic_key=topic_of_interest
        )

        return {
            "speaker_id": speaker.id,
            "listener_id": listener.id,
            "propagated_rumor": propagated,
            "inquiry_result": inquiry_result,
            "tick": current_tick
        }
