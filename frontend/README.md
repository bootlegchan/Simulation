# Oakwood visual client

A 2D storybook village client for the Python simulation engine.

## Technology choice

- **Phaser 3** renders the interactive 2D village scene and clickable villagers.
- **React** renders the responsive menus, resident inspector, simulation controls and data panels.
- **Vite** provides the development server and production build.
- The existing **FastAPI** service remains authoritative for simulation state and mutations.

This hybrid keeps the visual world performant while making information-heavy panels straightforward to extend. The frontend does not duplicate simulation rules.

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

Open http://localhost:5173.

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`. For another API host, set `VITE_API_URL` before building.

## Current integration

- Initial state: `GET /api/v1/simulation/status`
- Residents and objects: `GET /api/v1/npcs`, `GET /api/v1/objects`
- Event feed: `GET /api/v1/events/history`
- Runner controls: `POST /api/v1/simulation/control`
- Resident actions: `POST /api/v1/mutate/npc/{npc_id}/action`
- Live channel: `WS /api/v1/ws/bridge`

The art is currently drawn with Phaser vector primitives, so the client runs without external image assets. It is an original cosy village presentation inspired by the warmth and readability of life-simulation games, not a reproduction of Animal Crossing artwork or characters.

## Build

```bash
npm run build
```
