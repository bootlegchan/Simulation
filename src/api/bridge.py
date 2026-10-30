"""
Live State Mutator and External Bridge Interface Engine.
Provides clean, verified runtime state manipulation and RPC execution for external display, UI, and control modules.
"""
import uuid
from typing import Any, Dict, Optional
from src.simulation.engine import SimulationEngine
from src.core.events import DomainEvent
from src.api.dtos import (
    NPCAttributeMutationDTO,
    NPCForceActionDTO,
    ObjectMutationDTO,
    EnvironmentMutationDTO,
    EventInjectionDTO,
    EventDTO,
    BridgeRPCCommandDTO,
    BridgeRPCResponseDTO,
)

class StateMutator:
    """Provides atomic, thread-safe runtime manipulation of simulation entities and environment."""

    @staticmethod
    def mutate_npc(engine: SimulationEngine, npc_id: str, mutation: NPCAttributeMutationDTO) -> Dict[str, Any]:
        if npc_id not in engine.npcs:
            raise KeyError(f"NPC '{npc_id}' not found in simulation engine.")

        npc = engine.npcs[npc_id]
        changes = []

        if mutation.location_id is not None:
            old_loc = npc.location_id
            npc.location_id = mutation.location_id
            engine._place_npc_in_room(npc.id, mutation.location_id)
            changes.append(f"location_id: {old_loc} -> {mutation.location_id}")

        if mutation.wealth is not None:
            old_wealth = npc.wealth
            npc.wealth = max(0.0, mutation.wealth)
            changes.append(f"wealth: {old_wealth} -> {npc.wealth}")

        if mutation.needs is not None:
            for need_key, value in mutation.needs.items():
                old_val = npc.needs.get(need_key, 0.0)
                npc.needs[need_key] = max(0.0, min(100.0, value))
                changes.append(f"needs.{need_key}: {old_val} -> {npc.needs[need_key]}")

        if mutation.current_state is not None:
            old_state = npc.current_state
            npc.current_state = mutation.current_state
            changes.append(f"current_state: {old_state} -> {mutation.current_state}")

        if mutation.vices is not None:
            for vice_key, val in mutation.vices.items():
                npc.vices[vice_key] = max(0.0, min(100.0, val))
                changes.append(f"vices.{vice_key}: {val}")

        if getattr(mutation, "feelings", None) is not None:
            for f_key, f_val in mutation.feelings.items():
                npc.set_feeling(f_key, f_val)
                changes.append(f"feelings.{f_key}: {f_val}")

        if mutation.social_profile_updates is not None:
            npc.social_profile.update(mutation.social_profile_updates)
            changes.append(f"social_profile updated ({len(mutation.social_profile_updates)} fields)")

        # Publish mutation event to EventBus
        current_tick = engine.clock.current_tick if engine.clock else 0
        clock_iso = engine.clock.current_virtual_time_iso if engine.clock else "2026-01-01T06:00:00Z"
        
        evt = DomainEvent(
            event_type="external_npc_mutated",
            tick=current_tick,
            source_id="external_bridge",
            payload={
                "npc_id": npc_id,
                "changes": changes,
                "updated_location_id": npc.location_id,
                "updated_wealth": npc.wealth,
            }
        )
        engine.event_bus.publish(evt)

        return {
            "npc_id": npc_id,
            "status": "MUTATED",
            "changes_applied": changes,
            "current_location_id": npc.location_id,
            "current_wealth": npc.wealth,
            "current_needs": npc.needs,
            "current_state": npc.current_state,
        }

    @staticmethod
    def force_npc_action(engine: SimulationEngine, npc_id: str, action_req: NPCForceActionDTO) -> Dict[str, Any]:
        if npc_id not in engine.npcs:
            raise KeyError(f"NPC '{npc_id}' not found in simulation engine.")

        npc = engine.npcs[npc_id]
        act_type = action_req.action_type.upper()
        npc.current_state = f"FORCED_{act_type}"

        if action_req.target_location_id:
            npc.location_id = action_req.target_location_id
            engine._place_npc_in_room(npc.id, action_req.target_location_id)

        # Satisfaction effects based on forced action
        if act_type == "EAT":
            npc.needs["hunger"] = max(0.0, npc.needs.get("hunger", 50.0) - 40.0)
        elif act_type == "SLEEP":
            npc.needs["energy"] = min(100.0, npc.needs.get("energy", 50.0) + 50.0)
        elif act_type == "SOCIALIZE":
            npc.needs["social"] = min(100.0, npc.needs.get("social", 50.0) + 40.0)

        current_tick = engine.clock.current_tick if engine.clock else 0
        evt = DomainEvent(
            event_type="external_npc_action_forced",
            tick=current_tick,
            source_id="external_bridge",
            payload={
                "npc_id": npc_id,
                "forced_action": act_type,
                "target_location_id": action_req.target_location_id,
                "priority": action_req.override_priority,
            }
        )
        engine.event_bus.publish(evt)

        return {
            "npc_id": npc_id,
            "status": "ACTION_FORCED",
            "forced_action": act_type,
            "location_id": npc.location_id,
            "current_needs": npc.needs,
        }

    @staticmethod
    def mutate_object(engine: SimulationEngine, object_id: str, mutation: ObjectMutationDTO) -> Dict[str, Any]:
        if object_id not in engine.objects:
            raise KeyError(f"Interactive object '{object_id}' not found in simulation engine.")

        obj = engine.objects[object_id]
        changes = []

        if mutation.location_id is not None:
            old_loc = obj.location_id
            obj.location_id = mutation.location_id
            engine._place_object_in_room(obj.id, mutation.location_id)
            changes.append(f"location_id: {old_loc} -> {mutation.location_id}")

        if mutation.is_locked is not None:
            # Add or remove lock permission flag dynamically
            if hasattr(obj, "is_locked"):
                setattr(obj, "is_locked", mutation.is_locked)
            changes.append(f"is_locked: {mutation.is_locked}")

        if mutation.add_capabilities:
            for cap in mutation.add_capabilities:
                if cap not in obj.capabilities:
                    obj.capabilities.append(cap)
            changes.append(f"added capabilities: {mutation.add_capabilities}")

        if mutation.remove_capabilities:
            for cap in mutation.remove_capabilities:
                if cap in obj.capabilities:
                    obj.capabilities.remove(cap)
            changes.append(f"removed capabilities: {mutation.remove_capabilities}")

        current_tick = engine.clock.current_tick if engine.clock else 0
        evt = DomainEvent(
            event_type="external_object_mutated",
            tick=current_tick,
            source_id="external_bridge",
            payload={"object_id": object_id, "changes": changes}
        )
        engine.event_bus.publish(evt)

        return {
            "object_id": object_id,
            "status": "MUTATED",
            "changes_applied": changes,
            "location_id": obj.location_id,
            "capabilities": obj.capabilities,
        }

    @staticmethod
    def mutate_environment(engine: SimulationEngine, mutation: EnvironmentMutationDTO) -> Dict[str, Any]:
        changes = []
        sim_settings = engine.settings.setdefault("environment", {})

        if mutation.weather:
            sim_settings["weather"] = mutation.weather
            changes.append(f"weather: {mutation.weather}")

        if mutation.season:
            sim_settings["season"] = mutation.season
            changes.append(f"season: {mutation.season}")

        if mutation.time_of_day:
            sim_settings["time_of_day"] = mutation.time_of_day
            changes.append(f"time_of_day: {mutation.time_of_day}")

        if mutation.world_tension is not None:
            sim_settings["world_tension"] = mutation.world_tension
            changes.append(f"world_tension: {mutation.world_tension}")

        current_tick = engine.clock.current_tick if engine.clock else 0
        evt = DomainEvent(
            event_type="external_environment_mutated",
            tick=current_tick,
            source_id="external_bridge",
            payload={"changes": changes}
        )
        engine.event_bus.publish(evt)

        return {
            "status": "ENVIRONMENT_MUTATED",
            "changes_applied": changes,
            "current_environment": sim_settings,
        }

    @staticmethod
    def inject_event(engine: SimulationEngine, event_req: EventInjectionDTO) -> EventDTO:
        current_tick = engine.clock.current_tick if engine.clock else 0
        clock_iso = engine.clock.current_virtual_time_iso if engine.clock else "2026-01-01T06:00:00Z"

        evt = DomainEvent(
            event_type=event_req.event_type,
            tick=current_tick,
            source_id=event_req.source_id,
            payload=event_req.payload,
        )
        engine.event_bus.publish(evt)

        return EventDTO(
            event_id=getattr(evt, "event_id", f"evt_{uuid.uuid4().hex[:8]}"),
            event_type=event_req.event_type,
            tick=current_tick,
            source_id=event_req.source_id,
            payload=event_req.payload,
            timestamp_iso=clock_iso,
        )

    @staticmethod
    def execute_rpc_command(engine: SimulationEngine, cmd: BridgeRPCCommandDTO) -> BridgeRPCResponseDTO:
        """Executes a Bridge RPC Command sent by an external module."""
        try:
            ctype = cmd.command_type.upper()
            if ctype == "MUTATE_NPC":
                if not cmd.target_id:
                    return BridgeRPCResponseDTO(command_id=cmd.command_id, success=False, message="Missing target_id for MUTATE_NPC")
                dto = NPCAttributeMutationDTO(**cmd.payload)
                res = StateMutator.mutate_npc(engine, cmd.target_id, dto)
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=True, message="NPC mutated successfully", data=res)

            elif ctype == "FORCE_ACTION":
                if not cmd.target_id:
                    return BridgeRPCResponseDTO(command_id=cmd.command_id, success=False, message="Missing target_id for FORCE_ACTION")
                dto = NPCForceActionDTO(**cmd.payload)
                res = StateMutator.force_npc_action(engine, cmd.target_id, dto)
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=True, message="NPC action forced successfully", data=res)

            elif ctype == "MUTATE_OBJECT":
                if not cmd.target_id:
                    return BridgeRPCResponseDTO(command_id=cmd.command_id, success=False, message="Missing target_id for MUTATE_OBJECT")
                dto = ObjectMutationDTO(**cmd.payload)
                res = StateMutator.mutate_object(engine, cmd.target_id, dto)
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=True, message="Object mutated successfully", data=res)

            elif ctype == "MUTATE_ENV":
                dto = EnvironmentMutationDTO(**cmd.payload)
                res = StateMutator.mutate_environment(engine, dto)
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=True, message="Environment mutated successfully", data=res)

            elif ctype == "INJECT_EVENT":
                dto = EventInjectionDTO(**cmd.payload)
                res_evt = StateMutator.inject_event(engine, dto)
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=True, message="Event injected successfully", data=res_evt.model_dump())

            else:
                return BridgeRPCResponseDTO(command_id=cmd.command_id, success=False, message=f"Unknown RPC command type: '{cmd.command_type}'")

        except Exception as e:
            return BridgeRPCResponseDTO(command_id=cmd.command_id, success=False, message=f"RPC Execution Error: {str(e)}")
