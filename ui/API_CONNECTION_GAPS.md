# Oakwood UI — verified API connection gaps

**Repository inspected:** `bootlegchan/Simulation`, branch `main`, commit `76d66dd4e02bb9994edef0aa81deaee34b86c22b` (9 November 2026).

**Scope:** UI integration only. This document does not authorise or include backend changes. Route names are proposed browser-facing routes, not routes currently served by the repository.

## 1. Current state

The repository contains:

- `src/api/local_interface.py`: `SimulationConnector` and `LocalVisualAPI`.
- `SimulationEngine.get_connector()` and `SimulationEngine.get_visual_api()` factory methods.
- A real in-process `EventBus` with bounded history and event query methods.
- A subsystem pipeline profiler.
- Standalone telemetry and deep-report classes.
- Test coverage in `tests/unit/test_92_data_layer_connector_telemetry_and_explainability.py` for the connector, event bus, world inspection, citizen dossier, controls and content inspection.

There is **no HTTP server, REST router, WebSocket server or Server-Sent Events endpoint** in the inspected repository. The browser cannot call the Python facade directly. A separate adapter/transport is the first integration dependency.

## 2. Existing facade methods

| UI area | Existing Python method(s) | What is already available |
|---|---|---|
| API discovery | `LocalVisualAPI.get_api_capabilities()` | API/engine version labels, supported areas, registered service names and subsystem count |
| Runtime | `get_simulation_status()`, `step()`, `fast_forward()`, `pause()`, `resume()`, `reset()` | Lifecycle, tick, virtual time, weather summary and basic controls |
| Scenarios | `list_scenarios()`, `inspect_scenario()` | Scenario file discovery and manifest inspection |
| Checkpoints | `create_checkpoint()`, `restore_checkpoint()` | In-memory partial snapshot only; not a complete save system |
| World structure | `get_world_hierarchy()`, `get_room_details()`, `get_spatial_connections()`, `verify_world_integrity()` | Settlement/building/room hierarchy, room occupants/objects/connections and graph integrity |
| Citizens | `list_citizens()`, `get_citizen_profile()`, `get_citizen_state()`, `get_citizen_decision_explanation()`, `get_citizen_relationships()`, `get_citizen_knowledge()`, `get_citizen_history()` | Citizen directory, traits, current state, utility/drive explanation, relationships, memory traces and biography |
| Economy | `get_economy_overview()`; connector stock/price/household/job telemetry methods | Total currency, Gini, treasury, commodity stocks/prices and household count; extra connector data is not all exposed by the facade |
| Society | `get_society_overview()`, connector methods | Factions, active grudges, domestic spats and municipal decrees |
| Justice | `get_justice_overview()` | Pending/resolved lawsuits and citizens on probation |
| Environment | `get_climate_status()` | Current climate snapshot |
| Content | `get_content_packs()`, `inspect_settings_manifest()`, `preview_merge_patch()` | Pack manifest list, one settings manifest by name and a placeholder merge preview |
| Events | `get_event_stream()`, `query_events()` | In-process bounded event history and filters |
| Diagnostics | `get_subsystem_performance()`, `get_integrity_audit()`, `verify_world_integrity()` | Pipeline timings/call counts/errors and integrity-audit output |

## 3. Required browser-facing transport

Create a separate adapter around `SimulationEngine.get_visual_api()`. The adapter should:

1. Bind to `127.0.0.1` by default; do not expose the simulation to a network by default.
2. Provide `GET /api/v1/health` and `GET /api/v1/capabilities`.
3. Expose read routes for the existing facade methods listed above.
4. Expose explicit command routes for pause, resume, step, fast-forward and reset, with input bounds and lifecycle checks.
5. Return JSON only, with structured errors and clear unavailable/not-initialised states.
6. Keep Python objects and engine internals inside the process; serialize DTOs only.
7. Add origin/CSRF protection for mutating requests if the browser and adapter use different origins.
8. Publish a capability document so the UI can disable screens or actions unsupported by a given engine build.

Suggested initial route mapping:

| Browser route | Existing facade mapping |
|---|---|
| `GET /api/v1/simulation/status` | `get_simulation_status()` |
| `POST /api/v1/simulation/step` | `step(ticks)` |
| `POST /api/v1/simulation/fast-forward` | `fast_forward(ticks, max_leap)` |
| `POST /api/v1/simulation/pause` | `pause()` |
| `POST /api/v1/simulation/start` | `resume()` |
| `POST /api/v1/simulation/reset` | `reset(seed, scenario_filename)` |
| `GET /api/v1/scenarios` | `list_scenarios()` |
| `GET /api/v1/world/hierarchy` | `get_world_hierarchy()` |
| `GET /api/v1/rooms/{id}` | `get_room_details(id)` |
| `GET /api/v1/citizens` | `list_citizens(filter_role, alive_only)` |
| `GET /api/v1/citizens/{id}/profile` | `get_citizen_profile(id)` |
| `GET /api/v1/citizens/{id}/state` | `get_citizen_state(id)` |
| `GET /api/v1/citizens/{id}/decision` | `get_citizen_decision_explanation(id)` |
| `GET /api/v1/citizens/{id}/relationships` | `get_citizen_relationships(id)` |
| `GET /api/v1/citizens/{id}/knowledge` | `get_citizen_knowledge(id)` |
| `GET /api/v1/citizens/{id}/history` | `get_citizen_history(id, limit)` |
| `GET /api/v1/economy/overview` | `get_economy_overview()` |
| `GET /api/v1/society/overview` | `get_society_overview()` |
| `GET /api/v1/justice/overview` | `get_justice_overview()` |
| `GET /api/v1/climate/status` | `get_climate_status()` |
| `GET /api/v1/content/packs` | `get_content_packs()` |
| `GET /api/v1/content/settings/{name}` | `inspect_settings_manifest(name)` |
| `GET /api/v1/events` | `get_event_stream(since_timestamp, limit)` or `query_events(...)` |
| `GET /api/v1/diagnostics/performance` | `get_subsystem_performance()` |
| `GET /api/v1/diagnostics/integrity` | `get_integrity_audit()` |

## 4. Missing or incomplete connections

### P0 — required before the UI can become live

- **HTTP transport and process lifecycle:** no browser-callable server/router; no health endpoint; no request/response contract.
- **Capability and version consistency:** the facade reports `v168.1-live` / `v168`, while the latest repository commit is labelled v169 in its release message. The README also still says v168. The UI must display returned metadata, not infer a version from the commit title.
- **Population count in status:** `get_simulation_status()` does not return population; the dashboard must obtain it from the citizen directory or a dedicated summary.
- **Telemetry history:** `LiveTelemetryEngine` is a separate class and is not registered or called by `SimulationEngine`; `LocalVisualAPI` has no latest-snapshot or metric-series methods.
- **Actual report integration:** `DeepSimulationReporter` is separate from the UI facade and has no report endpoint.

### P1 — needed for complete application screens

- **Citizen directory usability:** `list_citizens()` only supports role filtering and alive/deceased inclusion; it has no server-side search, sorting, pagination or stable cursor.
- **World directories:** there is a nested hierarchy and room detail method, but no dedicated settlement, building, room, object or item directory endpoints; no object/item detail endpoints.
- **Economy depth:** the facade only exposes a high-level overview. Household finance and job-market telemetry exist on `SimulationConnector` but are not surfaced through `LocalVisualAPI`. No transaction ledger, production/consumption history, tax receipts, shortage history or time series.
- **Society depth:** `get_society_overview()` returns factions, grudges, domestic spats and decrees. Clubs, aid lodges, information networks, life goals, recreation and commitments are not exposed by this overview.
- **Justice depth:** active/resolved lawsuits and probation are exposed, but no crime incident history or full case detail query.
- **Environment depth:** current climate only; no climate history, environmental exposure series, health incidents or mortality history.
- **Content validation:** pack listing and settings inspection are read-only. There are no facade methods for pack validation, dependency graph, unmount, load history, schema discovery or export.
- **Merge preview:** `preview_merge_patch()` currently returns `valid: true` with a generic message; it does not demonstrate a real schema validation or applied merge result. The UI labels it unavailable rather than treating it as validation.
- **Event timeline:** the facade exposes stream and filtered event query methods, but no dedicated event-type catalogue, stable event cursor, reconnect/replay contract or browser stream. Entity timeline is not separately exposed by the facade.
- **Diagnostics:** pipeline timings and integrity output exist, but there are no health/uptime, structured log, memory, queue or service health endpoints.

### P2 — actions that should remain unavailable

- **Checkpoint safety:** checkpoint storage is in-memory and the snapshot covers only selected NPC fields plus treasury. Restore does not restore the complete world context or stateful services. Do not present it as full save/load or replay.
- **Content mutation:** engine has `mount_pack()`, but the facade does not expose a validated mount/unmount workflow. Keep pack operations read-only in the UI.
- **Operator edits:** no safe command layer for arbitrary citizen edits, decrees, inventory, relationships or economic overrides. Do not expose direct object mutation.
- **Live streaming:** the event bus supports in-process subscriptions/history, not SSE/WebSocket transport. Polling can be used only after a bounded adapter endpoint exists; a reconnect cursor and retention metadata are still needed.

## 5. Data correctness safeguards

- Several facade methods return empty collections when a service is absent. The adapter should distinguish an absent service from a genuine empty result.
- Climate/status methods use fallback defaults when weather data is absent. The adapter should include an availability/source flag so defaults are not presented as observed conditions.
- Citizen decision explanation invokes cognition evaluation methods. Verify that these reads do not alter meaningful simulation state before exposing them as ordinary GET requests.
- Event history is bounded in memory. Expose retention metadata and do not imply that old events are complete.
- The integrity auditor and report modules must be validated against actual simulation runs before their output is described as authoritative.
- Do not display missing values as zero. Use an em dash and an explicit unavailable label.

## 6. Validation status

The source and test files were reviewed on the current `main` branch. A full test run was **not executed in this environment** because the GitHub repository could not be cloned into the execution container (network DNS resolution failed). The repository's documented command is:

```bash
python3 run_tests.py --all
```

The dedicated test `tests/unit/test_92_data_layer_connector_telemetry_and_explainability.py` verifies the in-process facade and connector behaviours described above. It does not verify an HTTP adapter, browser transport or UI integration.

## 7. Explicit exclusions

- No 2D/3D world renderer, map, scene, character art, animation or scenery.
- No changes to simulation rules, NPC logic, economy systems, world data or backend code.
- No direct browser access to Python objects or local files.
- No fake population, economic, event or climate values.
- No save/load, mod editing or arbitrary operator mutation until the backend supplies safe, validated operations.