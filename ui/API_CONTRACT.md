# Oakwood UI — expanded backend connection gap analysis

**Purpose:** define the full set of backend connections that would make the Oakwood UI genuinely useful as a simulation operations, inspection and analysis application.

**Scope boundary:** this is an API planning document only. It does not authorise changes to the simulation engine, simulation rules, content data or game visuals. Implement API access in a separate adapter/service layer. The UI must not import Python engine classes or mutate in-memory objects directly.

**Status key**
- **Required:** needed for the existing UI to display real data or safely operate the simulation.
- **Strongly recommended:** turns a static display into a useful inspection/management tool.
- **Advanced:** useful for deeper analysis, debugging, modding or future UI screens.
- **Not currently verified:** proposed route; confirm the corresponding source service and method before implementation.

The route names below are a recommended contract, not existing routes. The current repository has a local Python connector, not a complete HTTP API. Some diagnostics and connector methods currently return hard-coded placeholder values or empty collections; those must not be exposed as authoritative live data.

---

## 1. API foundation and service discovery

| Priority | Method and route | What the UI needs | Why it matters |
|---|---|---|---|
| Required | GET `/api/v1/health` | API process, engine process, readiness, version, uptime and last error | Distinguishes an unavailable server from a stopped simulation |
| Required | GET `/api/v1/capabilities` | Supported features, endpoints, optional services, read/write support and API version | Lets UI adapt to backend versions without assuming every subsystem exists |
| Required | GET `/api/v1/metadata` | Build/commit, schema versions, data directory identifier, active scenario and feature flags | Makes debugging and reproducibility possible |
| Required | GET `/api/v1/simulation/status` | Lifecycle state, tick, virtual time, paused state, scenario, seed and stochastic mode | Drives the global status bar and control availability |
| Strongly recommended | GET `/api/v1/diagnostics/services` | Service registry names, availability, initialization state and error state | Exposes missing optional services rather than disguising them as empty data |
| Strongly recommended | GET `/api/v1/diagnostics/pipeline` | Registered subsystems, tick stages, execution order, enabled state and last-run timing | Explains what the simulation actually ran on each tick |
| Strongly recommended | GET `/api/v1/diagnostics/logs` | Structured application logs with level, source, tick, timestamp and filters | Gives operators a way to diagnose initialization and runtime failures |
| Advanced | GET `/api/v1/diagnostics/configuration` | Effective configuration and origin of each value (default, scenario, pack, override) | Helps explain why a setting has its current value |

### API-wide response requirements
- Use stable entity IDs, not display names, as resource identifiers.
- Include `request_id`, `generated_at`, `engine_version` and `simulation_tick` where applicable.
- Return explicit `available`, `unavailable`, `not_initialized` or `error` states. Do not encode unavailable data as an empty list or zero.
- Standardise pagination (`limit`, `cursor`, `next_cursor`), filtering, sorting and search.
- Use UTC timestamps for real-world event timestamps and explicit ISO timestamps for simulation virtual time.
- Return units and definitions for every metric (gold, items, ticks, minutes, percentages, etc.).
- Use structured errors: `{ "error": { "code": "...", "message": "...", "details": {}, "request_id": "..." } }`.
- Include a schema version for complex nested response objects.
- Enforce request limits and timeouts. Large reports and integrity runs should be asynchronous jobs.
- Add authentication/authorisation if the API is reachable beyond the local machine. Bind a local-only default to loopback; protect mutating commands with CSRF/origin controls and an audit log.

---

## 2. Simulation lifecycle and time controls

| Priority | Method and route | Data/action |
|---|---|---|
| Required | GET `/simulation/status` | Current lifecycle state, tick, virtual date/time, ticks per minute, pause state, scenario and seed |
| Required | POST `/simulation/initialize` | Initialise from scenario ID, seed and stochastic setting; return validation and initialization report |
| Required | POST `/simulation/start` | Resume execution |
| Required | POST `/simulation/pause` | Pause safely at a tick boundary |
| Required | POST `/simulation/step` | Advance an exact number of ticks; return starting/ending tick and elapsed wall time |
| Required | POST `/simulation/fast-forward` | Advance to target tick or duration with explicit maximum leap and progress |
| Strongly recommended | POST `/simulation/stop` | Stop cleanly and report whether current tick completed |
| Strongly recommended | POST `/simulation/reset` | Reset to a known initial state; require explicit confirmation and report data loss |
| Strongly recommended | PATCH `/simulation/settings` | Change only documented runtime-safe settings; report settings that require reinitialisation |
| Strongly recommended | GET `/simulation/progress/{job_id}` | Poll a long-running initialize/fast-forward/report task |
| Advanced | POST `/simulation/speed` | Set wall-clock pacing or ticks-per-second target, separately from virtual time |
| Advanced | GET `/simulation/checkpoints` | List saved checkpoints and their tick, scenario, seed and version |

**Important engine check:** the current source clearly shows `start()`, `pause()`, `tick(count)` and `initialize(...)`. Confirm the exact `fast_forward`, stop, reset, persistence and pacing methods before binding those routes. Do not invent calls in the adapter.

Useful UI behaviour:
- Show virtual simulation time separately from the computer's real time.
- Display current tick and ticks-per-second throughput.
- Disable incompatible controls while initialising, resetting or running a non-interruptible job.
- Show progress and allow cancellation only where the engine can safely cancel.
- Confirm destructive reset/restore actions and state exactly which state will be lost.

---

## 3. Scenarios, saves, checkpoints and reproducibility

| Priority | Method and route | Data/action |
|---|---|---|
| Required | GET `/scenarios` | Available scenario IDs, names, descriptions and compatibility |
| Required | GET `/scenarios/{id}` | Scenario manifest, starting date, content references and validation status |
| Strongly recommended | POST `/scenarios/{id}/validate` | Run content and reference validation without starting the simulation |
| Strongly recommended | GET `/simulation/run-configuration` | Effective seed, stochastic mode, scenario, loaded packs and settings snapshot |
| Strongly recommended | GET `/simulation/reproducibility` | Whether current run can be replayed; engine/data versions and random seed |
| Advanced | GET `/saves` | Saved run/checkpoint catalogue |
| Advanced | POST `/saves` | Save a checkpoint with label and metadata |
| Advanced | POST `/saves/{id}/restore` | Restore a checkpoint after compatibility validation |
| Advanced | GET `/saves/{id}` | Checkpoint details, source versions and tick |
| Advanced | DELETE `/saves/{id}` | Delete checkpoint with confirmation |
| Advanced | POST `/simulation/replay` | Replay a run from a seed/checkpoint and event/action log |

A save/restore API should not be promised until the engine has a reliable serialisation contract for the complete world context and all stateful services. A partial save can silently corrupt a run.

---

## 4. World, settlements and spatial structure

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/world/summary` | Counts of settlements, buildings, rooms, NPCs, objects, item definitions and active systems |
| Required | GET `/settlements` | Settlement list and high-level population/building counts |
| Required | GET `/settlements/{settlement_id}` | Full settlement metadata and building references |
| Required | GET `/buildings` | Searchable building directory |
| Required | GET `/buildings/{building_id}` | Building category, owner, rooms, condition and use |
| Required | GET `/rooms` | Searchable room directory with settlement/building filters |
| Required | GET `/rooms/{room_id}` | Room archetype, connections, occupants, objects and capacity if modelled |
| Strongly recommended | GET `/rooms/{room_id}/connections` | Connected rooms, door/portal properties and traversal weights |
| Strongly recommended | GET `/spatial/graph` | Node/edge summary and graph health; allow filtered neighbourhood queries rather than returning an unbounded graph |
| Strongly recommended | GET `/spatial/path` | Path query between two valid locations, returned as nodes/edges with route cost |
| Strongly recommended | GET `/spatial/occupancy` | Current occupants by room/building and occupancy history |
| Strongly recommended | GET `/objects` | Interactive object directory, current location and containment |
| Required | GET `/objects/{object_id}` | Object properties, state, container/location and affordances |
| Required | GET `/items` | Item definition catalogue and category filters |
| Required | GET `/items/{item_id}` | Item properties, value, tags and stack/container rules |
| Advanced | GET `/world/changes` | Buildings/rooms/objects created, removed or changed since a tick |
| Advanced | GET `/world/integrity` | Orphaned rooms, invalid links, missing owners, invalid containment and inaccessible locations |

This is a data/structure view only. It does not require a 2D map, 3D world, character rendering or other visual development.

---

## 5. Population and citizen profiles

The citizen directory should be a major part of the application. A list endpoint alone is not enough: operators need to inspect why an individual is behaving as they are.

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/npcs` | Paginated directory with ID, name, alive/deceased status, age if modelled, occupation, home, workplace and current room |
| Required | GET `/npcs/{npc_id}` | Full canonical NPC profile |
| Strongly recommended | GET `/npcs/{npc_id}/needs` | Hunger, energy, fatigue, health, comfort and other modelled homeostatic variables |
| Strongly recommended | GET `/npcs/{npc_id}/feelings` | Current emotions, contentment and affect values |
| Strongly recommended | GET `/npcs/{npc_id}/traits` | Personality, temperament, skills, physical/mental attributes and vocational traits |
| Strongly recommended | GET `/npcs/{npc_id}/occupation` | Occupation, workplace, shift, duties, skill requirements and employment status |
| Strongly recommended | GET `/npcs/{npc_id}/household` | Household ID, members, residence, household funds and shared obligations |
| Strongly recommended | GET `/npcs/{npc_id}/inventory` | Carried items, quantities, equipment and containers |
| Strongly recommended | GET `/npcs/{npc_id}/relationships` | Directed relationships, romance, commitments, opinions and social links |
| Strongly recommended | GET `/npcs/{npc_id}/goals` | Active life goals, progress, priority and completed milestones |
| Strongly recommended | GET `/npcs/{npc_id}/current-activity` | Current action, target, start tick, elapsed duration and location |
| Advanced | GET `/npcs/{npc_id}/history` | Significant life events, jobs, moves, relationships and milestones |
| Advanced | GET `/npcs/{npc_id}/health-history` | Illness, injuries, recovery and mortality history where modelled |
| Advanced | GET `/npcs/{npc_id}/memory` | Stored memory traces and recall metadata, subject to privacy/size controls |
| Advanced | GET `/npcs/{npc_id}/knowledge` | Known facts, rumours, beliefs and epistemic confidence |
| Advanced | GET `/npcs/{npc_id}/schedule` | Current/expected time commitments and temporal scheduler entries |
| Advanced | GET `/npcs/{npc_id}/social-context` | Clubs, factions, household, mentors, dependants and social roles |

Directory filters worth supporting:
- Name/ID search, occupation, alive/deceased, settlement, building, room, household, faction and club.
- Current activity, current needs thresholds, wealth bands, skill ranges and relationship state.
- Sort by name, wealth, age (if modelled), tick of last activity or a selected metric.

Do not create fake fields where a source model does not have them. Each response should describe which fields are unavailable and why.

---

## 6. NPC cognition, decision-making and AI inspection

This is one of the most valuable differentiators of the simulation. The UI should be able to explain behaviour, not merely show an NPC's current room.

| Priority | Method and route | Data |
|---|---|---|
| Strongly recommended | GET `/npcs/{id}/decision/current` | Current selected action, goal/drive, target, utility score and decision tick |
| Strongly recommended | GET `/npcs/{id}/decision/candidates` | Candidate actions and comparable utility components at the last decision |
| Strongly recommended | GET `/npcs/{id}/drives` | Active drives, intensities, weights and contributing variables |
| Strongly recommended | GET `/npcs/{id}/desires` | Desire hierarchy and current priorities |
| Strongly recommended | GET `/npcs/{id}/volition` | Means-end reasoning, selected means, expected outcomes and confidence |
| Strongly recommended | GET `/npcs/{id}/attention` | Attentional focus, salience and competing stimuli |
| Strongly recommended | GET `/npcs/{id}/working-memory` | Active working-memory contents, capacity and expiry |
| Advanced | GET `/npcs/{id}/planning` | Current plan, subgoals, dependencies, completion and failure reasons |
| Advanced | GET `/npcs/{id}/decision/history` | Recent decisions and outcome summaries |
| Advanced | GET `/npcs/{id}/decision/explain/{decision_id}` | Human-readable explanation of why a candidate won, including utility terms |
| Advanced | GET `/npcs/{id}/beliefs` | Belief state, evidence source, confidence and age of knowledge |
| Advanced | GET `/npcs/{id}/learning` | Mentorship, skill progression and learning history |
| Advanced | GET `/ai/summary` | Aggregate actions, goal distribution, planning load and decision statistics |

**High-value requirement:** decision explanations should be captured at decision time. Reconstructing an old decision from current NPC state can produce a misleading explanation. Store a bounded decision trace with the actual candidate scores and inputs used.

The UI should distinguish:
- Observed fact (the engine's actual state).
- NPC belief (what the citizen thinks is true).
- Rumour or second-hand information.
- Inferred explanation (an analysis generated for the operator).

---

## 7. Economy, production, trade and labour

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/economy/summary` | Total currency, treasury, household count, aggregate wealth and available macro indicators |
| Required | GET `/economy/commodities` | Commodity stock totals by location and owner |
| Strongly recommended | GET `/economy/commodities/{item_id}` | Item stock, production, consumption, demand, price/value and scarcity |
| Strongly recommended | GET `/economy/production` | Production by commodity, recipe, workplace and tick range |
| Strongly recommended | GET `/economy/consumption` | Consumption by commodity, household and tick range |
| Strongly recommended | GET `/economy/supply-chains` | Chain stages, inputs, outputs, bottlenecks and active flows |
| Strongly recommended | GET `/economy/households` | Household roster, wealth, income, expenditure and residence |
| Strongly recommended | GET `/economy/households/{id}` | Full household financial and member details |
| Strongly recommended | GET `/economy/labour/jobs` | Active job postings, vacancies, requirements and wages |
| Strongly recommended | GET `/economy/labour/requisitions` | Workplace labour demand and active requisitions |
| Strongly recommended | GET `/economy/labour/shifts` | Shift schedules, attendance and work allocation |
| Strongly recommended | GET `/economy/labour/employment` | Employment by NPC, occupation and workplace |
| Strongly recommended | GET `/economy/taxation/rules` | Tax rates, rules and effective dates |
| Strongly recommended | GET `/economy/taxation/history` | Assessments, collections, arrears and treasury inflows |
| Advanced | GET `/economy/transactions` | Auditable transaction ledger with source, destination, reason and tick |
| Advanced | GET `/economy/prices/history` | Price/value time series per commodity |
| Advanced | GET `/economy/wealth-distribution` | Wealth bands, inequality metrics and Gini calculation methodology |
| Advanced | GET `/economy/shortages` | Scarcity, unmet demand, affected households and duration |
| Advanced | GET `/economy/forecasts` | Optional projections clearly labelled as estimates, never actual simulation results |

Useful analysis:
- Who produces each commodity, who consumes it and where it moves.
- Which production chains are blocked and by which missing input.
- Which households are becoming poorer and why.
- Whether vacancies are being filled and whether shifts are staffed.
- How much wealth is held by each household or social class.
- Whether treasury balances reconcile with tax and expenditure records.

Avoid returning a single hard-coded commodity stock dictionary. The current `SimulationConnector.get_commodity_stocks()` returns example values; it must be replaced with a query against actual supply-chain state.

---

## 8. Society, relationships, governance and institutions

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/society/relationships` | Relationship directory with participant IDs, type, stage and status |
| Strongly recommended | GET `/society/relationships/{id}` | Full relationship, timeline, agreements and current status |
| Strongly recommended | GET `/society/commitments` | Bilateral commitments, parties, terms, due dates and fulfilment |
| Strongly recommended | GET `/society/opinions` | Directed NPC opinions and sentiment values |
| Strongly recommended | GET `/society/grudges` | Active grudges, involved citizens, causes, intensity and age |
| Strongly recommended | GET `/society/mentorship` | Mentor/apprentice links, skills taught and progress |
| Required | GET `/society/factions` | Factions, membership, platform and status |
| Strongly recommended | GET `/society/factions/{id}` | Members, influence, grievance, political activity and history |
| Required | GET `/society/decrees` | Active and historical municipal decrees |
| Strongly recommended | GET `/society/decrees/{id}` | Text/configuration, author, status, effective dates and effects |
| Required | GET `/society/clubs` | Social clubs and membership |
| Strongly recommended | GET `/society/clubs/{id}` | Club rules, meetings, officers, members and activity |
| Required | GET `/society/fraternal-aid` | Aid organisations, dues, claims and relief |
| Strongly recommended | GET `/society/justice/cases` | Lawsuits, charges, participants, status and hearing schedule |
| Strongly recommended | GET `/society/justice/cases/{id}` | Full case timeline, evidence references, decisions and penalties |
| Strongly recommended | GET `/society/crime` | Crime decisions/incidents and reporting history where implemented |
| Required | GET `/society/information` | Notices, rumours, information items and propagation waves |
| Strongly recommended | GET `/society/information/{id}` | Origin, known recipients, spread, belief/confidence and status |
| Strongly recommended | GET `/society/life-goals` | Active goals and completed milestones by NPC |
| Strongly recommended | GET `/society/gatherings` | Prolonged gatherings, participants, location and duration |
| Strongly recommended | GET `/society/recreation` | Games, contests, participants, wagers and outcomes |
| Strongly recommended | GET `/society/dilemmas` | Moral dilemmas, transgressions, confessions and outcomes |
| Advanced | GET `/society/social-graph` | Filtered relationship network edges and node metadata |
| Advanced | GET `/society/social-trends` | Membership, relationship formation, faction influence and sentiment over time |

The interface should let an operator move from a faction or institution to its members, then from a member to their citizen profile. All links should use stable IDs and share one canonical NPC record.

---

## 9. Environment, climate, health and mortality

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/environment/summary` | Current environmental conditions and active climate service status |
| Strongly recommended | GET `/environment/climate` | Current microclimate and weather state |
| Strongly recommended | GET `/environment/climate/history` | Temperature/weather/climate series by tick |
| Strongly recommended | GET `/environment/conditions` | Local conditions by settlement/room where modelled |
| Strongly recommended | GET `/environment/urban-growth` | Growth/decay state and facility/urban indicators |
| Strongly recommended | GET `/health/summary` | Health events, illness burden and mortality totals where tracked |
| Strongly recommended | GET `/health/incidents` | Illness, infection, injury and health incident records |
| Strongly recommended | GET `/health/mortality` | Death count, causes and timeline |
| Strongly recommended | GET `/health/mortality/{npc_id}` | Individual mortality/death record if deceased |
| Advanced | GET `/environment/resources` | Resource nodes, soil plots, harvesting state and depletion |
| Advanced | GET `/environment/risks` | Weather, environmental or resource risks affecting citizens |

Only expose metrics that the current source actually tracks. Do not imply a health model or environmental variable exists simply because a UI panel would be useful.

---

## 10. Content packs, settings and modding tools

The repository's content guide describes declarative JSON packs, dependencies, JSON Merge Patch, referential validation and automated tests. This warrants a much richer content-management screen.

| Priority | Method and route | Data/action |
|---|---|---|
| Required | GET `/content/packs` | Pack ID, name, version, enabled/mounted status and dependencies |
| Required | GET `/content/packs/{id}` | Manifest, files, dependencies and load status |
| Strongly recommended | GET `/content/packs/{id}/dependencies` | Dependency graph, missing dependencies and cycle errors |
| Strongly recommended | GET `/content/packs/{id}/contents` | Content categories and record counts |
| Strongly recommended | GET `/content/packs/{id}/files/{path}` | Read-only JSON file content for editor/inspection |
| Strongly recommended | POST `/content/packs/{id}/validate` | Full pack validation without mounting |
| Strongly recommended | GET `/content/validation/{job_id}` | Validation progress, errors, warnings and file/line references |
| Strongly recommended | POST `/content/packs/{id}/mount` | Mount after dependency and schema validation |
| Strongly recommended | POST `/content/packs/{id}/unmount` | Unmount only if safe and dependency constraints permit |
| Strongly recommended | GET `/content/load-history` | Which packs loaded, order, duration and warnings |
| Strongly recommended | GET `/content/settings` | Effective settings grouped by domain |
| Strongly recommended | GET `/content/settings/{domain}` | Specific settings and provenance |
| Advanced | POST `/content/preview-merge` | Preview JSON Merge Patch result without saving |
| Advanced | POST `/content/validate-all` | Run full strict content lint |
| Advanced | POST `/content/reload` | Safe reload operation with pre-flight checks |
| Advanced | GET `/content/schema/{type}` | Schema and allowed fields for a content record |
| Advanced | GET `/content/migrations` | Available schema migrations and compatibility |
| Advanced | POST `/content/export` | Export selected data/pack as a portable archive |
| Advanced | GET `/content/test-results` | Latest unit, lint and pack-balance test results |

If future UI editing is authorised, add a draft/preview/validate/apply workflow. Never silently write directly into active scenario files. Show a diff, validate references, show dependent packs, require confirmation, and keep backups/version history. The present UI can remain read-only until that write workflow is specified.

---

## 11. Event feed, history and audit trail

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/events` | Recent domain events with pagination and filters |
| Required | GET `/events/{event_id}` | Full event payload and source entity |
| Strongly recommended | GET `/events/types` | Known event types and descriptions |
| Strongly recommended | GET `/events?from_tick=&to_tick=&type=&source_id=` | Filtered historical event search |
| Strongly recommended | GET `/events/entity/{entity_id}` | Timeline of events associated with a citizen, building, item or institution |
| Strongly recommended | GET `/audit/actions` | Operator actions and API mutations, including who/when/why |
| Advanced | GET `/events/causal-chain/{event_id}` | Related events and causal references where the engine records them |
| Advanced | POST `/events/export` | Export selected event window for analysis |

The EventBus currently stores a bounded in-memory history (up to a configured maximum). The adapter should expose retention limits and make clear that older events may no longer be available.

---

## 12. Telemetry, reporting and analytics

| Priority | Method and route | Data |
|---|---|---|
| Required | GET `/telemetry/latest` | Latest validated snapshot with source tick |
| Required | GET `/telemetry/series/{metric}` | Time series with units, aggregation and sample count |
| Strongly recommended | GET `/telemetry/catalog` | Available metrics, definitions, units, categories and availability |
| Strongly recommended | GET `/telemetry/summary` | Population, wealth, economy, social, health and urban summaries |
| Strongly recommended | GET `/telemetry/events` | UI activity feed derived from actual events |
| Strongly recommended | POST `/reports/generate` | Generate a report for a selected tick range |
| Strongly recommended | GET `/reports/{job_id}` | Report progress/result |
| Strongly recommended | GET `/reports/latest` | Latest completed report |
| Strongly recommended | GET `/reports/{id}/download` | Export report in JSON/CSV/HTML or PDF if supported |
| Advanced | GET `/analytics/population` | Demographic distributions and population changes |
| Advanced | GET `/analytics/economy` | Wealth, prices, production, shortages and household outcomes |
| Advanced | GET `/analytics/relationships` | Relationship formation, duration, social cohesion and faction dynamics |
| Advanced | GET `/analytics/urban` | Building/room occupancy, integrity and spatial access |
| Advanced | GET `/analytics/behaviour` | Action/goal distributions and agent behaviour patterns |
| Advanced | GET `/analytics/comparisons` | Compare snapshots/runs/scenarios on matching metrics |

**Current source warning:** `LiveTelemetryEngine.get_latest()` and `get_metric_timeseries()` currently return fixed example values. `DeepSimulationReporter` also contains initial constants and mostly empty report fields. `SimulationIntegrityAuditor` returns predetermined results. These modules need real instrumentation and validation before their responses can be shown as actual results.

Every chart series must include:
- Metric ID, display label, unit and definition.
- Tick/time coordinate and sampling interval.
- Source and completeness/retention metadata.
- Whether values are observed, aggregated, estimated or unavailable.
- Missing-data markers; never silently fill gaps with zero.

---

## 13. Runtime performance and subsystem diagnostics

| Priority | Method and route | Data |
|---|---|---|
| Strongly recommended | GET `/diagnostics/runtime` | Tick duration, ticks/second, average and percentile timings |
| Strongly recommended | GET `/diagnostics/subsystems` | Per-subsystem last duration, average duration, failures and stage |
| Strongly recommended | GET `/diagnostics/errors` | Exceptions and error summaries grouped by subsystem/tick |
| Strongly recommended | GET `/diagnostics/queues` | Pending scheduled tasks, temporal jobs and backlog if exposed |
| Strongly recommended | GET `/diagnostics/memory` | Process memory and bounded history sizes |
| Advanced | GET `/diagnostics/hotspots` | Highest-cost subsystems and repeated slow operations |
| Advanced | GET `/diagnostics/event-bus` | Event counts, subscribers, dispatch failures and history retention |
| Advanced | GET `/diagnostics/spatial` | Graph node/edge counts, invalid connections and pathfinding performance |
| Advanced | GET `/diagnostics/cache` | Cache hit/miss and invalidation metrics where caches exist |

Performance endpoints should not expose sensitive file paths, environment variables or secrets. Keep diagnostics read-only and bounded.

---

## 14. Safe operator actions and command APIs

The initial UI can be read-mostly. If operational actions are later added, they must be explicit commands, not generic arbitrary object mutation.

| Priority | Method and route | Action |
|---|---|---|
| Required | POST `/simulation/start` | Start/resume |
| Required | POST `/simulation/pause` | Pause |
| Required | POST `/simulation/step` | Step exact ticks |
| Strongly recommended | POST `/simulation/fast-forward` | Fast-forward with bounds |
| Strongly recommended | POST `/content/packs/{id}/mount` | Mount a validated pack |
| Strongly recommended | POST `/content/reload` | Reload content after validation |
| Advanced | POST `/commands` | Typed command envelope for future supported actions |
| Advanced | GET `/commands/{id}` | Command status and result |
| Advanced | POST `/commands/{id}/cancel` | Cancel only if command is cancellable |

Future command types might include posting a municipal decree, assigning a job or triggering a supported scenario event. Do not expose these until the engine has a documented command handler, input validation, lifecycle rules, permissions, audit event and deterministic behaviour.

Do not expose direct edits to NPC needs, wealth, relationships, inventory, location or cognition as ordinary UI controls. Such edits can violate invariants and make runs irreproducible.

---

## 15. Live updates: streaming contract

Prefer one authenticated event stream over frequent full-page polling.

Recommended:
- `GET /api/v1/stream/events` using Server-Sent Events for one-way updates, or a WebSocket if bidirectional messaging is genuinely required.
- Event envelope: `event_id`, `event_type`, `simulation_tick`, `virtual_time`, `occurred_at`, `source_id`, `payload_version`, `payload`.
- Support reconnect with a last-event cursor/ID.
- Send heartbeat events and expose dropped-event/replay limitations.
- Publish summary updates at a controlled frequency; do not push every internal calculation.
- Keep commands on normal POST routes, even if WebSocket is used for updates.

Suggested event topics:
- `simulation.lifecycle_changed`
- `simulation.tick_completed`
- `simulation.progress`
- `npc.created`, `npc.updated`, `npc.died`
- `npc.location_changed`, `npc.activity_changed`
- `economy.stock_changed`, `economy.shortage_detected`
- `relationship.changed`, `faction.changed`, `decree.enacted`
- `content.pack_loaded`, `content.validation_failed`
- `diagnostics.error`, `report.completed`

The stream should deliver change notifications and small summaries, not entire world snapshots.

---

## 16. Recommended delivery order

### Phase 1 — make the current UI truthful and functional
1. API health, capabilities and metadata.
2. Simulation status and lifecycle controls.
3. World summary, settlements/buildings/rooms.
4. NPC directory and full NPC detail.
5. Actual event feed.
6. Content pack list and validation status.
7. Replace all hard-coded preview values with API data or explicit unavailable states.

### Phase 2 — make the simulation inspectable
1. NPC needs, traits, occupation, household, inventory and relationships.
2. Current activity and recent history.
3. Decision candidates, utility breakdown and goal/drive state.
4. Economy summary, commodity stocks, supply chain, jobs and household economy.
5. Factions, decrees, justice, clubs, information networks and life goals.
6. Climate and mortality records where implemented.

### Phase 3 — make it a serious operations and analysis tool
1. Time-series telemetry and metric catalogue.
2. Report generation and export.
3. Runtime/subsystem performance diagnostics.
4. Content dependency graph, preview merge, strict validation and safe reload.
5. Save/checkpoint/replay only after complete engine serialisation exists.
6. Run comparison, determinism and integrity tools after their current placeholder implementations are replaced with real tests.

---

## 17. Acceptance criteria for every endpoint

An endpoint is not complete merely because it returns HTTP 200.

- It reads the real current engine/context/service state.
- It returns a documented schema with stable IDs and units.
- It distinguishes zero, empty, unavailable, not initialized and error.
- It handles missing optional services without crashing.
- It has pagination/filtering for potentially large results.
- It does not mutate state unless explicitly a command endpoint.
- It has unit tests and an integration test against an initialized Oakwood scenario.
- It has tests for empty world, missing service, malformed ID and stopped/uninitialized engine.
- It has a performance bound and does not serialize the entire world for a small query.
- It documents data retention and whether history is complete.
- It does not expose internal mutable Python objects or arbitrary file access.
- It has an API version/schema version and a capability declaration.
- Mutating commands are validated, auditable, permission-controlled and deterministic where possible.

## 18. Source-backed gaps confirmed during inspection

These are concrete issues visible in the current repository, not assumptions about future design:

1. `src/api/local_interface.py` is not an HTTP server. `LocalVisualAPI` has no implemented methods.
2. `SimulationConnector.get_commodity_stocks()` returns fixed sample stock counts.
3. `get_faction_statuses()`, `get_active_grudges()`, `get_mentorship_history()`, `get_active_domestic_spats()` and `get_power_contracts()` currently return empty collections.
4. `get_pending_lawsuits()` is the only connector method shown reading a service, and it only exposes active lawsuits.
5. `SimulationClock` exposes tick, pause state and virtual time in Python; those need serialised read endpoints.
6. `EventBus` stores bounded in-memory history and supports subscriptions, but there is no browser-facing event stream.
7. The engine exposes settlements, NPCs, objects and item definitions through `WorldContext`; the UI needs read-only serializers and filtered endpoints.
8. The engine registers many useful services (supply chain, household economy, labour demand, jobs, climate, factions, decrees, information, clubs, aid, recreation, dilemmas, life goals and cognition services), but there is no complete UI query surface for them.
9. The telemetry, deep report and integrity classes inspected contain fixed/example values. They must be made data-driven and tested before they are treated as reliable diagnostics.
10. The content guide calls for declarative packs, dependency ordering, merge patches and strict validation. The UI should expose these capabilities only to the extent that the loader/validator actually implements them.

## 19. What is deliberately out of scope

- Any 2D or 3D world renderer, map, scene, animation, character art or decorative game assets.
- Changes to simulation behaviour, NPC decision logic, economy rules, content definitions or world data.
- Direct database/file-system access from the browser.
- Unrestricted remote code execution, arbitrary Python evaluation or generic object mutation.
- Claims that a proposed route or metric exists before it has been implemented and tested.

**Guiding principle:** expose the simulation as a transparent, inspectable system. The operator should be able to see what is happening, inspect why it is happening, trace the history and understand system health—without the UI secretly changing the simulation.
