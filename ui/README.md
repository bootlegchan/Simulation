# Oakwood Simulation Studio

A browser-based operations and inspection interface connected to the existing Python simulation through a local HTTP adapter.

## Run the complete application

From the repository root:

```bash
python ui/server.py
```

Then open **http://127.0.0.1:4173**.

The server initializes the real `SimulationEngine`, obtains its `LocalVisualAPI` facade, serves the HTML/CSS/JavaScript, and exposes the JSON endpoints under the same origin at `/api/v1`. No separate static server or manually configured API URL is needed.

Optional startup arguments:

```bash
python ui/server.py --port 4173 --seed 42 --scenario oakwood_baseline.json
```

The adapter binds to loopback only by default. It deliberately refuses non-loopback bind addresses. Use Ctrl+C to stop it.

## Architecture

- `ui/server.py` owns HTTP transport, route dispatch, request validation, safe JSON serialization and local-origin checks.
- `src/simulation/engine.py` remains the simulation runtime and lifecycle owner.
- `src/api/local_interface.py` remains the authoritative in-process facade and data connector.
- `ui/app.js` consumes the adapter's versioned JSON API.

The adapter does not duplicate simulation rules, reach into arbitrary Python objects from the browser, or require simulation developers to implement browser networking. It maps HTTP requests to existing facade methods.

## API

Base path: `/api/v1`

- `GET /health`, `GET /capabilities`
- `GET /simulation/status`
- `POST /simulation/start`, `POST /simulation/pause`
- `POST /simulation/step`, `POST /simulation/fast-forward`, `POST /simulation/reset`
- `GET /scenarios`, `GET /scenarios/{filename}`
- `GET /world/hierarchy`, `GET /world/connections`, `GET /world/integrity`, `GET /rooms/{room_id}`
- `GET /citizens`, `GET /citizens/{id}/{profile|state|relationships|decision|knowledge|history}`
- `GET /economy/overview`, `GET /economy/households`, `GET /economy/jobs`
- `GET /society/overview`, `GET /justice/overview`, `GET /climate/status`
- `GET /content/packs`, `GET /content/settings/{name}`
- `GET /events?limit=100&since_timestamp=0`
- `GET /diagnostics/performance`, `GET /diagnostics/integrity`

Successful requests return JSON data. Errors use `{"error":{"code":"...","message":"..."}}` and an appropriate HTTP status. Simulation-changing commands are explicit POST routes, with bounded input validation. Request bodies are limited to 16 KB and tick counts are capped.

## Current limitations

The adapter exposes existing facade functionality; it does not manufacture missing capabilities. The UI should continue to mark unsupported features unavailable. In particular, the current project does not yet provide durable full-world save/load, safe content mutation, historical telemetry series, or a browser event-stream transport. Climate methods currently have fallback values when their service is missing; the adapter reports service availability separately so the interface can avoid treating defaults as measured observations.

## Tests

Run the existing project suite:

```bash
python3 run_tests.py --all
```

Run adapter checks:

```bash
python -m unittest ui.test_server
```

No third-party web framework is required; the adapter uses Python's standard library.
