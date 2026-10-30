"""
Cognitive Agent Subsystem.
Manages NPC physiological need decay, granular emotional feelings decay,
habituation routines, subjective fog-of-war cognition, and autonomous decision-action cycles.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.core.events import DomainEvent
from src.ai.cognitive_planning import HabituationEngine, SubjectiveCognitionEngine
from src.ai.utility import UtilityEvaluator
from src.world.environment import EnvironmentState, WeatherType
from src.behaviours.actions import ActionRegistry


class CognitiveAgentSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_cognitive"
    name = "Cognitive Agents & Autonomy Subsystem"
    tick_stage = TickStage.COGNITIVE_DECISION
    tick_frequency = 1  # Runs every tick for need and feeling decay
    execution_priority = 10
    is_enabled = True

    def __init__(self):
        self.habituation_engine: Optional[HabituationEngine] = None
        self.cognition_engine: Optional[SubjectiveCognitionEngine] = None
        self.autonomy_enabled: bool = True
        self.decision_interval: int = 60  # Evaluate decisions hourly (60 ticks)
        self.temperature: float = 12.0

    def initialize(self, context: WorldContext) -> None:
        habit_cfg = context.settings.get("habituation_loops")
        self.habituation_engine = HabituationEngine(habit_cfg)

        bias_cfg = context.settings.get("cognitive_biases")
        self.cognition_engine = SubjectiveCognitionEngine(bias_cfg)

        autonomy_cfg = context.settings.get("simulation", {}).get("autonomy", {})
        self.autonomy_enabled = autonomy_cfg.get("enabled", True)
        self.decision_interval = autonomy_cfg.get("decision_interval_ticks", 60)
        self.temperature = float(autonomy_cfg.get("softmax_temperature", 12.0))

        context.register_service("habituation_engine", self.habituation_engine)
        context.register_service("subjective_cognition_engine", self.cognition_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        # 1. Need Decay & Emotional Feelings Decay (every tick)
        for npc in context.npcs.values():
            npc.apply_need_decay()
            if hasattr(npc, "decay_feelings"):
                npc.decay_feelings()

        # 2. Hourly Autonomous Decision-Action Cycle
        if self.autonomy_enabled and tick > 0 and tick % self.decision_interval == 0:
            self._execute_autonomous_cycle(tick, context)

        # 3. Daily Cognitive checks: Missed habituation routines & withdrawal
        if tick > 0 and tick % 1440 == 0:
            if self.habituation_engine:
                for npc in context.npcs.values():
                    self.habituation_engine.process_daily_habit_decay_and_withdrawal(npc)

    def _execute_autonomous_cycle(self, tick: int, context: WorldContext) -> None:
        time_iso = context.clock.current_virtual_time_iso if context.clock else f"Tick {tick}"
        hour = (tick // 60) % 24
        env = EnvironmentState(weather=WeatherType.CLEAR, season="SUMMER")
        env_mods = env.calculate_utility_modifiers(hour)

        for npc in context.npcs.values():
            if getattr(npc, "current_state", "") in ("ARRESTED", "INCAPACITATED"):
                continue

            # Evaluate utilities from needs, feelings, personality, and vices
            utilities = UtilityEvaluator.evaluate_drives(
                needs=npc.needs,
                personality=npc.personality,
                vices=npc.vices,
                cognition=npc.cognition,
                feelings=npc.feelings,
                env_modifiers=env_mods,
            )

            # Sample choice using Softmax / Multinomial Logit with SeededRandom
            chosen_drive, sel_prob, _ = UtilityEvaluator.sample_choice_multinomial_logit(
                utilities, context.random, temperature=self.temperature
            )

            # Resolve action and record in biographical lifetime log
            action_name = chosen_drive

            if chosen_drive == "satisfy_hunger":
                food_item = next(
                    (i for i in npc.inventory if "food" in i.item_def_id or "bread" in i.item_def_id or "cider" in i.item_def_id),
                    None
                )
                if food_item:
                    ActionRegistry.eat(npc, food_item)
                    action_name = "EAT_FROM_STORES"
                    npc.record_biographical_entry(tick, time_iso, "ROUTINE_METABOLISM", "Ate a meal from personal stores to satisfy hunger.")
                elif npc.wealth >= 4.0:
                    npc.wealth -= 4.0
                    npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 0.0) - 35.0)
                    npc.adjust_feeling("contentment", 10.0)
                    action_name = "BUY_AND_EAT_FOOD"
                    npc.record_biographical_entry(tick, time_iso, "COMMERCE_LIVING", "Purchased and ate hearth bread at the village market.", {"cost_gold": 4.0})
                else:
                    action_name = "ENDURE_HUNGER"
                    npc.adjust_feeling("stress", 15.0)
                    npc.record_biographical_entry(tick, time_iso, "HARDSHIP", "Suffered from hunger with no coin or provisions remaining.")

            elif chosen_drive == "rest":
                if npc.home_location_id:
                    npc.location_id = npc.home_location_id
                ActionRegistry.sleep(npc)
                action_name = "SLEEP_REST"
                npc.record_biographical_entry(tick, time_iso, "ROUTINE_REST", f"Retired to quarters at {npc.location_id} to sleep and regain stamina.")

            elif chosen_drive == "work_production":
                if npc.work_location_id:
                    npc.location_id = npc.work_location_id
                earned = ActionRegistry.work(npc)
                action_name = "LABOR_WORK"
                npc.record_biographical_entry(tick, time_iso, "ECONOMIC_LABOR", f"Worked as {npc.occupation} in {npc.location_id}, earning {earned:.1f} gold.", {"earned_gold": earned})

            elif chosen_drive == "socialize":
                npc.location_id = "room_village_square" if (context.random.random() > 0.5) else "room_tavern_common"
                npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + 25.0)
                npc.adjust_feeling("loneliness", -25.0)
                npc.adjust_feeling("contentment", 15.0)
                action_name = "COMMUNITY_SOCIALIZE"
                npc.record_biographical_entry(tick, time_iso, "SOCIAL_INTERACTION", f"Visited {npc.location_id} to converse and exchange gossip with neighbors.")

            elif chosen_drive in ("courtship_and_romance", "seek_intimacy"):
                npc.adjust_feeling("passion", 20.0)
                npc.adjust_feeling("tenderness", 15.0)
                npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + 20.0)
                action_name = "ROMANTIC_COURTSHIP"
                npc.record_biographical_entry(tick, time_iso, "ROMANCE_INTIMACY", "Shared affectionate moments, nurturing romantic passion and emotional warmth.")

            elif chosen_drive == "spiritual_devotion":
                npc.location_id = "room_chapel_sanctuary"
                npc.adjust_feeling("stress", -25.0)
                npc.adjust_feeling("contentment", 15.0)
                npc.needs["conviction"] = min(100.0, npc.needs.get("conviction", 50.0) + 20.0)
                action_name = "PRAYER_SANCTUARY"
                npc.record_biographical_entry(tick, time_iso, "SPIRITUAL_DEVOTION", "Offered humble prayers at the chapel sanctuary, finding solace from daily trials.")

            elif chosen_drive == "vice_indulgence":
                npc.location_id = "room_vice_parlour"
                cost = min(5.0, npc.wealth)
                npc.wealth -= cost
                npc.adjust_feeling("stress", -20.0)
                npc.adjust_feeling("guilt", 15.0)
                action_name = "INDULGE_VICE"
                npc.record_biographical_entry(tick, time_iso, "VICE_INDULGENCE", f"Spent {cost:.1f} gold in the shadowy cellar vice den seeking escapism.", {"cost_gold": cost})

            elif chosen_drive == "hearth_relaxation":
                if npc.home_location_id:
                    npc.location_id = npc.home_location_id
                npc.adjust_feeling("contentment", 20.0)
                npc.adjust_feeling("loneliness", -20.0)
                action_name = "HEARTH_WARMTH"
                npc.record_biographical_entry(tick, time_iso, "DOMESTIC_LIVING", f"Gathered beside the family hearth at {npc.location_id}, resting in its radiant warmth.")

            elif chosen_drive == "write_diary_reflection":
                npc.adjust_feeling("stress", -20.0)
                npc.adjust_feeling("contentment", 15.0)
                action_name = "WRITE_DIARY"
                npc.record_biographical_entry(tick, time_iso, "INTROSPECTION", "Wrote in private diary, reflecting upon the burdens, relationships, and hopes of life.")

            else:
                action_name = "IDLE_CONTEMPLATE"
                npc.record_biographical_entry(tick, time_iso, "IDLE_ROUTINE", "Paused to rest and observe the shifting moods of the settlement.")

            npc.current_action = action_name

            # Emit domain event for real-time subscribers & telemetry
            context.publish_event(
                event_type="npc_autonomous_action",
                source_id=npc.id,
                payload={
                    "npc_id": npc.id,
                    "action_name": action_name,
                    "chosen_drive": chosen_drive,
                    "location_id": npc.location_id,
                    "dominant_mood": npc.get_dominant_mood(),
                    "wealth": npc.wealth,
                }
            )
