# Oakwood visual client

A 2D storybook village client for the Python simulation engine.

## Technology

- Phaser 3 renders the 2D village, camera, scenery, characters and pointer interactions.
- React renders responsive menus, resident/building inspectors, stories and simulation controls.
- Vite serves the development app and produces the production bundle.
- FastAPI remains authoritative for simulation state and mutations.

The frontend deliberately does not reimplement simulation rules.

## Run locally

Terminal 1 — from the repository root:

```bash
python -m pip install -r requirements.txt
python -m src.api.server
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite server proxies `/api` to `http://127.0.0.1:8000`.

Set `VITE_API_URL` if the API is hosted elsewhere.

## API integration

- `GET /api/v1/simulation/status`
- `GET /api/v1/npcs`
- `GET /api/v1/objects`
- `GET /api/v1/events/history`
- `POST /api/v1/simulation/control`
- `POST /api/v1/mutate/npc/{npc_id}/action`
- `WS /api/v1/ws/bridge`

WebSocket snapshots and subsequent tick batches are both consumed. The client reconnects with bounded exponential backoff.

## Interaction

- Drag the world or use the mouse wheel / arrow keys to scroll the village.
- Click a resident to inspect needs, mood, wealth and location.
- Click a landmark building to open its information panel.
- Use the simulation controls to start, resume, pause and step the backend.

The art is rendered with Phaser vector primitives and does not require third-party image assets. It is original cosy-life-simulation art direction, not a reproduction of Animal Crossing characters or assets.

## Production build

```bash
npm run build
```
