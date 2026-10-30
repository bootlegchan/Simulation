"""
Extortion & Blackmail Engine: Crusader Kings III inspired leverage and secret hooks.
Converts discovered secrets into blackmail hooks for monetary extortion or coerced council voting.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.society.governance import BillProposal

@dataclass
class BlackmailHook:
    hook_id: str
    extorter_id: str
    target_id: str
    secret_topic: str
    leverage_value: float  # 1.0 (minor) to 100.0 (scandalous)
    is_used: bool = False

class ExtortionEngine:
    """Manages blackmail hooks, monetary extortion, and coerced governance voting."""

    def __init__(self):
        self.active_hooks: Dict[str, BlackmailHook] = {}

    def create_hook(
        self,
        extorter_id: str,
        target_id: str,
        secret_topic: str,
        leverage_value: float = 50.0
    ) -> BlackmailHook:
        hook_id = f"hook_{extorter_id}_{target_id}_{secret_topic}"
        hook = BlackmailHook(
            hook_id=hook_id,
            extorter_id=extorter_id,
            target_id=target_id,
            secret_topic=secret_topic,
            leverage_value=leverage_value
        )
        self.active_hooks[hook_id] = hook
        return hook

    def demand_monetary_extortion(
        self,
        hook_id: str,
        extorter: NPC,
        target: NPC,
        demand_amount: float = 25.0
    ) -> Dict[str, Any]:
        """Extorts gold from target under threat of exposing their secret."""
        if hook_id not in self.active_hooks:
            return {"success": False, "reason": "No active blackmail hook found."}

        hook = self.active_hooks[hook_id]
        if target.wealth >= demand_amount:
            target.wealth -= demand_amount
            extorter.wealth += demand_amount
            hook.is_used = True
            return {
                "success": True,
                "gold_extorted": demand_amount,
                "extorter_id": extorter.id,
                "target_id": target.id,
                "secret_topic": hook.secret_topic
            }

        return {
            "success": False,
            "reason": "Target lacks liquid funds for extortion payment.",
            "target_wealth": target.wealth
        }

    def coerce_council_vote(
        self,
        hook_id: str,
        proposal: BillProposal,
        target_id: str,
        vote_for: bool
    ) -> Dict[str, Any]:
        """Forces target to vote according to extorter's direction on a council bill."""
        if hook_id not in self.active_hooks:
            return {"success": False, "reason": "No active hook found."}

        hook = self.active_hooks[hook_id]
        if vote_for:
            if target_id not in proposal.votes_for:
                proposal.votes_for.append(target_id)
            if target_id in proposal.votes_against:
                proposal.votes_against.remove(target_id)
        else:
            if target_id not in proposal.votes_against:
                proposal.votes_against.append(target_id)
            if target_id in proposal.votes_for:
                proposal.votes_for.remove(target_id)

        hook.is_used = True
        return {
            "success": True,
            "coerced_vote": "FOR" if vote_for else "AGAINST",
            "target_id": target_id,
            "bill_id": proposal.bill_id
        }
