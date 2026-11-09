"""
Social Clubs, Confraternities, and Fraternal Sodalities.
Operates 100% on declarative configurations from data/settings/social_clubs.json.
Models open vs. gated membership policies, temporary guest participation,
clandestine secrecy oaths, and continuous taste/state alignment.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from src.configuration.settings import SettingsRegistry

@dataclass
class SocialClub:
    club_id: str
    name: str
    description: str
    membership_policy: str = "OPEN"      # OPEN, GATED, SECRET
    is_secret: bool = False              # If True, members swear an oath of silence
    secrecy_oath: bool = False
    guest_policy: str = "ALLOWED"        # ALLOWED, INVITE_ONLY, FORBIDDEN
    required_trial_sessions: int = 2     # Sessions needed before permanent membership induction
    meeting_room_keywords: List[str] = field(default_factory=list)
    preferred_meeting_start_hour: float = 18.0
    preferred_meeting_end_hour: float = 22.0
    eligible_occupations: List[str] = field(default_factory=list)
    min_extraversion: float = 0.0
    peer_bonding_multiplier: float = 1.40
    morale_contentment_boost: float = 12.0
    stress_relief_bonus: float = -10.0
    reputation_focus: str = "general"
    state_requirements: Dict[str, Any] = field(default_factory=dict)
    member_ids: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.club_id

    def is_npc_eligible(self, npc: Any) -> bool:
        """Evaluates formal club eligibility based on policy and criteria."""
        if self.membership_policy == "OPEN":
            return True

        occ = (getattr(npc, "occupation", "") or "").lower()
        if self.eligible_occupations:
            if not any(k.lower() in occ for k in self.eligible_occupations):
                return False

        if self.min_extraversion > 0.0:
            ext = float(getattr(npc, "personality", {}).get("extraversion", 0.5))
            if ext < self.min_extraversion:
                return False

        # Secret club gating: requires crime or underworld ties
        if self.membership_policy == "SECRET":
            vices = getattr(npc, "vices", {}) or {}
            crime_prop = float(vices.get("crime_propensity", 0.0))
            if crime_prop < float(self.state_requirements.get("min_crime_propensity", 20.0)):
                return False

        return True

    def calculate_taste_and_state_suitability(self, npc: Any) -> Tuple[bool, float, str]:
        """
        Evaluates whether an NPC's current somatic state and continuous tastes
        qualify and motivate them to join a gathering of this club.
        """
        needs = getattr(npc, "needs", {}) or {}
        feelings = getattr(npc, "feelings", {}) or {}
        p = getattr(npc, "personality", {}) or {}
        vices = getattr(npc, "vices", {}) or {}
        sp = getattr(npc, "social_profile", {}) or {}

        energy = float(needs.get("energy", 100.0))
        stress = float(feelings.get("stress", 0.0))
        alcohol = float(vices.get("alcohol_dependence", 0.0))
        crime_prop = float(vices.get("crime_propensity", 0.0))
        honor = float(sp.get("moral_values", {}).get("honor", 0.5))

        reqs = self.state_requirements or {}
        min_e = float(reqs.get("min_energy", 15.0))
        max_s = float(reqs.get("max_stress", 85.0))

        # 1. Somatic State Check
        if energy < min_e:
            return False, 0.0, f"{npc.name} is too exhausted (energy {energy:.1f} < {min_e:.1f})"
        if stress > max_s:
            return False, 0.0, f"{npc.name} is under acute panic/stress ({stress:.1f} > {max_s:.1f})"

        # Specific vice / sobriety filters
        max_alc = reqs.get("max_alcohol")
        if max_alc is not None and alcohol > float(max_alc):
            return False, 0.0, f"{npc.name} is inebriated and turned away from solemn conclave"

        min_crime = reqs.get("min_crime_propensity")
        if min_crime is not None and crime_prop < float(min_crime):
            return False, 0.0, f"{npc.name} lacks the required underworld nerve"

        # 2. Continuous Tastes & Alignment
        ext = float(p.get("extraversion", 0.5))
        agree = float(p.get("agreeableness", 0.5))
        openness = float(p.get("openness", 0.5))

        taste_score = 0.0
        if self.reputation_focus == "recreation":
            gambling = float(vices.get("gambling_drive", 0.0))
            taste_score = (ext * 35.0) + (gambling * 0.40) + (alcohol * 0.25)
        elif self.reputation_focus == "piety":
            taste_score = (honor * 45.0) + (agree * 25.0) - (crime_prop * 0.50)
        elif self.reputation_focus == "craftsmanship":
            cons = float(p.get("conscientiousness", 0.5))
            taste_score = (cons * 40.0) + (openness * 30.0)
        elif self.reputation_focus == "subterfuge":
            taste_score = (crime_prop * 0.60) + ((1.0 - honor) * 35.0)

        min_align = float(reqs.get("min_taste_alignment", 0.0))
        if taste_score < min_align:
            return False, taste_score, f"{npc.name}'s tastes and mood do not align with {self.name} ({taste_score:.1f} < {min_align:.1f})"

        return True, taste_score, "State and tastes welcome in gathering"

    def is_meeting_hour(self, hour: float) -> bool:
        if self.preferred_meeting_start_hour <= self.preferred_meeting_end_hour:
            return self.preferred_meeting_start_hour <= hour <= self.preferred_meeting_end_hour
        else:
            return hour >= self.preferred_meeting_start_hour or hour <= self.preferred_meeting_end_hour


class SocialClubEngine:
    """
    Central Social Club, Confraternity, and Secret Syndicate Engine.
    Handles open vs gated club policies, guest trial participation,
    clandestine secrecy enforcement, and continuous taste/state suitability.
    """
    _instance: Optional["SocialClubEngine"] = None

    @classmethod
    def get_instance(cls) -> "SocialClubEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.clubs: Dict[str, SocialClub] = {}
        # Tracks trial sessions: club_id -> {npc_id: sessions_attended}
        self.trial_attendance: Dict[str, Dict[str, int]] = {}
        self.total_club_gatherings_count: int = 0
        self.total_guests_participated_count: int = 0
        self.total_inductions_count: int = 0
        self._load_from_settings()

    def clear(self) -> None:
        self.trial_attendance.clear()
        self.total_club_gatherings_count = 0
        self.total_guests_participated_count = 0
        self.total_inductions_count = 0
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        cfg = SettingsRegistry.get_instance().get("social_clubs")
        club_defs = cfg.get("social_clubs", {})
        self.clubs.clear()

        for c_id, data in club_defs.items():
            self.clubs[c_id] = SocialClub(
                club_id=c_id,
                name=data.get("name", "Social Club"),
                description=data.get("description", ""),
                membership_policy=data.get("membership_policy", "OPEN"),
                is_secret=bool(data.get("is_secret", False)),
                secrecy_oath=bool(data.get("secrecy_oath", False)),
                guest_policy=data.get("guest_policy", "ALLOWED"),
                required_trial_sessions=int(data.get("required_trial_sessions", 2)),
                meeting_room_keywords=list(data.get("meeting_room_keywords", ["tavern"])),
                preferred_meeting_start_hour=float(data.get("preferred_meeting_start_hour", 18.0)),
                preferred_meeting_end_hour=float(data.get("preferred_meeting_end_hour", 22.0)),
                eligible_occupations=list(data.get("eligible_occupations", [])),
                min_extraversion=float(data.get("min_extraversion", 0.0)),
                peer_bonding_multiplier=float(data.get("peer_bonding_multiplier", 1.40)),
                morale_contentment_boost=float(data.get("morale_contentment_boost", 12.0)),
                stress_relief_bonus=float(data.get("stress_relief_bonus", -10.0)),
                reputation_focus=data.get("reputation_focus", "general"),
                state_requirements=dict(data.get("state_requirements", {}))
            )

    def auto_discover_members(self, context: Any) -> None:
        """Registers founding members based on initial eligibility."""
        if not hasattr(context, "npcs") or not context.npcs:
            return
        if not self.clubs:
            self._load_from_settings()

        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            for club in self.clubs.values():
                # For open clubs, citizens start as members if they match basic vocation/personality
                if club.membership_policy in ("OPEN", "GATED") and club.is_npc_eligible(npc):
                    if npc.id not in club.member_ids:
                        club.member_ids.append(npc.id)

    def evaluate_club_gathering(
        self,
        club_id: str,
        room_id: str,
        context: Any,
        current_tick: int
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether co-located club members and suitable guests engage in a conclave.
        Respects secrecy oaths, temporary trial attendance, and state/taste suitability.
        """
        club = self.clubs.get(club_id)
        if not club or not hasattr(context, "npcs") or not room_id:
            return None

        vt = context.clock.current_virtual_time if hasattr(context, "clock") and context.clock else None
        hour = (vt.hour + vt.minute / 60.0) if vt else ((current_tick // 60) % 24)

        if not club.is_meeting_hour(hour):
            return None

        r_low = room_id.lower()
        if not any(k in r_low for k in club.meeting_room_keywords):
            return None

        # Filter co-located citizens in the room
        occupants = [
            n for n in context.npcs.values()
            if n.location_id == room_id and getattr(n, "is_alive", True)
        ]

        active_members: List[Any] = []
        guest_attendees: List[Any] = []

        for npc in occupants:
            is_member = (npc.id in club.member_ids)
            suitable, score, reason = club.calculate_taste_and_state_suitability(npc)
            if not suitable:
                continue

            if is_member:
                active_members.append(npc)
            elif club.guest_policy in ("ALLOWED", "INVITE_ONLY") and not club.is_secret:
                guest_attendees.append(npc)

        if len(active_members) < 2 and (len(active_members) + len(guest_attendees)) < 2:
            return None

        op_eng = context.get_service("directional_opinion_engine") if hasattr(context, "get_service") else None
        time_iso = context.clock.current_virtual_time_iso if hasattr(context, "clock") and context.clock else f"Tick {current_tick}"

        all_attendees = active_members + guest_attendees
        newly_inducted = []

        # 1. Process Permanent Members
        for member in active_members:
            member.adjust_feeling("contentment", club.morale_contentment_boost)
            member.adjust_feeling("stress", club.stress_relief_bonus)
            member.adjust_feeling("pride", 8.0)
            member.needs["social"] = min(100.0, member.needs.get("social", 50.0) + 20.0)

            if op_eng:
                for other in all_attendees:
                    if other.id != member.id:
                        delta = 6.0 * club.peer_bonding_multiplier
                        op_eng.add_modifier(
                            from_npc=member,
                            to_npc=other,
                            mod_id=f"club_{club.club_id}",
                            desc=f"Fellowship in {club.name}",
                            delta=delta,
                            tick=current_tick
                        )

            member.record_biographical_entry(
                current_tick, time_iso, "CLUB_GATHERING",
                f"Gathered with {len(all_attendees) - 1} brethren of {club.name} at {room_id}."
            )

        # 2. Process Guests & Temporary Trial Participation
        for guest in guest_attendees:
            guest.adjust_feeling("contentment", club.morale_contentment_boost * 0.75)
            guest.adjust_feeling("stress", club.stress_relief_bonus * 0.75)
            guest.needs["social"] = min(100.0, guest.needs.get("social", 50.0) + 18.0)

            club_trials = self.trial_attendance.setdefault(club.club_id, {})
            club_trials[guest.id] = club_trials.get(guest.id, 0) + 1
            sessions = club_trials[guest.id]

            self.total_guests_participated_count += 1
            guest.record_biographical_entry(
                current_tick, time_iso, "CLUB_GUEST_PARTICIPATION",
                f"Participated as a guest at a gathering of {club.name} (Trial session {sessions}/{club.required_trial_sessions})."
            )

            # Permanent Induction after completing trial sessions
            if sessions >= club.required_trial_sessions and guest.id not in club.member_ids:
                club.member_ids.append(guest.id)
                self.total_inductions_count += 1
                newly_inducted.append(guest.name)
                guest.adjust_feeling("pride", 20.0)
                guest.adjust_feeling("contentment", 15.0)
                guest.record_biographical_entry(
                    current_tick, time_iso, "CLUB_MEMBERSHIP_INDUCTED",
                    f"Formally inducted into permanent membership of {club.name} following trial participation."
                )

        # 3. Secret Club Enforce Gag Order
        # Notice boards and loud acoustic emissions are strictly suppressed for secret clubs
        self.total_club_gatherings_count += 1
        return {
            "success": True,
            "club_id": club.club_id,
            "club_name": club.name,
            "is_secret": club.is_secret,
            "attendees_count": len(all_attendees),
            "members_count": len(active_members),
            "guests_count": len(guest_attendees),
            "newly_inducted": newly_inducted,
            "room_id": room_id
        }
