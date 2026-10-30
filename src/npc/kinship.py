"""
Multi-Generational Kinship Networks, Family Trees, Lineage, and Inheritance.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

class KinshipRelation(Enum):
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    SPOUSE = "SPOUSE"
    GRANDPARENT = "GRANDPARENT"
    GRANDCHILD = "GRANDCHILD"
    IN_LAW = "IN_LAW"

@dataclass
class FamilyTree:
    family_id: str
    family_name: str
    head_npc_id: str
    member_ids: Set[str] = field(default_factory=set)
    family_heirlooms: List[str] = field(default_factory=list)
    ancestral_home_id: Optional[str] = None
    family_reputation_score: float = 75.0

class KinshipGraph:
    """Tracks explicit multi-generational kinship relationships, lineage, and family dynamics."""

    def __init__(self):
        self.relations: Dict[str, Dict[str, KinshipRelation]] = {}  # npc_a -> {npc_b -> KinshipRelation}
        self.family_trees: Dict[str, FamilyTree] = {}  # family_id -> FamilyTree

    def register_relation(self, npc_a_id: str, npc_b_id: str, relation: KinshipRelation) -> None:
        if npc_a_id not in self.relations:
            self.relations[npc_a_id] = {}
        if npc_b_id not in self.relations:
            self.relations[npc_b_id] = {}

        self.relations[npc_a_id][npc_b_id] = relation

        # Reciprocal relation
        reciprocal_map = {
            KinshipRelation.PARENT: KinshipRelation.CHILD,
            KinshipRelation.CHILD: KinshipRelation.PARENT,
            KinshipRelation.SIBLING: KinshipRelation.SIBLING,
            KinshipRelation.SPOUSE: KinshipRelation.SPOUSE,
            KinshipRelation.GRANDPARENT: KinshipRelation.GRANDCHILD,
            KinshipRelation.GRANDCHILD: KinshipRelation.GRANDPARENT,
            KinshipRelation.IN_LAW: KinshipRelation.IN_LAW,
        }
        self.relations[npc_b_id][npc_a_id] = reciprocal_map.get(relation, KinshipRelation.IN_LAW)

    def get_relation(self, npc_a_id: str, npc_b_id: str) -> Optional[KinshipRelation]:
        return self.relations.get(npc_a_id, {}).get(npc_b_id)

    def get_kin_ids(self, npc_id: str) -> List[str]:
        return list(self.relations.get(npc_id, {}).keys())

    def create_family_tree(self, family_id: str, family_name: str, head_npc_id: str, ancestral_home_id: Optional[str] = None) -> FamilyTree:
        tree = FamilyTree(
            family_id=family_id,
            family_name=family_name,
            head_npc_id=head_npc_id,
            member_ids={head_npc_id},
            ancestral_home_id=ancestral_home_id
        )
        self.family_trees[family_id] = tree
        return tree

    def add_family_member(self, family_id: str, npc_id: str) -> None:
        if family_id in self.family_trees:
            self.family_trees[family_id].member_ids.add(npc_id)

    def execute_inheritance(
        self,
        deceased_npc_id: str,
        npcs: Dict[str, Any],
        social_network: Any
    ) -> Dict[str, Any]:
        """
        Executes family inheritance upon NPC death:
        Passes wealth, home property title, and heirlooms to surviving primary kin.
        """
        if deceased_npc_id not in npcs:
            return {"success": False, "reason": "Deceased NPC not found"}

        deceased = npcs[deceased_npc_id]
        kin_map = self.relations.get(deceased_npc_id, {})

        # Priority 1: Spouse
        spouses = [k for k, rel in kin_map.items() if rel == KinshipRelation.SPOUSE and k in npcs]
        # Priority 2: Children
        children = [k for k, rel in kin_map.items() if rel == KinshipRelation.CHILD and k in npcs]
        # Priority 3: Siblings
        siblings = [k for k, rel in kin_map.items() if rel == KinshipRelation.SIBLING and k in npcs]

        primary_heir_id = None
        if spouses:
            primary_heir_id = spouses[0]
        elif children:
            primary_heir_id = children[0]
        elif siblings:
            primary_heir_id = siblings[0]

        inherited_wealth = deceased.wealth
        inherited_items = list(deceased.inventory)

        if primary_heir_id and primary_heir_id in npcs:
            heir = npcs[primary_heir_id]
            heir.wealth += inherited_wealth
            heir.inventory.extend(inherited_items)
            deceased.wealth = 0.0
            deceased.inventory.clear()

            return {
                "success": True,
                "primary_heir_id": primary_heir_id,
                "inherited_wealth": inherited_wealth,
                "inherited_items_count": len(inherited_items),
            }

        return {
            "success": True,
            "primary_heir_id": None,
            "inherited_wealth": 0.0,
            "inherited_items_count": 0,
            "note": "No surviving kin; wealth escheats to town treasury."
        }
