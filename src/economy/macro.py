"""Macroeconomic indicators tracking wallets, treasury, and domestic household vaults."""
from typing import Any, Dict, List
from src.entities.npc import NPC

class MacroEconomicTracker:
    @staticmethod
    def calculate_total_currency(npcs: Dict[str, NPC], municipal_treasury_vault: float = 0.0, household_vaults_total: float = 0.0, context: Any = None) -> float:
        total_npc = sum(npc.wealth for npc in npcs.values())
        hh_total = household_vaults_total
        if hh_total == 0.0 and context is not None:
            hh_eng = context.get_service("household_economy_engine") if hasattr(context, "get_service") else None
            if hh_eng and hasattr(hh_eng, "households"):
                hh_total = sum(getattr(h, "shared_treasury_gold", 0.0) for h in hh_eng.households.values())
        return round(total_npc + max(0.0, municipal_treasury_vault) + max(0.0, hh_total), 2)

    @staticmethod
    def calculate_gini_coefficient(npcs: Dict[str, NPC]) -> float:
        wealths = sorted([npc.wealth for npc in npcs.values()])
        n = len(wealths)
        if n == 0 or sum(wealths) == 0:
            return 0.0
        num = sum((i + 1) * w for i, w in enumerate(wealths))
        den = n * sum(wealths)
        return (2 * num) / den - (n + 1) / n
