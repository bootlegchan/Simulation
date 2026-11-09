# Oakwood UI

Standalone application UI for the current Python simulation repository.

## Run
Serve this directory with any static file server, for example:

```bash
python -m http.server 4173 --directory ui
```

Open `http://localhost:4173`.

No build step or third-party runtime dependency is required. The Google font falls back to system sans-serif if offline.

## Scope
- UI only: dashboard, citizen directory, settlement structure, economy, society, engine systems, content packs and diagnostics.
- No world renderer, map, character art, 2D/3D scene or visual game development.
- The current page uses a small, clearly labelled preview data set. It does not pretend to be live-connected.
- Proposed endpoints and missing backend connections are documented in `API_CONTRACT.md`.

## Integration
Implement the routes in `API_CONTRACT.md` in a separate backend adapter. Then replace the preview data provider in `app.js` with fetch calls to that API. Keep engine internals out of the browser.
