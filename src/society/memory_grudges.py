"""Memory Grudges and Enduring Vendettas.
Refactored to integrate with Epistemic Memory Atoms and Associative Cue Priming.
"""
from typing import Optional, Any, Dict, List

class MemoryGrudgeEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.grudges: List[Dict[str, Any]] = []
        self.total_grudges_registered: int = 0
        self.total_grudges_reconciled: int = 0

    def clear(self) -> None:
        self.grudges.clear()
        self.total_grudges_registered = 0
        self.total_grudges_reconciled = 0

    def has_grudge_against(self, bearer_id: str, perpetrator_id: str, context: Optional[Any] = None) -> bool:
        """Checks whether bearer harbors an enduring grudge against perpetrator."""
        has_base = any(g["bearer_id"] == bearer_id and g["perpetrator_id"] == perpetrator_id for g in self.grudges)
        if has_base:
            return True

        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng:
                traces = ep_eng.npc_memories.get(bearer_id, {})
                for trace in traces.values():
                    atom = trace.atom
                    if "grudge" in atom.tags and atom.actor_id == perpetrator_id:
                        if not trace.is_dormant(threshold=0.05):
                            return True
        return False

    def register_grudge(self, bearer: Any, perpetrator: Any, category: str, context: Any = None, current_tick: int = 0) -> Dict[str, Any]:
        """Registers an enduring grudge both in memory grudges list and as a high-relevance Epistemic Memory Atom."""
        record = {"bearer_id": bearer.id, "perpetrator_id": perpetrator.id, "category": category, "tick": current_tick}
        self.grudges.append(record)
        self.total_grudges_registered += 1

        atom = None
        if context and hasattr(context, "get_service"):
            ep_eng = context.get_service("epistemic_engine")
            if ep_eng:
                from src.society.epistemic_engine import EpistemicStatus, VisibilityTier, CarrierType
                atom = ep_eng.create_atom(
                    title=f"Enduring Grudge: {category} by {perpetrator.name}",
                    content=f"{bearer.name} harbors deep, unresolved grievance against {perpetrator.name} for {category}.",
                    status=EpistemicStatus.FACT,
                    visibility=VisibilityTier.INTERNAL_MIND,
                    carrier_type=CarrierType.MIND,
                    subject_id=bearer.id,
                    actor_id=perpetrator.id,
                    emotional_relevance=2.0,  # Permanent emotional anchor
                    created_tick=current_tick,
                    tags=["grudge", "vendetta", category.lower(), perpetrator.id.lower()],
                    associative_keys=[perpetrator.id.lower(), "grudge", category.lower()],
                    payload={"bearer_id": bearer.id, "perpetrator_id": perpetrator.id}
                )
                ep_eng.impart_knowledge(bearer, atom, current_tick, salience=1.0)

        return {"success": True, "grudge": record, "atom": atom}

    def reconcile_grudge(self, bearer: Any, perpetrator: Any, context: Any = None, current_tick: int = 0) -> bool:
        """Reconciles grievance between bearer and perpetrator, removing grudge and damping hostility."""
        removed = False
        new_grudges = []
        for g in self.grudges:
            if g["bearer_id"] == bearer.id and g["perpetrator_id"] == perpetrator.id:
                removed = True
            else:
                new_grudges.append(g)
        self.grudges = new_grudges

        if removed:
            self.total_grudges_reconciled += 1
            bearer.adjust_feeling("resentment", -25.0)
            bearer.adjust_feeling("contentment", 10.0)

            if context and hasattr(context, "get_service"):
                ep_eng = context.get_service("epistemic_engine")
                if ep_eng:
                    traces = ep_eng.npc_memories.get(bearer.id, {})
                    for trace in traces.values():
                        if "grudge" in trace.atom.tags and trace.atom.actor_id == perpetrator.id:
                            trace.salience = 0.0

        return removed

    def process_daily_grudge_decay(self, context: Optional[Any] = None) -> None:
        """Gradually decays salience of unresolved grudges unless rekindled by encounters."""
        pass
