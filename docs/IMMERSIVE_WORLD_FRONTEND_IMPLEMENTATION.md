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

## Procedural world composition and lighting foundation

The environment is moving away from a single pre-painted village background. The renderer now treats the environment as separate world layers and manifest-driven objects.

- The outdoor background SVG is no longer used as the active scene plate. The sky, distant ridge and ground are rendered by the engine.
- Building instances are separate nodes created from each room's `buildings` manifest array. Their IDs, positions, footprints, palette and style are data-driven; moving a building no longer requires editing a background image.
- Buildings create independent light-occluder polygons for 2D shadows.
- The new WorldLighting node uses CanvasModulate for time-of-day ambient grading and PointLight2D sources for practical lights. Light positions and colours are configured through each room's `lights` array.
- Weather is intended as a separate camera-space overlay driven by climate data, so precipitation does not need to be painted into scenery.
- The outdoor manifest now has an explicit `scenery` array, rendered as independent prop nodes. Trees, rocks, bushes and lamps can be repositioned or regenerated without editing a background image. The first entries are a proof of composition structure, not a complete procedural settlement generator.
- Interior furniture groups are also separate manifest-driven nodes, rather than being hard-coded into the room background drawing routine.
- Building configuration is only reapplied when its data changes, avoiding needless redraw and shadow-occluder reconstruction on every simulation frame.
- The engine remains authoritative for simulation state. Presentation manifests only define visual style and scene composition.

### Height-aware 2D rendering direction

A future height-map pass should use a per-object height texture or polygon-derived height profile, not a single global height map. The map should encode relative elevation for roofs, walls, eaves, props and character parts. A shader can derive a pseudo-normal from neighbouring height samples and use it with 2D light direction for directional shading, while LightOccluder2D handles cast shadows. Height and occlusion are separate concepts: the height map shades surfaces; occluders determine which light rays are blocked. Keep this optional per material so flat objects remain inexpensive.

 
## Three-quarter camera and player-follow movement

The world camera is configured for an elevated three-quarter adventure presentation rather than a fixed side-on or strict isometric view.

- The observer is framed slightly left of centre to reveal more of the world ahead.
- A soft horizontal dead zone allows small movements without constant camera correction.
- Directional look-ahead eases toward the direction of travel, then recentres when the observer stops.
- Exponential delta-time smoothing keeps camera movement consistent across frame rates.
- Camera framing and follow response can be overridden per room through an optional camera object in the room presentation manifest: screen_anchor, follow_speed, look_ahead_distance, look_ahead_response, dead_zone_left and dead_zone_right.
- Room changes snap to the new room's spawn framing rather than making the camera sweep across unrelated world coordinates.
- Existing distant-landform parallax continues to move more slowly than the foreground as the camera travels.

This is a horizontal follow foundation. Vertical tracking, camera rails, room-specific cinematic pans and zoom transitions can be layered in later without coupling camera behaviour to simulation logic.


## Interactive world feedback and character presentation

The interaction layer now provides a lightweight hover/selection affordance: a ground-contact ring and restrained name plate follow the current point of interest. It reuses existing target-picking and selection data, so no new backend commands or simulation state are introduced.

NPC presentation slots are stable between redraws instead of drifting with a decorative sine wave. NPC rigs default to an idle gait; the observer's walk animation is explicitly driven by actual player movement. This avoids showing every citizen as if they were constantly walking. When authoritative NPC navigation/activity fields become available, the same motion hook can be connected to them.

Building silhouettes retain their shared procedural base but now have distinct visual signatures for civic, shop, bakery and tavern styles. Scenery trees and bushes receive subtle wind motion through their independent Node2D transforms.

These are presentation-only improvements. Python remains authoritative for simulation state and the frontend does not fabricate NPC activity or player actions.

## Cinematic room transitions and camera focus

Room travel now uses a short, full-screen dark fade so the scene and camera can change without exposing a hard cut.

- Clicking an entrance moves the observer toward the portal's explicit door_x anchor. The portal remains the destination trigger when the observer reaches it.
- The camera gently tightens its framing while a portal is selected, creating a subtle approach shot.
- Entering or exiting a room fades the current scene down, changes the room presentation and spawn position, requests the authoritative room snapshot, then fades back up.
- The transition waits for an in-flight HTTP request to finish before requesting the new room snapshot. Failed or malformed requests also release the fade instead of leaving the screen covered.
- Camera zoom, framing, follow response, portal focus and fade durations are room-manifest settings. Interiors use a slightly tighter zoom and slower reveal than the outdoor square.
- Camera and transition code remain in Godot. No simulation rules or Python API behaviour is changed.
