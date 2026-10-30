from typing import Any, Dict

class ActionClassification:
    """Contextual tagging of actions for legality and social intent."""

    @staticmethod
    def classify_action(action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        tags = {
            "is_legal": True,
            "social_intent": "neutral",
            "is_aggressive": False
        }

        if action_type == "steal":
            tags["is_legal"] = False
            tags["social_intent"] = "exploitative"
            tags["is_aggressive"] = True
        elif action_type == "bribe":
            tags["is_legal"] = False
            tags["social_intent"] = "corrupt"
        elif action_type == "trade":
            tags["social_intent"] = "cooperative"

        return tags
