"""
Visual-Agnostic Spatial Topology Framework.
Decouples spatial reasoning from specific 2D/3D visual implementations (e.g. 2D tilemaps, 3D engines, or spreadsheet tables).
Space is represented as an abstract weighted node topology where distance is travel weight/cost and accessibility is threshold-based.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

@dataclass
class SpatialNode:
    node_id: str
    name: str
    node_type: str  # "room", "building", "district", "spreadsheet_cell", "zone"
    connected_node_ids: List[str] = field(default_factory=list)
    traversal_cost_modifier: float = 1.0  # 1.0 = standard, >1.0 = difficult terrain/staircase, <1.0 = paved road
    contained_object_ids: List[str] = field(default_factory=list)
    occupant_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AbstractSpatialTopology(ABC):
    """Abstract Base Class for visual-agnostic spatial topology providers."""

    @abstractmethod
    def get_travel_weight(self, start_node_id: str, target_node_id: str) -> float:
        """Returns abstract travel weight/cost between two spatial nodes."""
        pass

    @abstractmethod
    def is_accessible(self, observer_node_id: str, target_node_id: str, threshold: float = 50.0) -> bool:
        """Evaluates whether target node is perceptually or physically accessible to observer."""
        pass

    @abstractmethod
    def find_shortest_weighted_path(self, start_node_id: str, target_node_id: str) -> Optional[List[str]]:
        """Finds path of spatial nodes connecting start and target nodes."""
        pass

class WeightedNodeTopology(AbstractSpatialTopology):
    """
    Data-driven weighted node topology implementation.
    Works seamlessly whether rendering on a 2D tile map, 3D Unreal/Unity engine, or Excel spreadsheet grid.
    Includes memoized path caching for high-performance tick loops.
    """

    def __init__(self):
        self.nodes: Dict[str, SpatialNode] = {}
        self.custom_edge_weights: Dict[Tuple[str, str], float] = {}
        self._path_cache: Dict[Tuple[str, str], Optional[List[str]]] = {}
        self._weight_cache: Dict[Tuple[str, str], float] = {}

    def invalidate_cache(self) -> None:
        """Clears path and weight caches when topology structure changes."""
        self._path_cache.clear()
        self._weight_cache.clear()

    def register_node(self, node: SpatialNode) -> None:
        self.nodes[node.node_id] = node
        self.invalidate_cache()

    def set_edge_weight(self, node_a_id: str, node_b_id: str, weight: float) -> None:
        self.custom_edge_weights[(node_a_id, node_b_id)] = max(0.1, weight)
        self.custom_edge_weights[(node_b_id, node_a_id)] = max(0.1, weight)
        self.invalidate_cache()

    def get_travel_weight(self, start_node_id: str, target_node_id: str) -> float:
        if start_node_id == target_node_id:
            return 0.0

        cache_key = (start_node_id, target_node_id)
        if cache_key in self._weight_cache:
            return self._weight_cache[cache_key]

        path = self.find_shortest_weighted_path(start_node_id, target_node_id)
        if not path:
            self._weight_cache[cache_key] = 100.0
            return 100.0  # High penalty for unreachable nodes

        total_weight = 0.0
        for i in range(len(path) - 1):
            curr, nxt = path[i], path[i+1]
            edge_w = self.custom_edge_weights.get((curr, nxt), 1.0)
            target_node = self.nodes.get(nxt)
            node_modifier = target_node.traversal_cost_modifier if target_node else 1.0
            total_weight += edge_w * node_modifier

        res = round(total_weight, 2)
        self._weight_cache[cache_key] = res
        return res

    def is_accessible(self, observer_node_id: str, target_node_id: str, threshold: float = 50.0) -> bool:
        weight = self.get_travel_weight(observer_node_id, target_node_id)
        return weight <= threshold

    def find_shortest_weighted_path(self, start_node_id: str, target_node_id: str) -> Optional[List[str]]:
        if start_node_id == target_node_id:
            return [start_node_id]
        if start_node_id not in self.nodes or target_node_id not in self.nodes:
            return None

        cache_key = (start_node_id, target_node_id)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        # Priority queue for weighted shortest path
        queue = [(0.0, start_node_id, [start_node_id])]
        visited: Set[str] = set()

        while queue:
            cost, curr, path = heapq.heappop(queue)
            if curr == target_node_id:
                self._path_cache[cache_key] = path
                return path

            if curr in visited:
                continue
            visited.add(curr)

            curr_node = self.nodes[curr]
            for neighbor_id in curr_node.connected_node_ids:
                if neighbor_id not in visited and neighbor_id in self.nodes:
                    edge_w = self.custom_edge_weights.get((curr, neighbor_id), 1.0)
                    neighbor_node = self.nodes[neighbor_id]
                    step_cost = edge_w * neighbor_node.traversal_cost_modifier
                    new_cost = cost + step_cost
                    new_path = list(path)
                    new_path.append(neighbor_id)
                    heapq.heappush(queue, (new_cost, neighbor_id, new_path))

        self._path_cache[cache_key] = None
        return None
