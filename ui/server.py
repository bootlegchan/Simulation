#!/usr/bin/env python3
"""Oakwood browser adapter: serves the UI and a loopback-only JSON API.

Run from the repository root with: python ui/server.py
The adapter owns HTTP transport and DTO serialization; simulation rules remain
inside SimulationEngine and LocalVisualAPI.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import threading
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.api.local_interface import LocalVisualAPI
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine

MAX_BODY_BYTES = 16 * 1024
MAX_TICKS = 100_000


def to_json_value(value: Any, depth: int = 0) -> Any:
    """Convert facade DTOs to JSON-safe values without exposing Python objects."""
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
    return str(value)


def success_payload(data: Any) -> Any:
    return to_json_value(data)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class OakwoodHandler(SimpleHTTPRequestHandler):
    api: LocalVisualAPI
    engine: SimulationEngine
    state_lock: threading.RLock

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def log_message(self, fmt, *args):
        print("[oakwood-http] " + (fmt % args))

    def _send_json(self, status: int, payload: Any):
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: int, code: str, message: str):
        self._send_json(status, {"error": {"code": code, "message": message}})

    def _read_json(self) -> dict:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError:
            raise ApiError(400, "invalid_content_length", "Content-Length must be an integer.")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ApiError(413, "request_too_large", "Request body exceeds the 16 KB limit.")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(400, "invalid_json", "Request body must be valid UTF-8 JSON.")
        if not isinstance(value, dict):
            raise ApiError(400, "invalid_body", "Request body must be a JSON object.")
        return value

    @staticmethod
    def _int_arg(value, name: str, default: int, minimum: int, maximum: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            raise ApiError(400, "invalid_argument", f"{name} must be an integer.")
        if not minimum <= value <= maximum:
            raise ApiError(400, "out_of_range", f"{name} must be between {minimum} and {maximum}.")
        return value

    def _dispatch_get(self, path: str, query: dict[str, list[str]]):
        api = self.api
        if path == "/health":
            return {"ok": True, "service": "oakwood-local-api", "api_version": api.API_VERSION,
                    "engine_state": getattr(getattr(self.engine, "lifecycle_state", None), "name", "UNKNOWN")}
        if path == "/capabilities":
            result = api.get_api_capabilities()
            result["transport"] = {"name": "oakwood-local-http", "version": "1",
                                   "base_path": "/api/v1", "streaming": False}
            result["population"] = {
                "alive": sum(1 for n in self.engine.npcs.values() if getattr(n, "is_alive", True)),
                "total": len(self.engine.npcs)
            }
            return result
        if path == "/simulation/status":
            result = api.get_simulation_status()
            result["population"] = sum(1 for n in self.engine.npcs.values() if getattr(n, "is_alive", True))
            result["total_population"] = len(self.engine.npcs)
            result["data_quality"] = {"weather_available": self.engine.context.get_service("micro_climate_engine") is not None}
            return result
        if path == "/scenarios":
            return api.list_scenarios()
        if path.startswith("/scenarios/"):
            filename = unquote(path[len("/scenarios/"):])
            if not filename or Path(filename).name != filename or not filename.endswith(".json"):
                raise ApiError(400, "invalid_scenario", "Scenario must be a JSON filename.")
            result = api.inspect_scenario(filename)
            if isinstance(result, dict) and result.get("error"):
                raise ApiError(404, "scenario_not_found", result["error"])
            return result
        if path == "/world/hierarchy":
            return api.get_world_hierarchy()
        if path.startswith("/rooms/"):
            room_id = unquote(path[len("/rooms/"):])
            if not room_id:
                raise ApiError(400, "invalid_room_id", "Room ID is required.")
            return api.get_room_details(room_id)
        if path == "/world/connections":
            return api.get_spatial_connections()
        if path == "/world/integrity":
            return api.verify_world_integrity()
        if path == "/citizens":
            role = query.get("role", [None])[0]
            alive_only = query.get("alive_only", ["true"])[0].lower() not in ("false", "0", "no")
            return api.list_citizens(filter_role=role, alive_only=alive_only)
        if path.startswith("/citizens/"):
            parts = path.strip("/").split("/")
            if len(parts) != 3:
                raise ApiError(404, "route_not_found", "Citizen route was not found.")
            citizen_id, section = unquote(parts[1]), parts[2]
            methods = {
                "profile": api.get_citizen_profile,
                "state": api.get_citizen_state,
                "relationships": api.get_citizen_relationships,
                "decision": api.get_citizen_decision_explanation,
                "knowledge": api.get_citizen_knowledge,
                "history": api.get_citizen_history,
            }
            method = methods.get(section)
            if method is None:
                raise ApiError(404, "route_not_found", "Citizen dossier section was not found.")
            if section == "history":
                limit = self._int_arg(query.get("limit", [None])[0], "limit", 100, 1, 500)
                return method(citizen_id, limit=limit)
            result = method(citizen_id)
            if isinstance(result, dict) and result.get("error"):
                raise ApiError(404, "citizen_not_found", result["error"])
            return result
        if path == "/economy/overview":
            return api.get_economy_overview()
        if path == "/economy/households":
            return api.connector.get_household_finances()
        if path == "/economy/jobs":
            return api.connector.get_job_market_telemetry()
        if path == "/society/overview":
            return api.get_society_overview()
        if path == "/justice/overview":
            return api.get_justice_overview()
        if path == "/climate/status":
            result = api.get_climate_status()
            result["data_quality"] = {"weather_available": self.engine.context.get_service("micro_climate_engine") is not None}
            return result
        if path == "/content/packs":
            return api.get_content_packs()
        if path.startswith("/content/settings/"):
            name = unquote(path[len("/content/settings/"):])
            if not name or "/" in name or "\\" in name:
                raise ApiError(400, "invalid_manifest", "Manifest name is invalid.")
            return api.inspect_settings_manifest(name)
        if path == "/events":
            limit = self._int_arg(query.get("limit", [None])[0], "limit", 100, 1, 500)
            since = query.get("since_timestamp", [None])[0]
            try:
                since_timestamp = float(since) if since is not None else 0.0
            except ValueError:
                raise ApiError(400, "invalid_argument", "since_timestamp must be numeric.")
            if not math.isfinite(since_timestamp):
                raise ApiError(400, "invalid_argument", "since_timestamp must be finite.")
            return api.get_event_stream(since_timestamp=since_timestamp, limit=limit)
        if path == "/diagnostics/performance":
            return api.get_subsystem_performance()
        if path == "/diagnostics/integrity":
            return api.get_integrity_audit()
        raise ApiError(404, "route_not_found", "API route was not found.")

    def _dispatch_post(self, path: str, body: dict):
        api = self.api
        if path == "/simulation/pause":
            return api.pause()
        if path == "/simulation/start":
            return api.resume()
        if path == "/simulation/step":
            ticks = self._int_arg(body.get("ticks"), "ticks", 1, 1, MAX_TICKS)
            return api.step(ticks)
        if path == "/simulation/fast-forward":
            ticks = self._int_arg(body.get("ticks"), "ticks", 60, 1, MAX_TICKS)
            max_leap = self._int_arg(body.get("max_leap"), "max_leap", 60, 1, 1000)
            return api.fast_forward(ticks, max_leap)
        if path == "/simulation/reset":
            seed = body.get("seed", 42)
            if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
                raise ApiError(400, "invalid_argument", "seed must be an integer or null.")
            if seed is not None and not -(2**31) <= seed < 2**31:
                raise ApiError(400, "out_of_range", "seed is outside the supported 32-bit range.")
            scenario = body.get("scenario_filename", "oakwood_baseline.json")
            if not isinstance(scenario, str) or Path(scenario).name != scenario or not scenario.endswith(".json"):
                raise ApiError(400, "invalid_scenario", "scenario_filename must be a JSON filename.")
            return api.reset(seed=seed, scenario_filename=scenario)
        raise ApiError(404, "route_not_found", "API route was not found.")

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/v1/"):
            return super().do_GET()
        try:
            query = parse_qs(parsed.query)
            with self.state_lock:
                result = self._dispatch_get(parsed.path[len("/api/v1"):], query)
            self._send_json(200, success_payload(result))
        except ApiError as exc:
            self._send_error(exc.status, exc.code, exc.message)
        except Exception as exc:
            self._send_error(500, "internal_error", f"{type(exc).__name__}: {exc}")

    def do_POST(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/v1/"):
            self._send_error(404, "route_not_found", "Only API POST routes are supported.")
            return
        origin = self.headers.get("Origin")
        allowed = {f"http://127.0.0.1:{self.server.server_port}",
                   f"http://localhost:{self.server.server_port}"}
        if origin and origin not in allowed:
            self._send_error(403, "origin_not_allowed", "Mutating requests are only accepted from this local UI origin.")
            return
        try:
            body = self._read_json()
            with self.state_lock:
                result = self._dispatch_post(parsed.path[len("/api/v1"):], body)
            self._send_json(200, success_payload(result))
        except ApiError as exc:
            self._send_error(exc.status, exc.code, exc.message)
        except Exception as exc:
            self._send_error(500, "internal_error", f"{type(exc).__name__}: {exc}")

    def do_OPTIONS(self):
        self._send_error(405, "method_not_allowed", "CORS preflight is not needed for the same-origin local UI.")


def main():
    parser = argparse.ArgumentParser(description="Run Oakwood Simulation Studio with its Python API adapter.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback only).")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scenario", default="oakwood_baseline.json")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        parser.error("The adapter is loopback-only. Use 127.0.0.1, localhost or ::1.")

    engine = SimulationEngine(get_default_data_dir())
    engine.initialize(seed=args.seed, scenario_filename=args.scenario)
    api = engine.get_visual_api()
    handler = type("ConfiguredOakwoodHandler", (OakwoodHandler,), {
        "api": api, "engine": engine, "state_lock": threading.RLock()
    })
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Oakwood Simulation Studio: http://{args.host}:{args.port}")
    print(f"Python API: http://{args.host}:{args.port}/api/v1")
    print("Simulation initialized from the selected scenario. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Oakwood local server…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
