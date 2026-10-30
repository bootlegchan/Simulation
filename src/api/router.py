import asyncio
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if TYPE_CHECKING:
    from src.simulation.runner import SimulationRunner

from src.simulation.engine import SimulationEngine
from src.api.dtos import (
    SimulationTickBatchDTO,
    WorldStateDTO,
    NPCVisualDTO,
    InteractiveObjectDTO,
    SpatialGraphDTO,
    SpatialNodeDTO,
    EventDTO,
    NPCAttributeMutationDTO,
    NPCForceActionDTO,
    ObjectMutationDTO,
    EnvironmentMutationDTO,
    EventInjectionDTO,
    BridgeRPCCommandDTO,
    BridgeRPCResponseDTO,
)
from src.api.bridge import StateMutator
from src.economy.macro import MacroEconomicTracker

class ControlRequest(BaseModel):
    action: str  # "start", "pause", "resume", "stop", "step", "set_tps"
    step_ticks: int = 1
    target_tps: float = 10.0

class ConnectionManager:
    """Manages real-time WebSocket client connections for live 2D/3D visual streaming and bidirectional RPC."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

def create_app(engine: SimulationEngine, runner: Optional[Any] = None) -> FastAPI:
    """Creates FastAPI REST, SSE Event Streaming, and Bidirectional RPC WebSocket Server Application."""
    app = FastAPI(
        title="Social Simulation Engine Visual & Data API Bridge",
        description="REST, SSE Streaming, and Bidirectional RPC WebSocket API for 2D/3D Visual Frontends, UI Dashboards, and External Control Modules",
        version="26.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if runner is None:
        from src.simulation.runner import SimulationRunner
        sim_runner = SimulationRunner(engine, target_tps=10.0)
    else:
        sim_runner = runner

    ws_manager = ConnectionManager()

    def on_tick_subscriber(batch: SimulationTickBatchDTO):
        if ws_manager.active_connections:
            data = batch.model_dump()
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(ws_manager.broadcast(data))
            except RuntimeError:
                pass

    sim_runner.register_subscriber(on_tick_subscriber)

    # =========================================================================
    # 1. SIMULATION STATUS & RUNNER CONTROL ENDPOINTS
    # =========================================================================

    @app.get("/api/v1/simulation/status", response_model=WorldStateDTO, tags=["Status & Control"])
    def get_status():
        batch = sim_runner._build_tick_batch([])
        return batch.world_state

    @app.post("/api/v1/simulation/control", response_model=WorldStateDTO, tags=["Status & Control"])
    def control_simulation(req: ControlRequest):
        act = req.action.lower()
        if act == "start":
            sim_runner.start_live_runner()
        elif act == "pause":
            sim_runner.pause_live_runner()
        elif act == "resume":
            sim_runner.resume_live_runner()
        elif act == "stop":
            sim_runner.stop_live_runner()
        elif act == "step":
            sim_runner.step_ticks(req.step_ticks)
        elif act == "set_tps":
            sim_runner.set_target_tps(req.target_tps)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown control action: '{req.action}'")

        batch = sim_runner._build_tick_batch([])
        return batch.world_state

    # =========================================================================
    # 2. SPATIAL GRAPH & VISUAL PROJECTIONS (FOR 2D/3D ENGINES)
    # =========================================================================

    @app.get("/api/v1/spatial/graph", response_model=SpatialGraphDTO, tags=["Spatial Topology"])
    def get_spatial_graph():
        nodes = {}
        for s_id, sett in engine.settlements.items():
            for b_id, bldg in sett.buildings.items():
                for r_id, room in bldg.rooms.items():
                    x3d, y3d, z3d = sim_runner._project_3d_coordinates(r_id)
                    nodes[r_id] = SpatialNodeDTO(
                        node_id=room.id,
                        name=room.name,
                        node_type="room",
                        x_2d=x3d,
                        y_2d=y3d,
                        x_3d=x3d,
                        y_3d=y3d,
                        z_3d=z3d,
                        connected_node_ids=room.connected_room_ids,
                        contained_object_ids=room.contained_object_ids,
                        occupant_ids=room.occupant_ids,
                    )
        return SpatialGraphDTO(
            settlement_id="settlement_oakwood",
            settlement_name="Oakwood Settlement",
            nodes=nodes,
            building_count=len(engine.settlements.get("settlement_oakwood", {}).buildings) if "settlement_oakwood" in engine.settlements else 0,
            room_count=len(nodes),
        )

    # =========================================================================
    # 3. ENTITY READ ENDPOINTS (NPCS & OBJECTS)
    # =========================================================================

    @app.get("/api/v1/npcs", response_model=Dict[str, NPCVisualDTO], tags=["NPC Query"])
    def get_npcs():
        batch = sim_runner._build_tick_batch([])
        return batch.npcs

    @app.get("/api/v1/npcs/{npc_id}", response_model=Dict[str, Any], tags=["NPC Query"])
    def get_npc_detail(npc_id: str):
        if npc_id not in engine.npcs:
            raise HTTPException(status_code=404, detail=f"NPC '{npc_id}' not found in simulation engine.")
        npc = engine.npcs[npc_id]
        res = npc.to_dict()
        res["visual_dto"] = sim_runner._build_tick_batch([]).npcs.get(npc_id, {}).model_dump() if npc_id in sim_runner._build_tick_batch([]).npcs else {}
        return res

    @app.get("/api/v1/objects", response_model=Dict[str, InteractiveObjectDTO], tags=["Object Query"])
    def get_objects():
        batch = sim_runner._build_tick_batch([])
        return batch.objects

    @app.get("/api/v1/economy", tags=["Macro Telemetry"])
    def get_economy_status():
        gini = MacroEconomicTracker.calculate_gini_coefficient(engine.npcs)
        total_currency = MacroEconomicTracker.calculate_total_currency(engine.npcs)
        return {
            "gini_coefficient": round(gini, 3),
            "total_currency_gold": round(total_currency, 2),
            "npc_count": len(engine.npcs),
        }

    @app.get("/api/v1/events/history", response_model=List[EventDTO], tags=["Event Stream"])
    def get_event_history(limit: int = Query(default=100, ge=1, le=1000)):
        events = engine.event_bus.history[-limit:]
        clock_iso = engine.clock.current_virtual_time_iso if engine.clock else "2026-01-01T06:00:00Z"
        return [
            EventDTO(
                event_id=getattr(e, "event_id", "evt"),
                event_type=getattr(e, "event_type", "tick"),
                tick=getattr(e, "tick", 0),
                source_id=getattr(e, "source_id", "engine"),
                payload=getattr(e, "payload", {}),
                timestamp_iso=getattr(e, "timestamp_iso", clock_iso),
            )
            for e in events
        ]

    # =========================================================================
    # 4. LIVE ATTRIBUTE & DATA MUTATION ENDPOINTS (INBOUND MANIPULATION INTERFACE)
    # =========================================================================

    @app.post("/api/v1/mutate/npc/{npc_id}", tags=["Live Attribute Manipulation"])
    def mutate_npc_attributes(npc_id: str, req: NPCAttributeMutationDTO):
        """Modifies an NPC's live location, wealth, needs, state, vices, or social profile."""
        try:
            return StateMutator.mutate_npc(engine, npc_id, req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mutation error: {str(e)}")

    @app.post("/api/v1/mutate/npc/{npc_id}/action", tags=["Live Attribute Manipulation"])
    def force_npc_action(npc_id: str, req: NPCForceActionDTO):
        """Forces an NPC to perform a specific action (EAT, WORK, SLEEP, BRAWL, GOTO_LOCATION)."""
        try:
            return StateMutator.force_npc_action(engine, npc_id, req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Action forcing error: {str(e)}")

    @app.post("/api/v1/mutate/object/{object_id}", tags=["Live Attribute Manipulation"])
    def mutate_object_state(object_id: str, req: ObjectMutationDTO):
        """Modifies an interactive object's location, lock state, or capabilities."""
        try:
            return StateMutator.mutate_object(engine, object_id, req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Object mutation error: {str(e)}")

    @app.post("/api/v1/mutate/environment", tags=["Live Attribute Manipulation"])
    def mutate_environment_state(req: EnvironmentMutationDTO):
        """Modifies live weather, season, time of day, or world tension."""
        try:
            return StateMutator.mutate_environment(engine, req)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Environment mutation error: {str(e)}")

    @app.post("/api/v1/mutate/events/inject", response_model=EventDTO, tags=["Live Attribute Manipulation"])
    def inject_world_event(req: EventInjectionDTO):
        """Injects a custom shock or domain event into the live simulation EventBus."""
        try:
            return StateMutator.inject_event(engine, req)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Event injection error: {str(e)}")

    # =========================================================================
    # 5. STREAMING & BIDIRECTIONAL RPC ENDPOINTS (SSE & WEBSOCKET BRIDGE)
    # =========================================================================

    @app.get("/api/v1/events/stream", tags=["Live Stream"])
    async def sse_event_stream(request: Request):
        """Server-Sent Events (SSE) HTTP endpoint for streaming live tick state updates."""
        async def event_generator():
            last_tick = engine.clock.current_tick if engine.clock else 0
            while True:
                if await request.is_disconnected():
                    break
                curr_tick = engine.clock.current_tick if engine.clock else 0
                if curr_tick > last_tick:
                    last_tick = curr_tick
                    batch = sim_runner._build_tick_batch([])
                    data_str = json.dumps(batch.model_dump())
                    yield f"event: tick\ndata: {data_str}\n\n"
                await asyncio.sleep(0.05)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.websocket("/api/v1/ws/bridge")
    async def websocket_rpc_bridge(websocket: WebSocket):
        """
        High-Throughput Bidirectional RPC WebSocket Endpoint.
        Streams live tick batches to external display modules AND executes inbound RPC mutation commands in real time!
        """
        await ws_manager.connect(websocket)
        try:
            # Send initial state snapshot on connection
            batch = sim_runner._build_tick_batch([])
            await websocket.send_json({"type": "SNAPSHOT", "data": batch.model_dump()})

            while True:
                data = await websocket.receive_json()
                
                # Check if payload is an RPC mutation command
                if "command_type" in data:
                    cmd_dto = BridgeRPCCommandDTO(**data)
                    rpc_res = StateMutator.execute_rpc_command(engine, cmd_dto)
                    await websocket.send_json({"type": "RPC_RESPONSE", "data": rpc_res.model_dump()})
                
                # Simple control shortcuts
                elif "action" in data:
                    act = data["action"]
                    if act == "step":
                        sim_runner.step_ticks(data.get("count", 1))
                    elif act == "set_tps":
                        sim_runner.set_target_tps(data.get("tps", 10.0))

        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            ws_manager.disconnect(websocket)

    # Retain /api/v1/ws/live for backwards compatibility
    @app.websocket("/api/v1/ws/live")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket_rpc_bridge(websocket)

    return app
