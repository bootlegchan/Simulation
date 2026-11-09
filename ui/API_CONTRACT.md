# Oakwood UI — backend connection contract

This UI is a standalone frontend. It does not modify or embed the simulation engine. All routes below are **proposed UI-facing endpoints**, not claims about routes already implemented in the Python repository. They should be implemented in a separate adapter/API layer around `SimulationEngine`.

## Conventions
- Prefix: `/api/v1`
- JSON responses; stable IDs from the engine/data files.
- Include `request_id`, `generated_at`, and `simulation_tick` where relevant.
- Paginate large collections with `limit`, `cursor`, and `next_cursor`.
- Return structured errors: `{ "error": { "code", "message", "details" } }`.
- Read endpoints must not mutate simulation state.
- Mutations must validate lifecycle state and return the resulting state.
- Use Server-Sent Events or WebSocket for live updates; do not poll high-volume event history.

## Runtime and scenario
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/health` | API and engine readiness | Adapter health |
| GET | `/simulation/status` | Lifecycle, tick, virtual time, seed, scenario | `engine.lifecycle_state`, `engine.clock` |
| POST | `/simulation/initialize` | Initialize selected scenario/seed/stochastic mode | `engine.initialize()` |
| POST | `/simulation/start` | Resume simulation | `engine.start()` |
| POST | `/simulation/pause` | Pause simulation | `engine.pause()` |
| POST | `/simulation/step` | Advance exact tick count | `engine.tick(count)` |
| POST | `/simulation/fast-forward` | Adaptive advance with max leap | `engine.fast_forward(total_ticks,max_leap)` |
| GET | `/scenarios` | Available scenario IDs and metadata | Content loader/data directory |
| GET | `/simulation/config` | Tick rate, active settings and run configuration | Clock/settings/context |

## World and population
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/settlements` | Settlement summaries | `engine.settlements` |
| GET | `/settlements/{id}` | Buildings, rooms, room links and owners | Settlement model |
| GET | `/npcs` | Searchable, paginated citizen list | `engine.npcs` |
| GET | `/npcs/{id}` | Full NPC profile, needs, feelings, personality, cognition, household and relations | NPC model + context services |
| GET | `/objects` | Interactive objects and containment | `engine.objects` |
| GET | `/items` | Item definitions and categories | `engine.item_definitions` |
| GET | `/world/summary` | Entity counts, settlement counts, room counts and object counts | `engine.context` |

## Economy
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/economy/summary` | Currency, treasury, Gini, production and consumption totals | Macro tracker + treasury + supply chain |
| GET | `/economy/commodities` | Stocks, prices, production and demand | Supply-chain engine |
| GET | `/economy/households` | Household membership, balances and flows | Household economy engine |
| GET | `/economy/labour` | Jobs, shifts, requisitions and employment | Job posting + labour demand engines |
| GET | `/economy/taxation` | Tax rules, receipts and treasury history | Municipal tax engine + treasury |
| GET | `/economy/history?metric={id}` | Timestamped economic series | Telemetry recorder |

## Society and governance
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/society/relationships` | Relationships, romance stages and commitments | Romance + commitment services |
| GET | `/society/grudges` | Active grudges and history | Memory grudge engine |
| GET | `/society/factions` | Factions, members, platforms, grievance and strike state | Faction political engine |
| GET | `/society/decrees` | Active and historical decrees | Municipal decree engine |
| GET | `/society/clubs` | Clubs, memberships and gatherings | Social club engine |
| GET | `/society/fraternal-aid` | Lodges, dues, claims and relief history | Fraternal aid engine |
| GET | `/society/justice` | Lawsuits, crime reports and case status | Courtroom + justice subsystem |
| GET | `/society/information` | Notices, gossip, rumours, waves and knowledge diffusion | Unified information engine |
| GET | `/society/life-goals` | Active goals and completed milestones | Life goal engine |
| GET | `/society/recreation` | Games, contests and wager history | Recreation game engine |

## Systems and content
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/systems` | Registered services and subsystem pipeline | Context service registry + pipeline manager |
| GET | `/systems/events` | Recent domain events | EventBus history |
| GET | `/content/packs` | Pack manifests, dependencies and mount status | ContentLoader.loaded_packs |
| POST | `/content/packs/{id}/mount` | Mount pack and report validation | `engine.mount_pack(id)` |
| GET | `/content/validation` | Validation status and diagnostics | Content validator |
| POST | `/content/reload` | Trigger safe content reload | PackHotReloader / loader |

## Diagnostics and live updates
| Method | Route | Purpose | Engine mapping |
|---|---|---|---|
| GET | `/telemetry/latest` | Latest validated live snapshot | LiveTelemetryEngine |
| GET | `/telemetry/series/{metric}` | Metric time series | LiveTelemetryEngine |
| GET | `/telemetry/events` | Recent UI activity feed | Event bus / telemetry |
| GET | `/reports/latest` | Deep simulation dossier | DeepSimulationReporter |
| POST | `/diagnostics/integrity` | Determinism, seed divergence, entropy and coverage tests | SimulationIntegrityAuditor |
| GET | `/diagnostics/runtime` | Tick throughput, stage timings, errors and memory | Runtime instrumentation |
| GET | `/stream/events` | SSE or WebSocket event stream | EventBus adapter |

## Actions not exposed by the current UI
The first UI release is read-mostly apart from simulation lifecycle controls and pack mounting. Do not expose arbitrary NPC edits, decree enactment, relationship manipulation, inventory edits or economy overrides until the backend defines safe command methods, validation, permissions and audit events.

## Important implementation notes
1. `src/api/local_interface.py` currently contains placeholder return values and an empty `LocalVisualAPI`; it is not an HTTP server.
2. The UI must not call Python engine methods directly from the browser. Add a thin API adapter in a separate backend change, or use a local desktop bridge.
3. Telemetry and integrity modules contain placeholder/default values in the current source. Validate and populate them from the initialized engine before presenting them as live.
4. The frontend should treat absent optional subsystems as `unavailable`, not as empty/zero, so missing instrumentation is distinguishable from a real zero count.
5. Provide a capability manifest (e.g. `GET /api/v1/capabilities`) so the UI can hide or disable screens/actions unsupported by a given engine build.
