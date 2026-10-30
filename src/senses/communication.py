from typing import Any, Dict, List

class CommunicationChannel:
    """Handles social gossip, rumor, and information propagation."""

    @staticmethod
    def propagate_rumor(speaker_id: str, listener_id: str, rumor: Dict[str, Any], confidence: float = 0.9) -> Dict[str, Any]:
        propagated = dict(rumor)
        propagated["source_speaker"] = speaker_id
        propagated["confidence"] = round(confidence * 0.9, 2)
        return propagated
