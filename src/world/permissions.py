from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.entities.object import InteractiveObject

class PermissionsEngine:
    """Manages object ownership, room privacy, memberships, and usage rules."""

    @staticmethod
    def can_access_object(npc: NPC, obj: InteractiveObject) -> Dict[str, Any]:
        # 1. Owner check
        if obj.owner_id is not None and obj.owner_id != npc.id:
            # Check family / household permission or explicit key
            if obj.owner_id not in npc.access_permissions and f"key_{obj.owner_id}" not in npc.access_permissions:
                # Check if it's a public or library object requiring membership
                if "requires_membership" in obj.capabilities:
                    required_perm = f"{obj.id}_membership"
                    if required_perm not in npc.access_permissions and "library_membership" not in npc.access_permissions:
                        return {
                            "allowed": False,
                            "reason": "Requires active Membership/Permit",
                            "is_trespassing": False,
                            "required_permission": required_perm
                        }
                elif "private_property" in obj.capabilities:
                    return {
                        "allowed": False,
                        "reason": f"Private Property owned by '{obj.owner_id}'",
                        "is_trespassing": True,
                        "required_permission": f"key_{obj.owner_id}"
                    }

        # 2. Check borrowing limit for library shelves / archives
        if "borrowable" in obj.capabilities:
            borrowed_count = sum(1 for item in npc.inventory if "borrowed_book" in item.item_def_id)
            if borrowed_count >= 2 and "library_membership" not in npc.access_permissions:
                return {
                    "allowed": False,
                    "reason": "Exceeded maximum borrowing limit (2 items max)",
                    "is_trespassing": False
                }

        return {
            "allowed": True,
            "reason": "Access Granted",
            "is_trespassing": False
        }

    @staticmethod
    def grant_permission(npc: NPC, permission: str) -> None:
        if permission not in npc.access_permissions:
            npc.access_permissions.append(permission)

    @staticmethod
    def revoke_permission(npc: NPC, permission: str) -> None:
        if permission in npc.access_permissions:
            npc.access_permissions.remove(permission)
