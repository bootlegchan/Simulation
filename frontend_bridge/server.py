#!/usr/bin/env python3
"""Loopback-only JSON bridge; the existing SimulationEngine remains authoritative."""
from __future__ import annotations
import argparse
import json
import math
import sys
import threading
import time
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api.local_interface import LocalVisualAPI
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine

MAX_BODY_BYTES = 8192
MAX_TICKS = 100_000


def to_json_value(value: Any, depth: int = 0) -> Any:
    if depth > 32:
        raise ValueError("Response nesting exceeds the supported limit.")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_json_value(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_value(v, depth + 1) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_json_value(value.to_dict(), depth + 1)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_json_value(getattr(value, field.name), depth + 1) for field in fields(value)}
    raise TypeError("Unsupported response value: %s" % type(value).__name__)


def validate_ticks(value: Any, default: int = 1, maximum: int = MAX_TICKS) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("ticks must be an integer.")
    if not 1 <= value <= maximum:
        raise ValueError("ticks must be between 1 and %s." % maximum)
    return value


def build_snapshot(api: LocalVisualAPI, engine: SimulationEngine, room_id: str) -> dict:
    known_rooms = {
        rid for settlement in engine.settlements.values()
        for building in settlement.buildings.values() for rid in building.rooms.keys()
    }
    active_room = api.get_room_details(room_id) if room_id in known_rooms else {}
    objects = [obj.to_dict() for obj in engine.objects.values() if hasattr(obj, "to_dict")]
    status = api.get_simulation_status()
    climate = api.get_climate_status()
    climate["data_quality"] = {"weather_available": engine.context.get_service("micro_climate_engine") is not None}
    return {
        "schema_version":"1.0",
        "snapshot_id":"%s-%s" % (status.get("tick",0),time.monotonic_ns()),
        "api_version":getattr(api,"API_VERSION","unknown"),
        "status":status,
        "climate":climate,
        "economy":api.get_economy_overview(),
        "settlements":api.get_world_hierarchy(),
        "connections":api.get_spatial_connections(),
        "npcs":api.list_citizens(alive_only=True),
        "objects":objects,
        "active_room":active_room,
        "population":{
            "alive":sum(1 for npc in engine.npcs.values() if getattr(npc,"is_alive",True)),
            "total":len(engine.npcs)
        }
    }


class SimulationTicker:
    def __init__(self, engine: SimulationEngine, lock: threading.RLock, ticks_per_second: int):
        self.engine = engine
        self.lock = lock
        self.interval = 1.0 / ticks_per_second
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run,name="immersive-simulation-ticker",daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3.0)

    def _run(self) -> None:
        deadline = time.monotonic()
        while not self._stop.is_set():
            deadline += self.interval
            if self._stop.wait(max(0.0,deadline-time.monotonic())):
                break
            with self.lock:
                if getattr(getattr(self.engine,"lifecycle_state",None),"name","") == "RUNNING":
                    self.engine.tick(1)


class ApiError(Exception):
    def __init__(self,status: int,code: str,message: str):
        super().__init__(message)
        self.status,self.code,self.message = status,code,message


class BridgeState:
    def __init__(self,engine: SimulationEngine,api: LocalVisualAPI):
        self.engine,self.api = engine,api
        self.lock = threading.RLock()


class BridgeHandler(BaseHTTPRequestHandler):
    state: BridgeState
    server_version = "ImmersiveBridge/1.0"

    def log_message(self,fmt: str,*args: Any) -> None:
        print("[immersive-bridge] "+(fmt % args))

    def _send(self,status: int,payload: Any) -> None:
        encoded = json.dumps(to_json_value(payload),ensure_ascii=False,allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(encoded)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self,status: int,code: str,message: str) -> None:
        self._send(status,{"error":{"code":code,"message":message}})

    def _check_origin(self) -> None:
        origin = self.headers.get("Origin")
        if origin and not origin.startswith(("http://127.0.0.1:","http://localhost:")):
            raise ApiError(403,"origin_rejected","Only local frontend origins are accepted.")

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length","0"))
        except ValueError:
            raise ApiError(400,"invalid_content_length","Content-Length must be an integer.")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ApiError(413,"request_too_large","Request body exceeds the supported limit.")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except (UnicodeDecodeError,json.JSONDecodeError):
            raise ApiError(400,"invalid_json","Request body must be valid UTF-8 JSON.")
        if not isinstance(data,dict):
            raise ApiError(400,"invalid_body","Request body must be a JSON object.")
        return data

    def do_GET(self) -> None:
        try:
            self._check_origin()
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/v1/"):
                raise ApiError(404,"route_not_found","Unknown API route.")
            route = parsed.path[len("/api/v1"):]
            query = parse_qs(parsed.query)
            with self.state.lock:
                api = self.state.api
                if route == "/health":
                    result = {"ok":True,"service":"immersive-bridge","api_version":api.API_VERSION}
                elif route == "/snapshot":
                    room_id = unquote(query.get("room_id",["room_village_square"])[0])
                    result = build_snapshot(api,self.state.engine,room_id)
                elif route.startswith("/rooms/"):
                    result = api.get_room_details(unquote(route[len("/rooms/"):]))
                    if result.get("error"):
                        raise ApiError(404,"room_not_found",result["error"])
                elif route.startswith("/citizens/") and route.endswith("/profile"):
                    citizen_id = unquote(route[len("/citizens/"):-len("/profile")].strip("/"))
                    result = api.get_citizen_profile(citizen_id)
                    if result.get("error"):
                        raise ApiError(404,"citizen_not_found",result["error"])
                elif route == "/simulation/status":
                    result = api.get_simulation_status()
                else:
                    raise ApiError(404,"route_not_found","Unknown API route.")
            self._send(200,result)
        except ApiError as exc:
            self._error(exc.status,exc.code,exc.message)
        except Exception as exc:
            self._error(500,"internal_error","%s: %s" % (type(exc).__name__,exc))

    def do_POST(self) -> None:
        try:
            self._check_origin()
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/v1/"):
                raise ApiError(404,"route_not_found","Unknown API route.")
            route = parsed.path[len("/api/v1"):]
            body = self._body()
            with self.state.lock:
                api = self.state.api
                if route == "/simulation/pause":
                    result = api.pause()
                elif route == "/simulation/resume":
                    result = api.resume()
                elif route == "/simulation/step":
                    result = api.step(validate_ticks(body.get("ticks")))
                    if body.get("pause_after",True):
                        result = api.pause()
                elif route == "/simulation/fast-forward":
                    ticks = validate_ticks(body.get("ticks"),60)
                    max_leap = validate_ticks(body.get("max_leap"),60,1000)
                    result = api.fast_forward(ticks,max_leap)
                    if body.get("pause_after",True):
                        result = api.pause()
                else:
                    raise ApiError(404,"route_not_found","Unknown command.")
            self._send(200,result)
        except ApiError as exc:
            self._error(exc.status,exc.code,exc.message)
        except ValueError as exc:
            self._error(400,"invalid_argument",str(exc))
        except Exception as exc:
            self._error(500,"internal_error","%s: %s" % (type(exc).__name__,exc))


def run_server(host: str = "127.0.0.1",port: int = 8765,seed: int = 42,
               scenario: str = "oakwood_baseline.json",ticks_per_second: int = 1,paused: bool = False) -> None:
    if host not in ("127.0.0.1","localhost"):
        raise ValueError("The immersive bridge must bind to loopback.")
    if not 1 <= ticks_per_second <= 60:
        raise ValueError("ticks_per_second must be between 1 and 60.")
    engine = SimulationEngine(get_default_data_dir())
    engine.initialize(seed=seed,scenario_filename=scenario)
    api = engine.get_visual_api()
    if not paused:
        api.resume()
    state = BridgeState(engine,api)
    BridgeHandler.state = state
    server = ThreadingHTTPServer((host,port),BridgeHandler)
    ticker = SimulationTicker(engine,state.lock,ticks_per_second)
    ticker.start()
    print("Immersive bridge ready at http://%s:%s/api/v1" % (host,server.server_port))
    print("Scenario: %s | NPCs: %s | Ticks/sec: %s" % (scenario,len(engine.npcs),ticks_per_second))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping immersive bridge...")
    finally:
        ticker.stop()
        server.shutdown()
        server.server_close()
        with state.lock:
            engine.pause()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local simulation bridge for the immersive Godot frontend.")
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--scenario",default="oakwood_baseline.json")
    parser.add_argument("--ticks-per-second",type=int,default=1)
    parser.add_argument("--paused",action="store_true")
    args = parser.parse_args()
    run_server(args.host,args.port,args.seed,args.scenario,args.ticks_per_second,args.paused)


if __name__ == "__main__":
    main()
