"""
Leisure Contests, Tavern Wagers, and Sports Recreation.
Operates 100% on declarative game rules from data/settings/recreation_games.json.
Models bilateral game acceptance, attribute-scaled win probabilities (sigmoid logit),
closed-loop cash wagers, and ambient spectator entertainment.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

@dataclass
class RecreationGameSpec:
    game_id: str
    name: str
    category: str
    preferred_rooms: List[str]
    primary_attribute: str
    secondary_attribute: str
    base_wager_gold: float = 0.25
    min_wealth_to_play_gold: float = 1.0
    skill_influence_weight: float = 0.60
    luck_weight: float = 0.40
    winner_contentment_gain: float = 12.0
    winner_pride_gain: float = 10.0
    loser_stress_gain: float = 4.0
    spectator_contentment_boost: float = 4.0
    spectator_stress_relief: float = -3.0

    @property
    def id(self) -> str:
        return self.game_id


class RecreationGameEngine:
    """
    Central Recreation, Tavern Gaming, and Contest Engine.
    Executes leisure contests, calculates attribute-derived win probabilities,
    transfers wagers directly between participants, and spreads entertainment to onlookers.
    """
    _instance: Optional["RecreationGameEngine"] = None

    @classmethod
    def get_instance(cls) -> "RecreationGameEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.games: Dict[str, RecreationGameSpec] = {}
        self.contest_history: List[Dict[str, Any]] = []
        self.total_contests_played: int = 0
        self.total_wagers_circulated_gold: float = 0.0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        cfg = SettingsRegistry.get_instance().get("recreation_games")
        g_defs = cfg.get("games", {})
        self.games.clear()

        for g_id, data in g_defs.items():
            self.games[g_id] = RecreationGameSpec(
                game_id=g_id,
                name=data.get("name", "Recreation Game"),
                category=data.get("category", "GENERAL"),
                preferred_rooms=list(data.get("preferred_rooms", ["tavern"])),
                primary_attribute=data.get("primary_attribute", "shrewdness"),
                secondary_attribute=data.get("secondary_attribute", "composure"),
                base_wager_gold=float(data.get("base_wager_gold", 0.25)),
                min_wealth_to_play_gold=float(data.get("min_wealth_to_play_gold", 1.0)),
                skill_influence_weight=float(data.get("skill_influence_weight", 0.60)),
                luck_weight=float(data.get("luck_weight", 0.40)),
                winner_contentment_gain=float(data.get("winner_contentment_gain", 12.0)),
                winner_pride_gain=float(data.get("winner_pride_gain", 10.0)),
                loser_stress_gain=float(data.get("loser_stress_gain", 4.0)),
                spectator_contentment_boost=float(data.get("spectator_contentment_boost", 4.0)),
                spectator_stress_relief=float(data.get("spectator_stress_relief", -3.0))
            )

    def evaluate_game_invitation(
        self,
        actor: Any,
        target: Any,
        game_id: str,
        context: Any
    ) -> Tuple[bool, str]:
        """
        Evaluates whether target accepts actor's invitation to play game_id.
        Continuous trade-off: wealth affordability, physical stamina, extraversion, and opinion.
        """
        game = self.games.get(game_id)
        if not game:
            return False, f"Game '{game_id}' not found."

        if actor.location_id != target.location_id:
            return False, f"{target.name} is not co-located in {actor.location_id}."

        t_wealth = float(getattr(target, "wealth", 0.0))
        if t_wealth < game.min_wealth_to_play_gold or t_wealth < game.base_wager_gold:
            return False, f"{target.name} lacks coin for the wager."

        t_energy = float(getattr(target, "needs", {}).get("energy", 100.0))
        if t_energy < 15.0:
            return False, f"{target.name} is too fatigued to contest."

        # Willingness check based on personality and social opinion
        p = getattr(target, "personality", {}) or {}
        ext = float(p.get("extraversion", 0.5))
        agree = float(p.get("agreeableness", 0.5))
        
        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        trust_mod = 0.0
        if op_eng and hasattr(op_eng, "get_net_opinion"):
            trust_mod = op_eng.get_net_opinion(target.id, actor.id) / 200.0

        # Organic shunning: if actor has terrible reputation/trustworthiness, decline
        actor_rep = float(getattr(actor, "social_profile", {}).get("reputation_facets", {}).get("trustworthiness", 75.0))
        if actor_rep < 25.0:
            return False, f"{target.name} shuns {actor.name} due to dishonest reputation."

        acceptance_chance = max(0.15, min(0.95, 0.40 + (ext * 0.30) + (agree * 0.15) + trust_mod))
        roll = context.random.random() if hasattr(context, "random") and hasattr(context.random, "random") else 0.5

        if roll <= acceptance_chance:
            return True, "Invitation accepted."
        return False, f"{target.name} declined to play."

    def execute_contest(
        self,
        actor: Any,
        opponent: Any,
        game_id: str,
        context: Any,
        tick: int = 0,
        custom_wager: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes the recreation contest between actor and opponent:
        1. Calculates win probability using continuous sigmoid on attribute delta.
        2. Transfers wager from loser to winner (strict closed-loop).
        3. Awards contentment and pride to winner; mild stress to loser.
        4. Entertains co-located room spectators.
        """
        game = self.games.get(game_id)
        if not game:
            return {"success": False, "reason": f"Game '{game_id}' not found"}

        wager = float(custom_wager if custom_wager is not None else game.base_wager_gold)
        wager = min(wager, float(getattr(actor, "wealth", 0.0)), float(getattr(opponent, "wealth", 0.0)))
        if wager <= 0.0:
            wager = 0.10

        # Extract evaluated attributes
        def get_attr(npc: Any, attr_name: str) -> float:
            # Check physical attributes, mental attributes, skills, or attributes
            for source in ("physical_attributes", "mental_attributes", "skills", "attributes"):
                d = getattr(npc, source, {}) or {}
                if attr_name in d:
                    return float(d[attr_name])
            return 50.0

        actor_score = (get_attr(actor, game.primary_attribute) * 0.70) + (get_attr(actor, game.secondary_attribute) * 0.30)
        opp_score = (get_attr(opponent, game.primary_attribute) * 0.70) + (get_attr(opponent, game.secondary_attribute) * 0.30)

        delta = actor_score - opp_score
        # Continuous sigmoid win probability: 1 / (1 + exp(-delta / 15))
        p_actor_win = 1.0 / (1.0 + math.exp(-delta / 15.0))

        roll = context.random.random() if hasattr(context, "random") and hasattr(context.random, "random") else 0.5
        actor_won = (roll < p_actor_win)

        winner = actor if actor_won else opponent
        loser = opponent if actor_won else actor

        # Closed-loop wager payout
        loser.wealth = max(0.0, round(loser.wealth - wager, 2))
        winner.wealth = round(winner.wealth + wager, 2)
        self.total_wagers_circulated_gold += wager
        self.total_contests_played += 1

        # Participant feeling adjustments
        winner.adjust_feeling("contentment", game.winner_contentment_gain)
        winner.adjust_feeling("pride", game.winner_pride_gain)
        winner.adjust_feeling("stress", -5.0)

        loser.adjust_feeling("stress", game.loser_stress_gain)
        loser.adjust_feeling("contentment", -2.0)

        # Ambient spectator entertainment
        room_id = actor.location_id
        spectators_count = 0
        if context and hasattr(context, "npcs"):
            for n in context.npcs.values():
                if n.id not in (actor.id, opponent.id) and n.location_id == room_id and getattr(n, "is_alive", True):
                    n.adjust_feeling("contentment", game.spectator_contentment_boost)
                    n.adjust_feeling("stress", game.spectator_stress_relief)
                    spectators_count += 1

        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {tick}"
        winner.record_biographical_entry(
            tick, time_iso, "RECREATION_CONTEST_WON",
            f"Won {game.name} against {loser.name} at {room_id}, pocketing {wager:.2f}g wager with {spectators_count} onlookers."
        )
        loser.record_biographical_entry(
            tick, time_iso, "RECREATION_CONTEST_LOST",
            f"Contested {game.name} against {winner.name} at {room_id}, conceding {wager:.2f}g wager."
        )

        record = {
            "game_id": game.game_id,
            "game_name": game.name,
            "winner_id": winner.id,
            "winner_name": winner.name,
            "loser_id": loser.id,
            "loser_name": loser.name,
            "wager_gold": wager,
            "location_id": room_id,
            "spectators_count": spectators_count,
            "tick": tick
        }
        self.contest_history.append(record)
        return {
            "success": True,
            "winner": winner.name,
            "loser": loser.name,
            "wager_gold": wager,
            "game_name": game.name,
            "actor_won": actor_won
        }
