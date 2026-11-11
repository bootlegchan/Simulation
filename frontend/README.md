# Oakwood — Immersive World Frontend

This is the first implementation slice of the illustrated, diegetic 2.5D frontend. It is a separate Godot client; the Python simulation remains authoritative.

## Run

1. Make sure Python 3 is installed. The current simulation bridge uses the Python standard library and the repository's own modules; there is no `requirements.txt` in this repository.
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

## Visual style: storybook summer

The client is drawn in a hand-made, crayon-and-paper look inspired by the cheerful
summer-holiday feel of the 2024 Shin-chan Switch game: warm flat fills, thick brown
outlines with a slight wobble, rounded chunky shapes, and shadows that lean violet
instead of grey. All art is original and generated from code; no assets or characters
from that game are used.

- `scripts/style/storybook_style.gd` is the single source of the look: palette,
  wobbly outlines, outlined shapes, puffy lobes, blob shadows, clouds, sky and
  ambient colours. Change a colour or outline weight here to restyle everything.
- `shaders/storybook_paper.gdshader` is a full-screen paper-grain, warm-tint and
  vignette pass. It lives on its own `CanvasLayer` (layer 10) created in
  `world_view.gd`; delete that layer to turn the effect off.
- Renderers (`world_terrain`, `world_prop`, `world_building`, `world_furniture`,
  `world_interactable`, `world_foreground`, `world_atmosphere`, the character parts
  and the HUD) call the style module and keep their original geometry, anchors and
  light occluders, so manifest data and gameplay are unchanged.
- Characters use chibi proportions (large head over a short body); `HEAD_SCALE`
  and `BODY_SCALE` in `character_visual.gd` control this.

Cleanups made alongside the restyle: removed unused draw functions in
`world_view.gd` that called an undefined `_draw_ellipse`, and declared the missing
`WORLD_HEIGHT` constant in `world_atmosphere.gd`.
