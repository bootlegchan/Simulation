# Oakwood Simulation Studio UI

A standalone, browser-based operations and inspection interface for the Oakwood simulation.

## Run

Serve this directory with a static file server:

```bash
python -m http.server 4173 --directory ui
```

Open `http://localhost:4173`.

The frontend is plain HTML, CSS and JavaScript. It has no build step and no third-party runtime dependency. Styling uses native system fonts.

## API connection

The frontend expects a browser-facing JSON API at:

```
http://127.0.0.1:8765/api/v1
```

Override the base URL before `app.js` loads by setting `window.OAKWOOD_API_BASE` in `index.html` or in a small local configuration script.

**Important:** the current Python repository exposes `SimulationConnector` and `LocalVisualAPI` as in-process Python classes. It does not currently expose the HTTP routes called by this browser application. The UI will therefore show a clear disconnected state until a separate adapter is supplied. It does not display fabricated demo data.

See [API_CONNECTION_GAPS.md](./API_CONNECTION_GAPS.md) for the verified method-to-screen mapping and remaining work.

## Scope

- UI only: application shell, navigation, dashboard, data tables, inspectors, controls and diagnostics panels.
- No game-world renderer, map, 2D/3D scene, character art, animation or scenery.
- No changes to simulation behaviour, world content, engine services or backend files.
- All displayed simulation values must originate from the connected API.
- Missing data is shown as unavailable, not as zero or sample content.

## Browser security

The adapter should bind to loopback by default, validate request origins, and restrict mutation routes to explicit local operator actions. Do not expose arbitrary Python execution or direct object mutation to the browser.