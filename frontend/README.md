# Oakwood — Immersive World Frontend

This is the first implementation slice of the illustrated, diegetic 2.5D frontend. It is a separate Godot client; the Python simulation remains authoritative.

## Run

1. Install the Python dependencies from the repository root (`python3 -m pip install -r requirements.txt`).
2. Open `frontend/project.godot` with Godot 4.4.1.
3. Run the project. Godot first checks for an existing local bridge; if none is running, it starts `frontend_bridge/server.py` automatically and connects to the live simulation.

For troubleshooting, the bridge can still be started manually from the repository root:

    python3 -m frontend_bridge.server --port 8765 --seed 42 --ticks-per-second 1

The bridge binds to loopback only. It exposes read-only world snapshots and explicit pause/resume/step/fast-forward controls. It does not expose arbitrary Python calls, NPC manipulation, purchases, production commands or simulation rule changes.

## Prototype features

- Oakwood square with original procedural illustrated environment.
- Side-scrolling camera and click-to-walk observer.
- Backend-driven NPCs, names, occupations, room occupancy and current actions.
- Clickable entrances to Town Hall, shop, bakery and tavern.
- Indoor room presentation and exits back to the square.
- Noticeboard, municipal ledger and shop stock inspection.
- Time-of-day and weather presentation driven by backend state.
- Contextual inspection sheet presented as an in-world paper object.
- Connection failure state; no fake simulation success.

The environment and characters are currently original procedural placeholder artwork. Replace them with commissioned or created art using the manifest anchors and scene pipeline; do not copy proprietary reference-game assets.

## Controls

- Left click ground: walk.
- Left click NPC/object/door: approach and select.
- E: inspect or enter selected doorway.
- Escape: close inspection.

## Data

data/presentation/oakwood.json maps backend room and object IDs to presentation scenes, anchors and portals. Backend IDs remain canonical. Unknown room mappings are not silently invented.

## Tests

From repository root:

    python -m unittest frontend_bridge.test_server
    python3 run_tests.py --all

The Godot project should also be imported with Godot 4.4.1. Automated headless scene validation should be added when the target Godot runtime is available in CI.
