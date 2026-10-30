from typing import Any, Dict, List, Optional
from src.entities.base import BaseEntity
from src.entities.item import ItemInstance

class NPC(BaseEntity):
    """Autonomous Non-Player Character entity with expanded social, physical, vice, cognitive, emotional, moral, and biographical profiles."""

    def __init__(
        self,
        npc_id: str,
        name: str,
        location_id: Optional[str] = None,
        occupation: str = "Unemployed",
        home_location_id: Optional[str] = None,
        work_location_id: Optional[str] = None,
        needs: Optional[Dict[str, float]] = None,
        decay_rates: Optional[Dict[str, float]] = None,
        attributes: Optional[Dict[str, float]] = None,
        personality: Optional[Dict[str, float]] = None,
        inventory: Optional[List[ItemInstance]] = None,
        wealth: float = 50.0,
        faction_id: Optional[str] = None,
        civic_role: Optional[str] = None,
        social_profile: Optional[Dict[str, Any]] = None,
        appearance: Optional[Dict[str, str]] = None,
        education: str = "Basic Literacy",
        cognition: Optional[Dict[str, Any]] = None,
        vices: Optional[Dict[str, float]] = None,
        access_permissions: Optional[List[str]] = None,
        mental_map: Optional[Dict[str, Dict[str, Any]]] = None,
        acquaintances: Optional[Dict[str, Dict[str, Any]]] = None,
        feelings: Optional[Dict[str, float]] = None,
        moral_erosion: float = 10.0,
        biographical_log: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(npc_id, name, "npc", location_id)
        self.occupation = occupation
        self.home_location_id = home_location_id
        self.work_location_id = work_location_id

        self.needs = needs if needs is not None else {"hunger": 20.0, "energy": 90.0, "social": 50.0}
        self.decay_rates = decay_rates if decay_rates is not None else {"hunger": 0.5, "energy": -0.3, "social": -0.2}
        self.attributes = attributes if attributes is not None else {"strength": 10.0, "intelligence": 10.0, "stamina": 10.0}
        self.personality = personality if personality is not None else {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5
        }

        self.inventory: List[ItemInstance] = inventory if inventory is not None else []
        self.wealth = max(0.0, wealth)
        self.current_state = "IDLE"
        self.faction_id = faction_id
        self.civic_role = civic_role

        self.social_profile = social_profile if social_profile is not None else {
            "moral_values": {"loyalty": 0.7, "honor": 0.8, "ambition": 0.5},
            "reputation_facets": {"trustworthiness": 75.0, "temperament": 50.0, "discretion": 70.0},
            "communication_style": "Direct & Honest",
            "sentimental_attachments": ["Family Estate"],
            "vulnerabilities": ["Pride"],
            "background": "Local citizen of Oakwood with deep community roots."
        }

        self.appearance = appearance if appearance is not None else {
            "outfit": "Plain Homespun Tunic",
            "grooming": "Neat",
            "build": "Average",
            "style": "Traditional"
        }
        self.education = education
        self.cognition = cognition if cognition is not None else {
            "decision_quality": "Rational",  # Rational, Impulsive, Short-sighted, Deluded
            "laziness": 0.2
        }
        self.vices = vices if vices is not None else {
            "alcohol_dependence": 0.0,
            "gambling_drive": 0.0,
            "crime_propensity": 0.0,
            "vice_indulgence": 0.0
        }
        self.access_permissions = access_permissions if access_permissions is not None else []
        self.mental_map = mental_map if mental_map is not None else {}
        self.acquaintances = acquaintances if acquaintances is not None else {}

        # Granular emotional feelings profile
        self.feelings: Dict[str, float] = feelings if feelings is not None else {
            "contentment": 50.0,
            "tenderness": 20.0,
            "passion": 15.0,
            "loneliness": 10.0,
            "stress": 10.0,
            "jealousy": 0.0,
            "guilt": 0.0,
            "grief": 0.0,
            "pride": 30.0,
            "resentment": 0.0,
        }

        # Moral erosion & alignment tracking
        self.moral_erosion: float = max(0.0, min(100.0, moral_erosion))

        # Chronological diary & biographical lifetime memory log
        self.biographical_log: List[Dict[str, Any]] = list(biographical_log) if biographical_log is not None else []

    def get_feeling(self, name: str) -> float:
        return self.feelings.get(name, 0.0)

    def set_feeling(self, name: str, value: float) -> None:
        self.feelings[name] = max(0.0, min(100.0, value))

    def adjust_feeling(self, name: str, delta: float) -> float:
        curr = self.get_feeling(name)
        new_val = max(0.0, min(100.0, curr + delta))
        self.feelings[name] = new_val
        return new_val

    def adjust_moral_erosion(self, delta: float) -> float:
        self.moral_erosion = max(0.0, min(100.0, self.moral_erosion + delta))
        return self.moral_erosion

    def get_dominant_mood(self) -> str:
        """Evaluates live feelings and needs to determine dominant emotional mood."""
        if self.get_feeling("grief") > 40.0:
            return "GRIEVING"
        if self.get_feeling("jealousy") > 50.0:
            return "JEALOUS"
        if self.get_feeling("guilt") > 50.0:
            return "GUILT_RIDDEN"
        if self.get_feeling("passion") > 60.0:
            return "PASSIONATE"
        if self.get_feeling("tenderness") > 50.0:
            return "LOVING"
        if self.get_feeling("loneliness") > 60.0:
            return "LONELY"
        if self.get_feeling("stress") > 60.0:
            return "STRESSED"
        if self.get_feeling("resentment") > 40.0:
            return "BITTER"
        if self.needs.get("energy", 100.0) < 20.0:
            return "EXHAUSTED"
        if self.get_feeling("pride") > 60.0:
            return "PROUD"
        if self.get_feeling("contentment") >= 50.0:
            return "CONTENT"
        return "NEUTRAL"

    def decay_feelings(self) -> None:
        """Naturally decays intense temporary emotional feelings toward baseline equilibrium."""
        # Negative acute feelings decay towards 0
        for negative in ("grief", "jealousy", "guilt", "resentment"):
            curr = self.feelings.get(negative, 0.0)
            if curr > 0.0:
                self.feelings[negative] = max(0.0, curr - 0.2)

        # Stress & loneliness decay toward baseline 10.0
        for acute in ("stress", "loneliness"):
            curr = self.feelings.get(acute, 10.0)
            if curr > 10.0:
                self.feelings[acute] = max(10.0, curr - 0.15)

        # Passion and tenderness decay toward baseline 15.0/20.0 without intimate maintenance
        passion_curr = self.feelings.get("passion", 15.0)
        if passion_curr > 15.0:
            self.feelings["passion"] = max(15.0, passion_curr - 0.1)

        tender_curr = self.feelings.get("tenderness", 20.0)
        if tender_curr > 20.0:
            self.feelings["tenderness"] = max(20.0, tender_curr - 0.1)

    def record_biographical_entry(
        self,
        tick: int,
        time_iso: str,
        category: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Appends a personal diary / biographical entry recording life events and inner reflections."""
        entry = {
            "tick": tick,
            "time_iso": time_iso,
            "category": category,
            "description": description,
            "dominant_mood": self.get_dominant_mood(),
            "needs": {k: round(v, 1) for k, v in self.needs.items()},
            "feelings": {k: round(v, 1) for k, v in self.feelings.items()},
            "wealth": round(self.wealth, 1),
            "location_id": self.location_id,
            "metadata": metadata or {},
        }
        self.biographical_log.append(entry)
        return entry

    def apply_need_decay(self) -> None:
        for need, decay in self.decay_rates.items():
            current = self.needs.get(need, 50.0)
            self.needs[need] = max(0.0, min(100.0, current + decay))

    def update_mental_map(self, room_id: str, room_name: str, objects: List[str], current_tick: int) -> None:
        self.mental_map[room_id] = {
            "name": room_name,
            "objects": list(objects),
            "last_visited_tick": current_tick
        }

    def record_acquaintance(self, target_id: str, target_name: str, first_impression: float, notes: str, tick: int) -> None:
        if target_id not in self.acquaintances:
            self.acquaintances[target_id] = {
                "name": target_name,
                "first_met_tick": tick,
                "first_impression": round(first_impression, 1),
                "notes": notes,
                "interaction_count": 1
            }
        else:
            self.acquaintances[target_id]["interaction_count"] += 1

    def to_dict(self) -> Dict[str, Any]:
        res = super().to_dict()
        res.update({
            "occupation": self.occupation,
            "home_location_id": self.home_location_id,
            "work_location_id": self.work_location_id,
            "needs": self.needs,
            "decay_rates": self.decay_rates,
            "attributes": self.attributes,
            "personality": self.personality,
            "inventory": [item.to_dict() for item in self.inventory],
            "wealth": self.wealth,
            "faction_id": self.faction_id,
            "civic_role": self.civic_role,
            "current_state": self.current_state,
            "social_profile": self.social_profile,
            "appearance": self.appearance,
            "education": self.education,
            "cognition": self.cognition,
            "vices": self.vices,
            "access_permissions": self.access_permissions,
            "mental_map": self.mental_map,
            "acquaintances": self.acquaintances,
            "feelings": dict(self.feelings),
            "moral_erosion": self.moral_erosion,
            "biographical_log": list(self.biographical_log),
        })
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        inv = [ItemInstance.from_dict(i) for i in data.get("inventory", [])]
        return cls(
            npc_id=data["id"],
            name=data["name"],
            location_id=data.get("location_id"),
            occupation=data.get("occupation", "Unemployed"),
            home_location_id=data.get("home_location_id"),
            work_location_id=data.get("work_location_id"),
            needs=data.get("needs"),
            decay_rates=data.get("decay_rates"),
            attributes=data.get("attributes"),
            personality=data.get("personality"),
            inventory=inv,
            wealth=data.get("wealth", 50.0),
            faction_id=data.get("faction_id"),
            civic_role=data.get("civic_role"),
            social_profile=data.get("social_profile"),
            appearance=data.get("appearance"),
            education=data.get("education", "Basic Literacy"),
            cognition=data.get("cognition"),
            vices=data.get("vices"),
            access_permissions=data.get("access_permissions"),
            mental_map=data.get("mental_map"),
            acquaintances=data.get("acquaintances"),
            feelings=data.get("feelings"),
            moral_erosion=data.get("moral_erosion", 10.0),
            biographical_log=data.get("biographical_log", []),
        )
