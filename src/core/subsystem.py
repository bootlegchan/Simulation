"""Modular simulation subsystem pipeline kernel with adaptive multi-rate dispatching and live profiling."""
from abc import ABC, abstractmethod
from enum import Enum
import time
from typing import Any, Dict, List, Optional
from src.core.context import WorldContext

class TickStage(Enum):
    PRE_TICK_ENVIRONMENT = "PRE_TICK_ENVIRONMENT"
    COGNITIVE_DECISION = "COGNITIVE_DECISION"
    ACTION_EXECUTION = "ACTION_EXECUTION"
    ECONOMIC_PRODUCTION = "ECONOMIC_PRODUCTION"
    SOCIAL_AND_RELATIONAL = "SOCIAL_AND_RELATIONAL"
    URBAN_METABOLISM = "URBAN_METABOLISM"
    POST_TICK_MAINTENANCE = "POST_TICK_MAINTENANCE"

class ISimulationSubsystem(ABC):
    """Abstract contract for modular simulation subsystems."""
    subsystem_id: str = "base_subsystem"
    name: str = "Base Subsystem"
    tick_stage: TickStage = TickStage.ACTION_EXECUTION
    tick_frequency: int = 1
    execution_priority: int = 50
    is_enabled: bool = True

    @abstractmethod
    def initialize(self, context: WorldContext) -> None:
        pass

    @abstractmethod
    def on_tick(self, tick: int, context: WorldContext) -> None:
        pass

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        """Adaptive multi-rate tick dispatching. Defaults to calling standard on_tick."""
        self.on_tick(tick, context)

class SubsystemPipelineManager:
    """Manages ordered dispatching of subsystems per tick stage with high-resolution performance profiling."""

    def __init__(self):
        self.subsystems: List[ISimulationSubsystem] = []
        self.subsystem_timings_ms: Dict[str, float] = {}
        self.subsystem_call_counts: Dict[str, int] = {}
        self.subsystem_errors: Dict[str, int] = {}
        self.total_pipeline_time_ms: float = 0.0
        self.recent_tick_durations_ms: List[float] = []

    def register_subsystem(self, subsystem: ISimulationSubsystem) -> None:
        self.subsystems.append(subsystem)
        self.subsystems.sort(key=lambda s: s.execution_priority)
        if subsystem.subsystem_id not in self.subsystem_timings_ms:
            self.subsystem_timings_ms[subsystem.subsystem_id] = 0.0
            self.subsystem_call_counts[subsystem.subsystem_id] = 0
            self.subsystem_errors[subsystem.subsystem_id] = 0

    def load_from_manifest(self, manifest: Dict[str, Any], context: WorldContext) -> None:
        pass

    def dispatch_stage(self, stage: TickStage, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        for sub in self.subsystems:
            if sub.is_enabled and sub.tick_stage == stage:
                freq = max(1, sub.tick_frequency)
                # True if due on this tick or boundary was crossed during delta_ticks
                is_due = (
                    freq <= 1
                    or tick % freq == 0
                    or (delta_ticks > 1 and (tick // freq != (tick - delta_ticks) // freq))
                )
                if is_due:
                    t0 = time.perf_counter()
                    try:
                        if hasattr(sub, "on_tick_adaptive"):
                            sub.on_tick_adaptive(tick, context, delta_ticks=delta_ticks)
                        else:
                            sub.on_tick(tick, context)
                    except Exception as e:
                        self.subsystem_errors[sub.subsystem_id] = self.subsystem_errors.get(sub.subsystem_id, 0) + 1
                        raise e
                    finally:
                        dur_ms = (time.perf_counter() - t0) * 1000.0
                        self.subsystem_timings_ms[sub.subsystem_id] = self.subsystem_timings_ms.get(sub.subsystem_id, 0.0) + dur_ms
                        self.subsystem_call_counts[sub.subsystem_id] = self.subsystem_call_counts.get(sub.subsystem_id, 0) + 1

    def dispatch_tick(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        t0 = time.perf_counter()
        for stage in TickStage:
            self.dispatch_stage(stage, tick, context, delta_ticks=delta_ticks)
        tick_dur_ms = (time.perf_counter() - t0) * 1000.0
        self.total_pipeline_time_ms += tick_dur_ms
        self.recent_tick_durations_ms.append(tick_dur_ms)
        if len(self.recent_tick_durations_ms) > 100:
            self.recent_tick_durations_ms = self.recent_tick_durations_ms[-100:]

    def get_performance_profile(self) -> Dict[str, Any]:
        """Returns detailed live timing profile across all simulation subsystems."""
        avg_tick = sum(self.recent_tick_durations_ms) / max(1, len(self.recent_tick_durations_ms)) if self.recent_tick_durations_ms else 0.0
        return {
            "subsystem_timings_ms": {k: round(v, 2) for k, v in self.subsystem_timings_ms.items()},
            "subsystem_call_counts": dict(self.subsystem_call_counts),
            "subsystem_errors": dict(self.subsystem_errors),
            "avg_tick_duration_ms": round(avg_tick, 3),
            "total_pipeline_time_ms": round(self.total_pipeline_time_ms, 2),
            "active_subsystems_count": sum(1 for s in self.subsystems if s.is_enabled),
            "total_registered_subsystems": len(self.subsystems)
        }

    def reset_profiling(self) -> None:
        """Resets timing statistics."""
        for k in self.subsystem_timings_ms:
            self.subsystem_timings_ms[k] = 0.0
            self.subsystem_call_counts[k] = 0
            self.subsystem_errors[k] = 0
        self.total_pipeline_time_ms = 0.0
        self.recent_tick_durations_ms.clear()
