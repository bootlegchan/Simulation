from typing import Any, Dict, List, Optional, Tuple

class SpatialGridIndex:
    """Fast 2D spatial grid hashing for O(1) room and entity proximity queries."""

    def __init__(self, cell_size: float = 10.0):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[str]] = {}
        self.entity_positions: Dict[str, Tuple[float, float]] = {}
        self.room_coordinates: Dict[str, Tuple[float, float]] = {}

    def _hash_coords(self, x: float, y: float) -> Tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))

    def register_room(self, room_id: str, x: float, y: float) -> None:
        self.room_coordinates[room_id] = (x, y)
        cell = self._hash_coords(x, y)
        if cell not in self.grid:
            self.grid[cell] = []
        if room_id not in self.grid[cell]:
            self.grid[cell].append(room_id)

    def update_entity_position(self, entity_id: str, x: float, y: float) -> None:
        if entity_id in self.entity_positions:
            old_x, old_y = self.entity_positions[entity_id]
            old_cell = self._hash_coords(old_x, old_y)
            if old_cell in self.grid and entity_id in self.grid[old_cell]:
                self.grid[old_cell].remove(entity_id)

        self.entity_positions[entity_id] = (x, y)
        new_cell = self._hash_coords(x, y)
        if new_cell not in self.grid:
            self.grid[new_cell] = []
        self.grid[new_cell].append(entity_id)

    def get_nearby_entities(self, x: float, y: float, radius: float) -> List[str]:
        min_cell_x = int((x - radius) // self.cell_size)
        max_cell_x = int((x + radius) // self.cell_size)
        min_cell_y = int((y - radius) // self.cell_size)
        max_cell_y = int((y + radius) // self.cell_size)

        nearby = []
        radius_sq = radius * radius

        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cell_entities = self.grid.get((cx, cy), [])
                for e_id in cell_entities:
                    if e_id in self.entity_positions:
                        ex, ey = self.entity_positions[e_id]
                        dist_sq = (ex - x) ** 2 + (ey - y) ** 2
                        if dist_sq <= radius_sq and e_id not in nearby:
                            nearby.append(e_id)

        return nearby

    def get_distance(self, room_a_id: str, room_b_id: str) -> float:
        if room_a_id not in self.room_coordinates or room_b_id not in self.room_coordinates:
            return 1.0
        ax, ay = self.room_coordinates[room_a_id]
        bx, by = self.room_coordinates[room_b_id]
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
