"""
Unified Information and Communication Subsystem.
Consolidates all settlement communication channels into a single pipeline subsystem:
- Civic Notice Boards & Municipal Bulletins
- Social Rumor & Word-of-Mouth Diffusion
- Watch Crime Reports & Incident Alerts
- Shadow Intelligence & Wealthy Mark Appraisals
- Workshop Mentorship & Trade Study
"""
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.society.information_networks import UnifiedInformationEngine, InformationChannelType

class UnifiedInformationSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_information_and_communication"
    name = "Unified Information and Communication Subsystem"
    tick_stage = TickStage.SOCIAL_AND_RELATIONAL
    tick_frequency = 1
    execution_priority = 15
    is_enabled = True

    def __init__(self):
        self.information_engine = UnifiedInformationEngine.get_instance()
        self.diffusion_interval: int = 60

    def initialize(self, context: WorldContext) -> None:
        context.register_service("unified_information_engine", self.information_engine)

        # Seed initial public notices
        public_plaza = context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square"
        self.information_engine.publish_item(
            channel=InformationChannelType.CIVIC_NOTICES,
            topic="MUNICIPAL_WELCOME",
            headline="Oakwood Municipal Notice: Civic Harmony & Trade Ordinances",
            content="All citizens are reminded that honest labor is protected by municipal law, and complaints may be lodged at Town Hall.",
            target_location_id=public_plaza,
            current_tick=0,
            custom_duration=28800 # 20 days
        )

    def on_tick(self, tick: int, context: WorldContext) -> None:
        self.on_tick_adaptive(tick, context, delta_ticks=1)

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        # Hourly information lifecycle and ambient diffusion
        is_due = tick > 0 and (
            tick % self.diffusion_interval == 0
            or (delta_ticks > 1 and (tick // self.diffusion_interval != (tick - delta_ticks) // self.diffusion_interval))
        )
        if is_due:
            self.information_engine.process_lifecycle_and_ambient_diffusion(context, tick)

            # Bridge dynamic job postings into the unified information channels
            job_eng = context.get_service("job_posting_engine")
            if job_eng and hasattr(job_eng, "active_postings"):
                for post in job_eng.active_postings.values():
                    if (
                        post.created_tick == tick
                        or (delta_ticks > 1 and (tick - delta_ticks) <= post.created_tick <= tick)
                    ):
                        # Translate into unified information item
                        if post.channel.value == "OFFICIAL":
                            self.information_engine.publish_item(
                                channel=InformationChannelType.CIVIC_NOTICES,
                                topic=f"JOB_{post.category.value}",
                                headline=f"Notice: {post.title}",
                                content=f"{post.description} Reward: {post.reward_gold:.1f}g.",
                                target_location_id=post.location_id,
                                payload={"posting_id": post.posting_id, "reward_gold": post.reward_gold},
                                current_tick=tick
                            )
                        else:
                            self.information_engine.publish_item(
                                channel=InformationChannelType.SHADOW_INTELLIGENCE,
                                topic=f"ILLICIT_{post.category.value}",
                                headline=f"Shadow Tip: {post.title}",
                                content=f"{post.description} Bounty: {post.reward_gold:.1f}g.",
                                target_location_id=post.location_id,
                                payload={"posting_id": post.posting_id, "bounty_gold": post.reward_gold},
                                current_tick=tick
                            )
