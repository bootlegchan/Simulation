"""Spatial transit latency and walking simulation."""
from typing import Any

class SpatialTransitEngine:
    def __init__(self, spatial_graph: Any = None):
        self.spatial_graph = spatial_graph

    def plan_and_start_transit(self, npc: Any, dest_room: str, tick: int, context: Any, reason: str = "") -> None:
        npc.location_id = dest_room
