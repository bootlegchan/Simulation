from src.entities.lifecycle_mortality import DemiseEngine
"""
Cognitive Agent Subsystem with Continuous Field Dynamics & HAEST Temporal Intent Horizons.
Operates on continuous homeostatic gradients, vocational shift potentials,
asynchronous intent horizons, and topological spatial transit without implicit finite state machines.
"""
from typing import Any, Dict, List, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.ai.drive_strategies import DriveStrategyRegistry
from src.ai.preemption import TaskPreemptionEngine
from src.ai.utility import UtilityEvaluator
from src.entities.daily_life_rhythms import DynamicDailyRhythmEngine, DailyRhythmPhase
from src.entities.occupations import OccupationRegistry
from src.economy.work_shifts import WorkplaceLaborDemandEngine
from src.economy.job_postings import DynamicJobPostingEngine, PostingChannel, JobPostingStatus
from src.core.temporal_scheduler import HierarchicalTemporalScheduler, IntentHorizon

class CognitiveAgentSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_cognitive"
    name = "Cognitive Subsystem"
    tick_stage = TickStage.COGNITIVE_DECISION
    tick_frequency = 1
    execution_priority = 10
    is_enabled = True

    def __init__(self):
        self.preemption_engine = TaskPreemptionEngine()
        self.strategy_registry = DriveStrategyRegistry()
        self.labor_demand_engine = WorkplaceLaborDemandEngine.get_instance()
        self.job_posting_engine = DynamicJobPostingEngine.get_instance()
        self.temporal_scheduler: Optional[HierarchicalTemporalScheduler] = None
        self.decision_interval: int = 60

    def initialize(self, context: WorldContext) -> None:
        context.register_service("task_preemption_engine", self.preemption_engine)
        context.register_service("drive_strategy_registry", self.strategy_registry)
        context.register_service("workplace_labor_demand_engine", self.labor_demand_engine)
        context.register_service("job_posting_engine", self.job_posting_engine)
        self.temporal_scheduler = context.get_service("temporal_scheduler") or HierarchicalTemporalScheduler.get_instance()
        context.register_service("temporal_scheduler", self.temporal_scheduler)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        self.on_tick_adaptive(tick, context, delta_ticks=1)

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        # 1. Biological needs and emotional feelings decay continuously via analytical integration
        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            npc.apply_continuous_decay(delta_ticks=delta_ticks, current_tick=tick)
            npc.decay_vices_and_moral_homeostasis()

            # Continuous Epistemic Memory Decay & Associative Sensory Priming
            ep_eng = context.get_service("epistemic_engine") if hasattr(context, "get_service") else None
            if ep_eng:
                ep_eng.apply_memory_decay(npc, tick, delta_ticks=delta_ticks)
                cues = [npc.location_id] if npc.location_id else []
                for p in context.npcs.values():
                    if p.location_id == npc.location_id and p.id != npc.id and getattr(p, "is_alive", True):
                        cues.append(p.id)
                        cues.append(p.name.lower())
                ep_eng.evaluate_associative_priming(npc, cues, context, tick)

            # Continuous Somatic Mortality Assessment (Starvation, Hypothermia, Shock)
            demise_eng = context.get_service("demise_engine") or DemiseEngine.get_instance()
            mortal_cause = demise_eng.evaluate_mortal_risks(npc, tick, context, delta_ticks=delta_ticks)
            if mortal_cause:
                demise_eng.execute_demise_and_succession(npc, mortal_cause, tick, context)
                continue

            # Dynamic preemption evaluation on active somatic signals
            preempt = self.preemption_engine.evaluate_preemption(npc, tick, context)
            if preempt and hasattr(npc, "intent_horizon") and npc.intent_horizon:
                # Emergency preemption breaks active intent horizon immediately
                npc.intent_horizon = None
                if self.temporal_scheduler:
                    self.temporal_scheduler.cancel_events_for_target(npc.id)

        # Daily assessment of proportional income taxes & living expenses (if day boundary crossed)
        is_day_boundary = tick > 0 and (
            tick % 1440 == 0 or (delta_ticks > 1 and (tick // 1440 != (tick - delta_ticks) // 1440))
        )
        if is_day_boundary:
            tax_eng = context.get_service("tax_engine")
            if tax_eng:
                if hasattr(tax_eng, "assess_taxpayer"):
                    mayor = context.find_npc_by_role(["mayor", "magistrate", "notary"])
                    for npc in context.npcs.values():
                        if getattr(npc, "is_alive", True):
                            tax_eng.assess_taxpayer(npc, mayor, context, tick)
                # Assess commercial market stall fees from operational business premises
                if hasattr(tax_eng, "collect_commercial_stall_fees"):
                    tax_eng.collect_commercial_stall_fees(context, tick)

            # Domestic Craft Goods & Tool Maintenance Purchases (Recycles Agrarian & Merchant wealth to Artisans)
            sc_eng = context.get_service("supply_chain_engine")
            if sc_eng:
                for npc in context.npcs.values():
                    if getattr(npc, "is_alive", True) and getattr(npc, "wealth", 0.0) > 60.0:
                        occ_l = (getattr(npc, "occupation", "") or "").lower()
                        if any(k in occ_l for k in ("farmer", "woodcutter", "miller", "laborer", "miner")) and sc_eng.get_stock_level("iron_tools") >= 1.0:
                            tool_price = sc_eng.calculate_market_price("iron_tools")
                            if npc.wealth >= (tool_price + 30.0) and context.random.random() < 0.15:
                                sc_eng.consume_stock("iron_tools", 1.0)
                                npc.wealth = round(npc.wealth - tool_price, 2)
                                smith = context.find_npc_by_role(["smith", "blacksmith"]) if hasattr(context, "find_npc_by_role") else None
                                if smith and getattr(smith, "is_alive", True):
                                    smith.wealth = round(smith.wealth + tool_price, 2)
                                    smith.record_stat("career_earnings_gold", tool_price)

                        if any(k in occ_l for k in ("mayor", "baker", "innkeeper", "merchant", "notary")) and sc_eng.get_stock_level("furniture") >= 1.0:
                            furn_price = sc_eng.calculate_market_price("furniture")
                            if npc.wealth >= (furn_price + 50.0) and context.random.random() < 0.10:
                                sc_eng.consume_stock("furniture", 1.0)
                                npc.wealth = round(npc.wealth - furn_price, 2)
                                carpenter = context.find_npc_by_role(["carpenter"]) if hasattr(context, "find_npc_by_role") else None
                                if carpenter and getattr(carpenter, "is_alive", True):
                                    carpenter.wealth = round(carpenter.wealth + furn_price, 2)
                                    carpenter.record_stat("career_earnings_gold", furn_price)

            # Fraternal mutual aid dues collection & emergency relief
            aid_eng = context.get_service("fraternal_aid_engine")
            if aid_eng:
                aid_eng.collect_daily_dues(context, tick)
                aid_eng.evaluate_emergency_relief(context, tick)

            # Life goal milestone progression evaluation
            lg_eng = context.get_service("life_goal_engine")
            if lg_eng:
                lg_eng.evaluate_milestones(context, tick)

            # Daily domestic upkeep & tool maintenance sink
            from src.configuration.settings import SettingsRegistry
            civ_cfg = SettingsRegistry.get_instance().get("civic_governance")
            col_cfg = civ_cfg.get("cost_of_living", {})
            if col_cfg.get("enabled", True):
                upkeep = float(col_cfg.get("daily_homestead_upkeep_gold", 0.35))
                tool_cost = float(col_cfg.get("daily_tool_maintenance_gold", 0.20))
                poverty_cutoff = float(col_cfg.get("poverty_exemption_wealth_gold", 5.0))

                exempt_cfg = civ_cfg.get("tax_exemptions", {})
                exempt_occs = [k.lower() for k in exempt_cfg.get("exempt_occupations", ["priest", "clergy", "monk", "curate"])]
                exempt_cats = [k.upper() for k in exempt_cfg.get("exempt_building_categories", ["SACRED", "CIVIC"])]

                for npc in context.npcs.values():
                    if getattr(npc, "is_alive", True):
                        occ_title = (getattr(npc, "occupation", "") or "").lower()
                        # Clergy and sacred/civic building exemptions from property/upkeep levies
                        if any(k in occ_title for k in exempt_occs):
                            continue
                        home_bldg = context.find_building_by_room_id(npc.home_location_id) if hasattr(context, "find_building_by_room_id") and npc.home_location_id else None
                        if home_bldg and home_bldg.category in exempt_cats:
                            continue

                        needs_tool = any(k in occ_title for k in ("smith", "carpenter", "farmer", "miner", "mason", "laborer"))
                        total_drain = upkeep + (tool_cost if needs_tool else 0.0)

                        if npc.wealth > poverty_cutoff:
                            actual_deduct = min(round(npc.wealth - poverty_cutoff, 2), total_drain)
                            npc.wealth = max(0.0, round(npc.wealth - actual_deduct, 2))

        # 2. Deliberation Cycle via Continuous Utility Gradients
        is_cycle_due = tick > 0 and (
            tick % self.decision_interval == 0
            or (delta_ticks > 1 and (tick // self.decision_interval != (tick - delta_ticks) // self.decision_interval))
        )
        if is_cycle_due:
            self._execute_cycle(tick, context, delta_ticks=delta_ticks)

    def _execute_cycle(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        hour = context.clock.current_virtual_time.hour if hasattr(context, "clock") and context.clock else (tick // 60) % 24
        time_iso = context.clock.current_virtual_time_iso if context.clock else f"Tick {tick}"
        rhythm_eng = context.get_service("dynamic_daily_rhythm_engine") or DynamicDailyRhythmEngine()
        wm_eng = context.get_service("elastic_working_memory_engine")
        occ_reg = OccupationRegistry.get_instance()

        from src.configuration.settings import SettingsRegistry
        temp_cfg = SettingsRegistry.get_instance().get("temporal_engine", {}).get("temporal_engine", {})
        act_durations = temp_cfg.get("action_durations", {})

        # -------------------------------------------------------------
        # A. DYNAMIC JOB POSTINGS: Process Lifecycle & Settlement Needs
        # -------------------------------------------------------------
        self.job_posting_engine.process_posting_lifecycle(context, tick)
        self.job_posting_engine.evaluate_settlement_needs(context, tick)

        # -------------------------------------------------------------
        # B. WORKPLACE SURGES: Real-time demand spikes (e.g. extra bartenders)
        # -------------------------------------------------------------
        new_surges = self.labor_demand_engine.evaluate_workplace_surges(context, tick)
        for surge in new_surges:
            candidate = self.labor_demand_engine.find_available_surge_candidate(surge, context)
            if candidate:
                candidate.record_biographical_entry(
                    tick, time_iso, "SURGE_JOB_ACCEPTED",
                    f"Accepted surge labor requisition as {surge.job_title} at {surge.location_id} with {surge.hourly_wage_multiplier:.1f}x pay."
                )

        active_claimed_jobs = {
            p.assigned_worker_id: p for p in self.job_posting_engine.active_postings.values()
            if p.status == JobPostingStatus.CLAIMED and p.assigned_worker_id
        }
        active_surge_npc_ids = {
            req.assigned_npc_id: req for req in self.labor_demand_engine.active_requisitions.values()
            if req.is_active and req.assigned_npc_id
        }

        # -------------------------------------------------------------
        # C. CITIZEN CONTINUOUS UTILITY DELIBERATION (Zero Implicit Machines)
        # -------------------------------------------------------------
        for npc in context.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue

            claimed_job = active_claimed_jobs.get(npc.id)
            on_surge_job = npc.id in active_surge_npc_ids
            surge_info = active_surge_npc_ids.get(npc.id)

            # Continuous scanning for available open jobs based on proximity and character alignment
            if not claimed_job and not on_surge_job:
                curr_loc = npc.location_id or (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")
                visible_postings = []
                if any(k in curr_loc.lower() for k in ("square", "hall", "plaza", "market", "bakery", "shop")):
                    visible_postings.extend(self.job_posting_engine.get_open_postings(PostingChannel.OFFICIAL))
                else:
                    visible_postings.extend(self.job_posting_engine.get_open_postings(PostingChannel.OFFICIAL, location_id=curr_loc))

                crime_prop = float(getattr(npc, "vices", {}).get("crime_propensity", 0.0))
                if any(k in curr_loc.lower() for k in ("underworld", "vice", "tavern", "alley", "cellar", "shadow")) or crime_prop >= 20.0:
                    visible_postings.extend(self.job_posting_engine.get_open_postings(PostingChannel.ILLICIT))

                if visible_postings:
                    evaluation = self.job_posting_engine.evaluate_npc_job_seeking(npc, visible_postings, context)
                    if evaluation:
                        chosen_post, score, reason = evaluation
                        self.job_posting_engine.claim_job_posting(chosen_post.posting_id, npc, context, tick)
                        claimed_job = chosen_post
                        active_claimed_jobs[npc.id] = chosen_post

            # Calculate continuous environmental and vocational potential modifiers
            env_mods: Dict[str, float] = {}
            shift = occ_reg.get_shift_window(getattr(npc, "occupation", ""))
            energy = float(npc.needs.get("energy", 100.0))
            wealth = float(getattr(npc, "wealth", 0.0))

            # Continuous Vocational Shift Potential
            if shift.is_within_shift(hour):
                # Inside official vocational hours: strong work alignment
                env_mods["work_production"] = 35.0
                if energy >= 30.0:
                    env_mods["rest"] = -25.0
            elif shift.is_overtime_window(hour):
                if energy >= 32.0:
                    wants_ot, mult, _ = self.labor_demand_engine.evaluate_worker_overtime_choice(npc, shift, context, is_surge_job=False)
                    if wants_ot:
                        env_mods["work_production"] = 30.0 * mult
                        env_mods["rest"] = -15.0
            else:
                # Outside shift: check pre-shift preparation
                hours_before = (shift.base_start_hour - hour) % 24.0
                if 0.0 < hours_before <= 1.5:
                    env_mods["work_production"] = 15.0
                # Evening communal recreation & dining
                elif 17.0 <= hour < 22.0:
                    env_mods["socialize"] = env_mods.get("socialize", 0.0) + 25.0
                    env_mods["communal_dining"] = env_mods.get("communal_dining", 0.0) + 20.0
                    if energy >= 25.0:
                        env_mods["rest"] = env_mods.get("rest", 0.0) - 15.0
                # Night rest hours
                elif hour >= 22.0 or hour < 6.0:
                    env_mods["rest"] = env_mods.get("rest", 0.0) + 35.0
                    env_mods["work_production"] = env_mods.get("work_production", 0.0) - 30.0

            # Contractual commitments provide continuous directional pull
            if claimed_job:
                env_mods["work_production"] = env_mods.get("work_production", 0.0) + 45.0 * (energy / 100.0)
            elif on_surge_job:
                env_mods["work_production"] = env_mods.get("work_production", 0.0) + 40.0 * (energy / 100.0)

            # Sleep inertia: once asleep, waking up requires feeling rested or acute hunger
            if getattr(npc, "current_action", "") in ("SLEEP_REST", "COLLAPSE_FATIGUE"):
                if energy < 90.0 and npc.needs.get("hunger", 0.0) < 65.0:
                    env_mods["rest"] = env_mods.get("rest", 0.0) + 40.0

            # Life goal aspirational utility steering modifiers
            lg_eng = context.get_service("life_goal_engine")
            lg_mods = lg_eng.get_utility_steering_modifiers(npc) if lg_eng else {}

            # Elastic Maslow Desire Hierarchy Modifiers
            desire_eng = context.get_service("desire_hierarchy_engine")
            desire_mods = desire_eng.calculate_utility_modifiers(npc, context, tick) if desire_eng else {}
            for d_name, d_val in desire_mods.items():
                env_mods[d_name] = env_mods.get(d_name, 0.0) + d_val

            # Attentional Mindspace: Evaluate dynamic stream of consciousness & thought biases
            mind_eng = context.get_service("attentional_mindspace_engine")
            mind_eval = mind_eng.evaluate_attentional_mindspace(npc, context, tick) if mind_eng else {}
            att_biases = mind_eval.get("utility_biases", {})

            # Evaluate continuous competing utilities
            r_temp = getattr(npc, "_current_room_temperature", None)
            utilities = UtilityEvaluator.evaluate_drives(
                npc.needs,
                npc.personality,
                env_modifiers=env_mods,
                ambition=float(getattr(npc, "mental_attributes", {}).get("ambition", 50.0)) / 100.0,
                room_temperature=r_temp,
                life_goal_modifiers=lg_mods,
                attentional_biases=att_biases
            )

            # Working memory attentional salience filter
            if wm_eng:
                utilities, _ = wm_eng.filter_active_salience_queue(npc, utilities, context, tick)

            # Multinomial Logit Sampling across competing utilities (Pure Choice, Zero Hard Overrides)
            chosen_drive, _, _ = UtilityEvaluator.sample_choice_multinomial_logit(utilities, context.random, temperature=12.0)

            # -------------------------------------------------------------
            # D. TOPOLOGICAL SPATIAL TRANSIT (No Instant Teleportation)
            # -------------------------------------------------------------
            target_destination = None
            if chosen_drive == "work_production" or (claimed_job and chosen_drive == "work_production"):
                if claimed_job:
                    target_destination = claimed_job.target_work_location_id
                elif on_surge_job and surge_info:
                    target_destination = surge_info.location_id
                else:
                    target_destination = npc.work_location_id or occ_reg.get_fallback_work_location(getattr(npc, "occupation", ""))
            elif chosen_drive == "rest":
                target_destination = npc.home_location_id or (context.get_central_public_room() if hasattr(context, "get_central_public_room") else "room_village_square")
            elif chosen_drive in ("socialize", "communal_dining"):
                spouse_id = npc.social_profile.get("spouse_id") if hasattr(npc, "social_profile") else None
                partner_id = npc.social_profile.get("partner_id") if hasattr(npc, "social_profile") else None
                target_partner = context.npcs.get(spouse_id or partner_id) if (spouse_id or partner_id) else None

                # Priest maintains morning pastoral hours in the chapel
                if "priest" in (getattr(npc, "occupation", "") or "").lower() and 8.0 <= hour <= 12.0:
                    target_destination = "room_chapel"
                # Penitent seeking spiritual confession in the chapel
                elif float(npc.get_feeling("guilt")) >= 20.0:
                    target_destination = "room_chapel"
                elif target_partner and getattr(target_partner, "is_alive", True) and getattr(npc, "unmet_intimacy_tension", 0.0) > 25.0:
                    target_destination = target_partner.location_id
                elif chosen_drive == "communal_dining":
                    target_destination = "room_tavern"

            # If the selected action requires being in a specific facility and the agent is elsewhere:
            if target_destination and npc.location_id != target_destination and hasattr(context, "spatial_graph"):
                path = context.spatial_graph.find_shortest_path(npc.location_id or target_destination, target_destination)
                if path and len(path) > 1:
                    # Move one topological room step towards the goal
                    next_room = path[1]
                    npc.location_id = next_room
                    npc.current_action = f"COMMUTE_TO_{target_destination}"
                    npc.intent_horizon = IntentHorizon(
                        action_name=f"COMMUTE_TO_{target_destination}",
                        started_tick=tick,
                        duration_ticks=1,
                        target_destination=target_destination
                    )

                    # Learn newly entered room into spatial mental map
                    ep_eng = context.get_service("epistemic_engine")
                    if ep_eng:
                        neighbors = list(context.spatial_graph.adj_list.get(next_room, set()))
                        room_name = next_room.replace("room_", "").replace("_", " ").title()
                        ep_eng.learn_spatial_landmark(npc, next_room, room_name, neighbors, context, tick)

                    continue

            # Execute drive at current location
            act_name = self.strategy_registry.execute_drive(chosen_drive, npc, context, tick, time_iso, hour, {})
            if claimed_job and chosen_drive == "work_production":
                act_name = f"JOB_{claimed_job.category.value}"
            npc.current_action = act_name

            # Establish continuous IntentHorizon and register in temporal scheduler
            dur = int(act_durations.get(act_name, act_durations.get("DEFAULT", 30)))
            if act_name == "SLEEP_REST":
                hrs_needed = max(1.0, (100.0 - energy) / 14.0)
                dur = int(hrs_needed * 60)
            elif act_name == "LABOR_WORK" or (claimed_job and chosen_drive == "work_production"):
                dur = min(120, max(30, int(shift.standard_duration_hours * 60)))

            npc.intent_horizon = IntentHorizon(
                action_name=act_name,
                started_tick=tick,
                duration_ticks=dur,
                target_destination=target_destination
            )
            if self.temporal_scheduler:
                self.temporal_scheduler.schedule_event(
                    scheduled_tick=tick + dur,
                    event_type="AGENT_INTENT_EXPIRED",
                    target_id=npc.id
                )

            # Update diagnostic rhythm profile for monitoring without overriding behavior
            rhythm_eng.evaluate_current_phase(npc, tick, context)
