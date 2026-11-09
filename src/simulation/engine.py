from src.entities.lifecycle_mortality import DemiseEngine
"""SimulationEngine Microkernel."""
from enum import Enum
from pathlib import Path
from typing import Set, Any, Dict, List, Optional, Union

from src.core.clock import SimulationClock
from src.core.randomness import SeededRandom
from src.core.events import EventBus, DomainEvent
from src.core.context import WorldContext
from src.core.subsystem import SubsystemPipelineManager, TickStage
from src.configuration.loader import ContentLoader
from src.configuration.hot_reload import PackHotReloader
from src.api.local_interface import SimulationConnector, LocalVisualAPI
from src.economy.taxation import MunicipalTaxEngine
from src.economy.work_shifts import WorkplaceLaborDemandEngine
from src.economy.job_postings import DynamicJobPostingEngine
from src.society.courtroom_lawsuits import CourtroomLawsuitEngine, LawsuitRegistry
from src.society.romance import RomanceEngine, RelationshipStageRegistry
from src.world.prolonged_gatherings import GatheringRegistry
from src.society.joint_commitments import CommitmentRegistry, BilateralCommitmentEngine
from src.ai.elastic_working_memory import ElasticWorkingMemoryEngine
from src.society.household_economy import HouseholdEconomyEngine
from src.society.social_opinions import DirectionalOpinionEngine
from src.society.memory_grudges import MemoryGrudgeEngine
from src.world.climate import MicroClimateEngine
from src.world.urban_growth import UrbanGrowthEngine
from src.subsystems.cognitive import CognitiveAgentSubsystem
from src.subsystems.politics_and_justice import PoliticsAndJusticeSubsystem
from src.subsystems.information_and_communication import UnifiedInformationSubsystem
from src.subsystems.environment_and_weather import EnvironmentAndWeatherSubsystem
from src.subsystems.commodity_production import CommodityProductionSubsystem
from src.society.information_networks import UnifiedInformationEngine
from src.society.factions import FactionPoliticalEngine
from src.society.municipal_decrees import MunicipalDecreeEngine
from src.economy.supply_chain import CommoditySupplyChainEngine
from src.core.temporal_scheduler import HierarchicalTemporalScheduler
from src.society.social_clubs import SocialClubEngine
from src.society.fraternal_aid import FraternalAidEngine
from src.society.recreation_games import RecreationGameEngine
from src.society.dilemmas_and_confession import MoralDilemmaEngine
from src.society.life_goals import LifeGoalEngine
from src.society.epistemic_engine import EpistemicEngine
from src.ai.attentional_mindspace import AttentionalMindspaceEngine
from src.ai.desire_hierarchy import DesireHierarchyEngine
from src.ai.means_end_volition import MeansEndVolitionEngine

class LifecycleState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

class SimulationEngine:
    """Master simulation microkernel coordinating context, event bus, and pipeline."""

    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        self.lifecycle_state = LifecycleState.UNINITIALIZED
        self.context = WorldContext(data_dir=self.data_dir)
        self.pipeline_manager = SubsystemPipelineManager()
        self.loader = ContentLoader(self.data_dir)
        self.hot_reloader: Optional[PackHotReloader] = None

    @property
    def clock(self) -> SimulationClock:
        return self.context.clock

    @property
    def random(self) -> SeededRandom:
        return self.context.random

    @property
    def event_bus(self) -> EventBus:
        return self.context.event_bus

    @property
    def settlements(self) -> Dict[str, Any]:
        return self.context.settlements

    @property
    def npcs(self) -> Dict[str, Any]:
        return self.context.npcs

    @property
    def objects(self) -> Dict[str, Any]:
        return self.context.objects

    @property
    def item_definitions(self) -> Dict[str, Any]:
        return self.context.item_definitions

    @property
    def micro_climate_engine(self) -> Any:
        return self.context.get_service("micro_climate_engine")

    @property
    def gathering_registry(self) -> Any:
        return self.context.get_service("gathering_registry")

    @property
    def commitment_registry(self) -> Any:
        return self.context.get_service("commitment_registry")

    @property
    def lawsuit_registry(self) -> Any:
        return self.context.get_service("lawsuit_registry")

    @property
    def relationship_stage_registry(self) -> Any:
        return self.context.get_service("relationship_stage_registry")

    @property
    def tax_engine(self) -> Any:
        return self.context.get_service("tax_engine")

    @property
    def job_posting_engine(self) -> Any:
        return self.context.get_service("job_posting_engine")

    @property
    def information_engine(self) -> Any:
        return self.context.get_service("unified_information_engine")

    @property
    def workplace_labor_demand_engine(self) -> Any:
        return self.context.get_service("workplace_labor_demand_engine")

    @property
    def temporal_scheduler(self) -> Any:
        return self.context.get_service("temporal_scheduler")

    @property
    def supply_chain_engine(self) -> Any:
        return self.context.get_service("supply_chain_engine")

    @property
    def faction_political_engine(self) -> Any:
        return self.context.get_service("faction_political_engine")

    @property
    def municipal_decree_engine(self) -> Any:
        return self.context.get_service("municipal_decree_engine")

    @property
    def epistemic_engine(self) -> Any:
        return self.context.get_service("epistemic_engine")

    @property
    def social_club_engine(self) -> Any:
        return self.context.get_service("social_club_engine")

    @property
    def fraternal_aid_engine(self) -> Any:
        return self.context.get_service("fraternal_aid_engine")

    @property
    def recreation_game_engine(self) -> Any:
        return self.context.get_service("recreation_game_engine")

    @property
    def moral_dilemma_engine(self) -> Any:
        return self.context.get_service("moral_dilemma_engine")

    @property
    def life_goal_engine(self) -> Any:
        return self.context.get_service("life_goal_engine")

    @property
    def attentional_mindspace_engine(self) -> Any:
        return self.context.get_service("attentional_mindspace_engine")

    @property
    def desire_hierarchy_engine(self) -> Any:
        return self.context.get_service("desire_hierarchy_engine")

    @property
    def means_end_volition_engine(self) -> Any:
        return self.context.get_service("means_end_volition_engine")

    def get_connector(self) -> SimulationConnector:
        return SimulationConnector(self)

    def get_visual_api(self) -> LocalVisualAPI:
        return LocalVisualAPI(self)

    def initialize(self, seed: Optional[int] = 42, scenario_filename: str = "oakwood_baseline.json", stochastic: bool = False) -> None:
        self.lifecycle_state = LifecycleState.INITIALIZING
        self.context.random = SeededRandom.create_stochastic() if stochastic else SeededRandom(seed=seed)
        self.context.clock = SimulationClock()

        # Register services
        self.context.register_service("tax_engine", MunicipalTaxEngine())
        self.context.register_service("courtroom_lawsuit_engine", CourtroomLawsuitEngine())
        self.context.register_service("lawsuit_registry", LawsuitRegistry.get_instance())
        self.context.register_service("romance_engine", RomanceEngine())
        self.context.register_service("relationship_stage_registry", RelationshipStageRegistry.get_instance())
        self.context.register_service("gathering_registry", GatheringRegistry.get_instance())
        self.context.register_service("commitment_registry", CommitmentRegistry.get_instance())
        self.context.register_service("bilateral_commitment_engine", BilateralCommitmentEngine())
        self.context.register_service("elastic_working_memory_engine", ElasticWorkingMemoryEngine())
        self.context.register_service("household_economy_engine", HouseholdEconomyEngine())
        self.context.register_service("directional_opinion_engine", DirectionalOpinionEngine())
        self.context.register_service("memory_grudge_engine", MemoryGrudgeEngine())
        clim_inst = MicroClimateEngine.get_instance()
        clim_inst.apply_seed_initialization(seed or 42)
        self.context.register_service("micro_climate_engine", clim_inst)
        self.context.register_service("weather_and_climate_engine", clim_inst)

        demise_inst = DemiseEngine.get_instance()
        demise_inst.demise_history.clear()
        demise_inst.total_deaths_count = 0
        self.context.register_service("demise_engine", demise_inst)
        self.context.register_service("urban_growth_engine", UrbanGrowthEngine())
        wl_inst = WorkplaceLaborDemandEngine.get_instance()
        wl_inst.active_requisitions.clear()
        wl_inst.surge_history.clear()
        self.context.register_service("workplace_labor_demand_engine", wl_inst)

        jp_inst = DynamicJobPostingEngine.get_instance()
        jp_inst.active_postings.clear()
        jp_inst.posting_history.clear()
        jp_inst._last_illicit_tick = -9999
        self.context.register_service("job_posting_engine", jp_inst)

        info_inst = UnifiedInformationEngine.get_instance()
        info_inst.active_items.clear()
        info_inst.item_history.clear()
        info_inst.npc_memory_traces.clear()
        info_inst.npc_knowledge_ledger.clear()
        info_inst.active_waves.clear()
        self.context.register_service("unified_information_engine", info_inst)

        sched_inst = HierarchicalTemporalScheduler.get_instance()
        sched_inst.clear()
        self.context.register_service("temporal_scheduler", sched_inst)

        sc_inst = CommoditySupplyChainEngine.get_instance()
        sc_inst.reseed_stocks()
        self.context.register_service("supply_chain_engine", sc_inst)

        fact_inst = FactionPoliticalEngine.get_instance()
        fact_inst.factions.clear()
        fact_inst._load_from_settings()
        self.context.register_service("faction_political_engine", fact_inst)

        dec_inst = MunicipalDecreeEngine.get_instance()
        dec_inst.active_decrees.clear()
        dec_inst.decree_history.clear()
        self.context.register_service("municipal_decree_engine", dec_inst)

        club_inst = SocialClubEngine.get_instance()
        club_inst.clear()
        self.context.register_service("social_club_engine", club_inst)

        aid_inst = FraternalAidEngine.get_instance()
        aid_inst._load_from_settings()
        aid_inst.relief_history.clear()
        aid_inst.last_dues_tick = -9999
        self.context.register_service("fraternal_aid_engine", aid_inst)

        game_inst = RecreationGameEngine.get_instance()
        game_inst._load_from_settings()
        game_inst.contest_history.clear()
        self.context.register_service("recreation_game_engine", game_inst)

        dil_inst = MoralDilemmaEngine.get_instance()
        dil_inst.transgression_history.clear()
        dil_inst.confession_history.clear()
        self.context.register_service("moral_dilemma_engine", dil_inst)

        lg_inst = LifeGoalEngine.get_instance()
        lg_inst._load_from_settings()
        lg_inst.agent_goals.clear()
        lg_inst.completed_milestones.clear()
        self.context.register_service("life_goal_engine", lg_inst)

        ep_inst = EpistemicEngine.get_instance()
        ep_inst.clear()
        self.context.register_service("epistemic_engine", ep_inst)

        mind_inst = AttentionalMindspaceEngine.get_instance()
        mind_inst.clear()
        self.context.register_service("attentional_mindspace_engine", mind_inst)

        desire_inst = DesireHierarchyEngine.get_instance()
        desire_inst.clear()
        self.context.register_service("desire_hierarchy_engine", desire_inst)

        volition_inst = MeansEndVolitionEngine.get_instance()
        volition_inst.clear()
        self.context.register_service("means_end_volition_engine", volition_inst)

        from src.society.civic import MunicipalTreasury
        self.context.municipal_treasury = MunicipalTreasury(balance=500.0)

        # Register subsystems
        self.pipeline_manager.register_subsystem(EnvironmentAndWeatherSubsystem())
        self.pipeline_manager.register_subsystem(CognitiveAgentSubsystem())
        self.pipeline_manager.register_subsystem(CommodityProductionSubsystem())
        self.pipeline_manager.register_subsystem(PoliticsAndJusticeSubsystem())
        self.pipeline_manager.register_subsystem(UnifiedInformationSubsystem())
        for sub in self.pipeline_manager.subsystems:
            sub.initialize(self.context)

        # Ingest content
        self.loader.load_content(scenario_filename)
        self._hydrate_context()
        self.lifecycle_state = LifecycleState.READY

    def _hydrate_context(self) -> None:
        from src.world.model import Settlement, Building, Room
        from src.entities.npc import NPC
        from src.entities.item import ItemDefinition
        from src.entities.object import InteractiveObject

        for s_id, s_data in self.loader.loaded_data.get("settlements", {}).items():
            self.context.settlements[s_id] = Settlement.from_dict(s_data)

        self.context.spatial_graph.build_graph(self.context.settlements)

        for n_id, n_data in self.loader.loaded_data.get("npcs", {}).items():
            self.context.npcs[n_id] = NPC.from_dict(n_data)

        for o_id, o_data in self.loader.loaded_data.get("objects", {}).items():
            self.context.objects[o_id] = InteractiveObject.from_dict(o_data)

        for i_id, i_data in self.loader.loaded_data.get("items", {}).items():
            self.context.item_definitions[i_id] = ItemDefinition.from_dict(i_data)

        # Households auto-discovery
        hh_eng = self.context.get_service("household_economy_engine")
        if hh_eng:
            hh_eng.auto_discover_households(self.context.npcs)

        # Faction membership discovery
        fact_eng = self.context.get_service("faction_political_engine")
        if fact_eng:
            fact_eng.auto_discover_members(self.context)
            for f_id, f_obj in fact_eng.factions.items():
                self.context.factions[f_id] = f_obj

        # Social clubs, fraternal aid, and life goals discovery
        club_eng = self.context.get_service("social_club_engine")
        if club_eng:
            club_eng.auto_discover_members(self.context)

        aid_eng = self.context.get_service("fraternal_aid_engine")
        if aid_eng:
            aid_eng.auto_discover_members(self.context)

        lg_eng = self.context.get_service("life_goal_engine")
        if lg_eng:
            lg_eng.assign_goals(self.context)

        # Mental maps & spatial landmarks discovery
        ep_eng = self.context.get_service("epistemic_engine")
        if ep_eng and hasattr(self.context, "spatial_graph"):
            for npc in self.context.npcs.values():
                known_locs = [loc for loc in (npc.home_location_id, npc.work_location_id, "room_village_square") if loc]
                for loc in known_locs:
                    neighbors = list(self.context.spatial_graph.adj_list.get(loc, set()))
                    room_name = loc.replace("room_", "").replace("_", " ").title()
                    ep_eng.learn_spatial_landmark(npc, loc, room_name, neighbors, self.context, current_tick=self.clock.current_tick)

    def start(self) -> None:
        self.clock.resume()
        self.lifecycle_state = LifecycleState.RUNNING

    def pause(self) -> None:
        self.clock.pause()
        self.lifecycle_state = LifecycleState.PAUSED

    def tick(self, count: int = 1) -> None:
        if self.lifecycle_state != LifecycleState.RUNNING:
            self.start()
        for _ in range(count):
            t = self.clock.advance_tick(1)
            self.pipeline_manager.dispatch_tick(t, self.context)

    def fast_forward(self, total_ticks: int, max_leap: int = 60) -> int:
        """
        Advances simulation using Hierarchical Asynchronous Event-Scheduled Time (HAEST).
        Leaps over dormant intervals analytically while maintaining bitwise reproducibility.
        """
        if self.lifecycle_state != LifecycleState.RUNNING:
            self.start()

        elapsed = 0
        scheduler: Optional[HierarchicalTemporalScheduler] = self.context.get_service("temporal_scheduler")

        while elapsed < total_ticks:
            remaining = total_ticks - elapsed
            next_event_tick = scheduler.peek_next_tick() if scheduler and scheduler.peek_next_tick() else None

            if next_event_tick is not None and next_event_tick > self.clock.current_tick:
                step = min(remaining, next_event_tick - self.clock.current_tick, max_leap)
            else:
                step = min(remaining, max_leap)

            step = max(1, step)
            t = self.clock.advance_tick(step)
            self.pipeline_manager.dispatch_tick(t, self.context, delta_ticks=step)
            elapsed += step

        return self.clock.current_tick

    def tick_adaptive(self, count: int = 1, max_leap: int = 60) -> int:
        """Convenience alias for adaptive temporal fast-forwarding."""
        return self.fast_forward(count, max_leap=max_leap)

    def mount_pack(self, pack_id: str) -> Dict[str, Any]:
        p_dir = self.data_dir / "packs" / pack_id
        res = self.loader.mount_pack_from_dir(p_dir, self.loader.loaded_data)
        self._hydrate_context()
        return res
