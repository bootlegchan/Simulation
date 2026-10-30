from typing import Dict, List, Any

class SecretSociety:
    def __init__(self, society_id: str, name: str, secret_passcode: str):
        self.id = society_id
        self.name = name
        self.secret_passcode = secret_passcode
        self.members: List[str] = []

    def add_member(self, npc_id: str, passcode: str) -> bool:
        if passcode == self.secret_passcode:
            if npc_id not in self.members:
                self.members.append(npc_id)
            return True
        return False

    def is_member(self, npc_id: str) -> bool:
        return npc_id in self.members

class DualLoyaltyEvaluator:
    @staticmethod
    def evaluate_conflict(official_faction_id: str, secret_society_id: str, present_npc_factions: List[str]) -> float:
        if official_faction_id in present_npc_factions and secret_society_id in present_npc_factions:
            return 0.8
        return 0.0

class WhistleblowerEngine:
    @staticmethod
    def expose_society(informant_id: str, society: SecretSociety) -> Dict[str, Any]:
        return {
            "informant_id": informant_id,
            "society_id": society.id,
            "is_exposed": True,
            "exposed_members": list(society.members)
        }
