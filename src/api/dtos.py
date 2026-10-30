from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SpatialNodeDTO(BaseModel):
    node_id: str
    name: str
    node_type: str
    x_2d: float = 0.0
    y_2d: float = 0.0
    x_3d: float = 0.0
    y_3d: float = 0.0
    z_3d: float = 0.0
    connected_node_ids: List[str] = Field(default_factory=list)
    contained_object_ids: List[str] = Field(default_factory=list)
    occupant_ids: List[str] = Field(default_factory=list)
    traversal_cost_modifier: float = 1.0

class SpatialGraphDTO(BaseModel):
    settlement_id: str
    settlement_name: str
    nodes: Dict[str, SpatialNodeDTO] = Field(default_factory=dict)
    building_count: int = 0
    room_count: int = 0

class NPCVisualDTO(BaseModel):
    id: str
    name: str
    location_id: str
    current_action: str = "IDLE"
    fsm_state: str = "READY"
    x_3d: float = 0.0
    y_3d: float = 0.0
    z_3d: float = 0.0
    heading_degrees: float = 0.0
    needs_hunger: float = 0.0
    needs_energy: float = 100.0
    needs_social: float = 50.0
    wealth: float = 0.0
    social_class: str = "COMMONER"
    mood_icon: str = "NEUTRAL"
    dominant_feeling: str = "CONTENT"
    feelings: Dict[str, float] = Field(default_factory=dict)
    speech_bubble: Optional[str] = None
    is_arrested: bool = False
    is_injured: bool = False
    is_intoxicated: bool = False

class InteractiveObjectDTO(BaseModel):
    id: str
    name: str
    location_id: str
    x_3d: float = 0.0
    y_3d: float = 0.0
    z_3d: float = 0.0
    is_locked: bool = False
    capabilities: List[str] = Field(default_factory=list)
    contained_item_ids: List[str] = Field(default_factory=list)

class WorldStateDTO(BaseModel):
    virtual_time_iso: str
    current_tick: int
    weather: str
    season: str
    time_of_day: str
    world_tension: float
    gini_coefficient: float
    total_wealth_gold: float
    active_npc_count: int
    active_object_count: int
    is_running: bool

class EventDTO(BaseModel):
    event_id: str
    event_type: str
    tick: int
    source_id: str
    payload: Dict[str, Any]
    timestamp_iso: str

class SimulationTickBatchDTO(BaseModel):
    tick: int
    virtual_time_iso: str
    world_state: WorldStateDTO
    npcs: Dict[str, NPCVisualDTO]
    objects: Dict[str, InteractiveObjectDTO]
    events: List[EventDTO] = Field(default_factory=list)

class StateDeltaDTO(BaseModel):
    """Sub-tick entity differential delta for external visual and display streaming."""
    tick: int
    modified_npcs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    modified_objects: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    events: List[EventDTO] = Field(default_factory=list)

# --- NEW EXTENSION DTOS FOR MANIPULATION & INTERACTION API INTERFACE ---

class NPCAttributeMutationDTO(BaseModel):
    """Payload for live NPC attribute manipulation by external display/control modules."""
    location_id: Optional[str] = None
    wealth: Optional[float] = None
    needs: Optional[Dict[str, float]] = None  # e.g. {"hunger": 0.0, "energy": 100.0}
    current_state: Optional[str] = None
    vices: Optional[Dict[str, float]] = None
    feelings: Optional[Dict[str, float]] = None
    social_profile_updates: Optional[Dict[str, Any]] = None

class NPCForceActionDTO(BaseModel):
    """Payload for forcing an NPC to perform an action or goal."""
    action_type: str  # "EAT", "WORK", "SLEEP", "SOCIALIZE", "GOTO_LOCATION", "BRAWL", "INTIMACY", "COMFORT"
    target_location_id: Optional[str] = None
    target_object_id: Optional[str] = None
    target_npc_id: Optional[str] = None
    override_priority: float = 100.0

class ObjectMutationDTO(BaseModel):
    """Payload for live object manipulation."""
    location_id: Optional[str] = None
    is_locked: Optional[bool] = None
    add_capabilities: Optional[List[str]] = None
    remove_capabilities: Optional[List[str]] = None

class EnvironmentMutationDTO(BaseModel):
    """Payload for live environmental & time manipulation."""
    weather: Optional[str] = None  # "CLEAR", "RAIN", "HEAVY_STORM", "COLD_SNAP"
    season: Optional[str] = None   # "SPRING", "SUMMER", "AUTUMN", "WINTER"
    time_of_day: Optional[str] = None  # "DAWN", "DAY", "DUSK", "NIGHT"
    world_tension: Optional[float] = None

class EventInjectionDTO(BaseModel):
    """Payload for injecting arbitrary custom events into the live EventBus."""
    event_type: str
    source_id: str = "external_client"
    payload: Dict[str, Any] = Field(default_factory=dict)

class BridgeRPCCommandDTO(BaseModel):
    """Bidirectional WebSocket command payload from external frontend."""
    command_id: str
    command_type: str  # "MUTATE_NPC", "FORCE_ACTION", "MUTATE_OBJECT", "MUTATE_ENV", "INJECT_EVENT"
    target_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

class BridgeRPCResponseDTO(BaseModel):
    """Execution response returned to external frontend."""
    command_id: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
