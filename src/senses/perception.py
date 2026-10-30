"""
Multi-Modal Sensory Perception System: Visual Node Perception & Auditory Propagation.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.world.model import Room

@dataclass
class Observation:
    observer_id: str
    subject_id: str
    event_type: str
    location_id: str
    tick: int
    sensory_modality: str = "VISUAL"  # "VISUAL", "AUDITORY", "ENVIRONMENTAL"
    decibel_volume: float = 50.0

class PerceptionSystem:
    """Multi-modal sensory awareness across visual and auditory channels."""

    @staticmethod
    def observe_room(room: Room, observer_id: str, current_tick: int) -> List[Observation]:
        """Visual observation of co-located occupants, interactable objects, and items."""
        observations = []
        for occupant in room.occupant_ids:
            if occupant != observer_id:
                observations.append(
                    Observation(
                        observer_id=observer_id,
                        subject_id=occupant,
                        event_type="presence_observed",
                        location_id=room.id,
                        tick=current_tick,
                        sensory_modality="VISUAL"
                    )
                )
        return observations

    @staticmethod
    def sense_auditory_events(
        observer_room: Room,
        adjacent_rooms: List[Room],
        observer_id: str,
        acoustic_events: List[Dict[str, Any]],
        current_tick: int
    ) -> List[Observation]:
        """
        Auditory perception of acoustic events (e.g., tavern brawls, screams, lockpicking, speeches)
        occurring in the current room OR adjacent connected rooms.
        Acoustic volume decays across adjacent room boundaries.
        """
        auditory_obs = []

        all_accessible_room_ids = {observer_room.id: 1.0}  # Direct room = 100% volume
        for adj_r in adjacent_rooms:
            all_accessible_room_ids[adj_r.id] = 0.5  # Adjacent room = 50% volume attenuation

        for event in acoustic_events:
            evt_room_id = event.get("location_id", "")
            if evt_room_id in all_accessible_room_ids:
                volume_multiplier = all_accessible_room_ids[evt_room_id]
                effective_volume = event.get("decibel_volume", 60.0) * volume_multiplier

                # Auditory threshold check (effective volume >= 20 dB)
                if effective_volume >= 20.0 and event.get("source_id") != observer_id:
                    auditory_obs.append(
                        Observation(
                            observer_id=observer_id,
                            subject_id=event.get("source_id", "unknown_source"),
                            event_type=f"auditory_{event.get('event_name', 'noise')}",
                            location_id=evt_room_id,
                            tick=current_tick,
                            sensory_modality="AUDITORY",
                            decibel_volume=round(effective_volume, 1)
                        )
                    )

        return auditory_obs
