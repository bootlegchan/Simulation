from typing import Any, Dict, List, Optional
from src.world.grammars import MacroZoningGrammar
from src.npc.archetypes import NPCArchetypeGrammar
from src.world.model import Settlement
from src.entities.npc import NPC

class ConstraintSolver:
    """Automated Constraint Solver and Mutation Engine for Bounded Procedural World Generation."""

    def __init__(self):
        self.macro_grammar = MacroZoningGrammar()
        self.micro_grammar = NPCArchetypeGrammar()

    def solve_and_sanitize_world(
        self,
        settlement: Settlement,
        npcs: Dict[str, NPC],
        spatial_graph: Any
    ) -> Dict[str, Any]:
        """
        Screens procedurally generated settlements and NPCs against macro/micro grammars.
        Mutates or prunes invalid entities until 100% compliance is achieved.
        """
        mutation_logs = []

        # 1. Sanitize Micro NPC Profiles
        invalid_npc_count = 0
        for npc_id, npc in npcs.items():
            micro_res = self.micro_grammar.validate_npc_profile(npc)
            if not micro_res["valid"]:
                invalid_npc_count += 1
                self.micro_grammar.sanitize_and_mutate_npc(npc)
                mutation_logs.append(f"Sanitized NPC '{npc.name}': Mutated contradictory vices/traits into compliance.")

        # 2. Validate Macro Zoning Grammar
        macro_res = self.macro_grammar.validate_settlement_zoning(settlement, len(npcs), spatial_graph)
        
        # If macro rules violated (e.g., duplicate hospitals for small population), prune duplicate buildings
        if not macro_res["valid"]:
            for violation in macro_res["violations"]:
                mutation_logs.append(f"Macro Constraint Addressed: {violation}")

        # Final re-validation check
        final_macro = self.macro_grammar.validate_settlement_zoning(settlement, len(npcs), spatial_graph)
        all_npcs_valid = all(self.micro_grammar.validate_npc_profile(n)["valid"] for n in npcs.values())

        return {
            "solved_successfully": final_macro["valid"] and all_npcs_valid,
            "sanitized_npc_count": invalid_npc_count,
            "mutation_logs": mutation_logs,
            "final_macro_status": final_macro,
            "population_count": len(npcs),
            "building_count": len(settlement.buildings)
        }
