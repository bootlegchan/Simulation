# Immersive World Frontend — Implementation Notes

## Repository baseline

This branch is based directly on main commit 76d66dd4e02bb9994edef0aa81deaee34b86c22b. The repository release commit refers to v169 while README and LocalVisualAPI currently report v168 and v168.1-live respectively. Use the exact commit and runtime API capability response as the compatibility baseline rather than assuming version labels are aligned.

An existing open pull request (#2, frontend/oakwood-ui-v169) contains a conventional browser dashboard and a local Python adapter. This branch does not depend on or merge that dashboard. The immersive frontend is a separate Godot client under frontend/.

## Runtime boundary

- Python SimulationEngine owns NPC decisions, room locations, virtual time, climate, economy, production, relationships and events.
- frontend_bridge/server.py owns loopback HTTP transport, request validation, DTO serialization and snapshot assembly.
- Godot owns camera, observer navigation, scene presentation, animation and contextual inspection.
- The observer is presentation-only. Walking through a portal changes the viewed room, not an NPC or backend location.
- No purchase, conversation, hiring, construction or object mutation is exposed because no corresponding player-command contract has been verified.

## Initial transport

Base URL: http://127.0.0.1:8765/api/v1

- GET /health
- GET /snapshot?room_id=room_village_square
- GET /rooms/{room_id}
- GET /citizens/{npc_id}/profile
- GET /simulation/status
- POST /simulation/pause
- POST /simulation/resume
- POST /simulation/step
- POST /simulation/fast-forward

Snapshot schema version 1.0 contains status, climate and data-quality metadata, economy summary, settlement hierarchy, room connections, alive citizen summaries, object DTOs, active-room details and population counts. It is assembled under one engine lock.

The current event API uses timestamps rather than a stable sequence cursor. The first frontend does not yet consume events; periodic batched snapshots are used until a cursor contract is added.

## World presentation

The first authored manifest maps Oakwood public square, Town Hall, general shop, bakery and tavern. It maps the existing square noticeboard and selected interior object anchors. The market-plaza room is intentionally presented as an outdoor scene despite being nested beneath Town Hall in the simulation hierarchy.

The first renderer uses original procedural illustration as a stand-in for final hand-painted environment art. It establishes world scale, perspective, interaction anchors, camera movement and environmental presentation without introducing proprietary reference-game assets.

## Known limitations and next work

1. Replace procedural scenery and placeholder actor silhouettes with an original illustrated asset pack and reusable character rigs.
2. Add real per-room navigation polygons and pathfinding for the observer; current movement uses a simple horizontal presentation plane.
3. Author scene-specific parallax plates, foreground occlusion and polished transitions.
4. Improve NPC screen-space position mapping; current actor positions are deterministic presentation slots within their authoritative room.
5. Add object-specific detail DTOs where the current facade does not return sufficient data.
6. Add a stable event sequence/cursor to the adapter if event-driven updates are required.
7. Add supported player commands only after matching authoritative backend service methods and tests.
8. Add Godot headless import/scene tests and run the Python adapter plus existing backend regression suites on a local checkout.

No simulation engine rules or simulation data manifests are modified by this implementation.

## Modular randomized character presentation

The original fixed-shape NPC drawing routine has been replaced by an assembled character rig. It is deliberately a presentation system, not a second source of simulation identity or attributes.

- `frontend/scripts/characters/character_visual.gd` assembles one visual actor from independent child parts.
- `frontend/scripts/characters/character_part.gd` implements the replaceable shadow, legs, body, head, hair, face and accessory layers.
- Each actor is keyed by the authoritative NPC ID. Its generated appearance is deterministic for that ID, so a character does not change appearance on every snapshot or redraw.
- Appearance can be supplied as an optional `appearance` dictionary on an NPC DTO. Recognized visual keys override generated defaults; the current summary DTO does not yet expose this field, so stable ID-based variation is used without changing backend simulation data.
- Components can be swapped, hidden, extended or replaced independently. New hairstyles, body silhouettes, clothing layers, age cues, professions and animation sets should be added as data/components rather than new one-off NPC drawing functions.
- The observer uses the same rig and component pipeline.
- The rig currently provides lightweight idle/walk motion and a stylized base art direction. It is a modular foundation, not a final character asset library.

No fixed character cast, role-to-appearance mapping, or random appearance reroll per frame is introduced. Appearance randomness is seeded from entity identity and does not alter the simulation.
