"""Spatial Grid Index for proximity queries."""
from typing import Dict, List, Tuple

class SpatialGridIndex:
    def __init__(self, cell_size: float = 10.0):
        self.cell_size = cell_size
        self.room_coords: Dict[str, Tuple[float, float]] = {}

    def register_room(self, room_id: str, x: float = 0.0, y: float = 0.0) -> None:
        self.room_coords[room_id] = (x, y)

    def get_room_coords(self, room_id: str) -> Tuple[float, float]:
        return self.room_coords.get(room_id, (0.0, 0.0))
