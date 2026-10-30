# AI SYSTEM CONTEXT & EXTENSION SPECIFICATION (V38)
> **INTENDED AUDIENCE**: AI Coding Assistants, LLM Agents, Programmatic Code Generators.
> **HUMAN READABILITY**: OPTIONAL / NON-PRIMARY.
> **PROJECT**: Headless Visual-Agnostic Social Simulation Engine.

---

## 1. SYSTEM ARCHITECTURE & CORE INVARIANTS

### 1.1 Core Tenets
1. **Dynamic Relative Path Resolution**: NO HARDCODED ABSOLUTE PATHS. All pathing resolves via `src.core.path_utils.get_default_data_dir()` or `Path(__file__).resolve().parent`.
2. **Visual-Agnostic Spatial Topology**: Space is represented as abstract weighted nodes (`WeightedNodeTopology`). 2D/3D spatial coordinate vectors (`x_3d`, `y_3d`, `z_3d`) are projected dynamically for external visual clients.
3. **100% Seed Determinism**: All random operations MUST route through `SeededRandom` to preserve bitwise reproducible state trajectories across simulation resets.
4. **Data-Driven Entity Composition**: Entities are composed dynamically from external JSON blueprints in `data/` validated against JSON Schema Draft 2020-12 contracts.
5. **Discrete Choice Softmax Sampling**: AI drive selection converts S-curve utilities into Softmax choice probabilities using temperature scaling.
6. **Real-Time API, SSE Streaming & Bidirectional WebSocket RPC Bridge**: Real-time background execution loop (`SimulationRunner`) streams tick-by-tick state batches (`SimulationTickBatchDTO`), Server-Sent Events (`/api/v1/events/stream`), and receives real-time mutation RPC commands over WebSockets (`/api/v1/ws/bridge`).
7. **Multi-Channel Social Learning & Epistemic Belief Synthesis**: NPCs learn about the world via public notice boards (100% credibility), workplace professional chatter (85% credibility), and tavern/leisure gossip (reputation-weighted credibility). Multi-source confirmation synthesizes speculative rumors into firm convictions.
8. **Dynamic Feelings & Emotional Mood Modeling**: NPCs track granular emotional feelings (`tenderness`, `passion`, `loneliness`, `stress`, `jealousy`, `guilt`, `grief`, `pride`, `contentment`, `resentment`). Emotions drive utility S-curves and decay naturally towards equilibrium.
9. **Expanded Content Blueprints**: Includes tangible content catalogs across physical intimacy, domestic living, sentimental heirlooms, and illicit underworld activities.
10. **Open-Minded Relationship Dynamics & Compersion Modeling**: Supports diverse relationship agreements (`MONOGAMOUS_EXCLUSIVE`, `OPEN_POLYAMOROUS`, `PLATONIC_COHABITATION`), declared communicative boundaries, and compersion that prevents automatic betrayal flags when outside encounters are mutually disclosed.
11. **Collaborative Intimacy & Strolling**: Features synchronized arm-in-arm multi-agent strolling (`couple_stroll`), collaborative domestic tasks (`cooperative_work_task`), playful flirting (`flirt_and_tease`), and restorative community mediation (`mediate_relationship_conflict`).
12. **Clandestine Cults & Esoteric Orders**: Secret subterranean societies (`CultOrder`) conducting nocturnal ceremonies (`CultRiteEngine`) at subterranean basalt altars with esoteric tomes, triggering moral panics and inquisitorial interrogations (`InquisitionAndHysteriaEngine`).
13. **Social Scandals, Taboos & Moral Economies**: Severe infractions trigger public ostracism (`SocialOstracismEngine`), 50% merchant markups on pariahs, and active citizen shunning, while desperate NPCs escape into underground vice dens (`ViceEscapismDen`) to consume lotus resin or gamble with loaded dice.
14. **Survival Economics & Indenture Peonage**: Destitute debtors enter binding indenture contracts (`IndentureManager`), garnishing 75% of labor wages to wealthy masters, while thieves launder stolen heirlooms through shadow fence broker counters (`ContrabandFencingRing`).
15. **Moral Erosion & Cognitive Dissonance Crises**: Tracks moral alignment drift from `VIRTUOUS` to `AMORAL` (`MoralErosionTracker`). When honorable NPCs commit dark crimes, cognitive dissonance triggers a `CRISIS_OF_CONSCIENCE` state, resolvable through penitent confessions to municipal or spiritual authorities.
16. **Dynamic Urban Growth & Intelligent Road Hierarchy**: Settlements expand as metabolic spatial graphs configured via `urban_planning_config.json`. New structures attach to hierarchical district roads rather than scattering arbitrarily.
17. **Building Lifecycle Degradation & Economic Coupling**: Structures track `structural_integrity` across 5 stages (`PRISTINE`, `MAINTAINED`, `DILAPIDATED`, `CONDEMNED`, `RUINS`). Economic prosperity funds repairs, while severe economic depression triggers maintenance neglect, leading to squatter ruin states or urban demolition.
18. **Data-Driven Functional Object Placement**: Objects in newly constructed rooms follow functional anchor rules (`object_placement_rules.json`) matching room archetypes, automatically stocking initial contextual items.
19. **Adaptive Building Repurposing & Functional Mutation**: Buildings adapt their economic and functional use dynamically based on `building_mutation_rules.json`. Bankrupt businesses convert into vice gambling speakeasies or fencing counters; neglected homes turn into squatter tenements; and ruined structures are repurposed as clandestine cult sanctums. Prosperous owners gentrify modest cottages into gilded salon villas.
20. **Responsive Civic Urban Planning & Crisis Mitigations**: Municipal authorities actively respond to town disasters via `civic_crisis_policies.json`. Medical outages trigger emergency healing clinics; fire outbreaks commission watchtowers and water reservoirs; and crime surges deploy security checkpoints with street lanterns.
21. **Environmental Micro-Climates & Thermal Dynamics**: `MicroClimateEngine` calculates ambient temperatures by season and diurnal cycle, indoor structural insulation, and hearth heating deltas (+22°C), applying hypothermia energy drain and freezing damage during cold snaps.
22. **Infrastructure Sanitation & Water Purity Decay**: `InfrastructureSanitationEngine` tracks water source purity on wells, troughs, and drainage culverts, accumulating daily silt and contamination when unmaintained and enabling chemical purification using mineral alum.
23. **Subjective Fog-of-War Cognition & Habituation Loops**: `SubjectiveCognitionEngine` tracks NPC beliefs about shop stocks with memory half-life decay, triggering wasted-trip stress when expectations fail reality. `HabituationEngine` models habit formation for routine behaviors, discounting action effort while inducing withdrawal stress when compulsive routines lapse.
24. **Informal Credit Instruments & Secondary Debt Markets**: `CreditInstrumentManager` models negotiable promissory notes and tally stick IOUs, enabling secondary market debt trading at discounted face values and default tracking.
25. **Guild Cartels, Price-Fixing & Scavenger Undercutting**: `GuildCartelManager` enforces minimum price floors across artisan guilds, fining compliant members who undercut while tracking non-guild scavengers operating on the black market.
26. **Lineage Marriage Dowries & Superstition Omens**: `LineageAllianceEngine` formalizes inter-clan dowry pacts and blood feuds. `SuperstitionOmensEngine` models celestial portents (blood moons, blighting frosts) that amplify citizen paranoia and drive superstitious scapegoating.
27. **Stage-Pipelined Subsystem Kernel Architecture**: Engine is refactored into a decoupled microkernel (`SimulationEngine`) delegating all domain logic to `SubsystemPipelineManager` across strict execution stages (`PRE_TICK`, `COGNITIVE_DECISION`, `EXECUTION_ACTION`, `POST_TICK_MAINTENANCE`). Subsystems implement `ISimulationSubsystem` and access state via the `WorldContext` facade.
28. **100% Data-Driven Subsystem Manifest**: Subsystems are declared in `data/settings/subsystems_manifest.json` with execution frequency, priority, and stage, eliminating all hardcoded subsystem registration from the engine kernel.
29. **Simulation Integrity & Trajectory Divergence**: Dual verification invariant: 100% bitwise determinism for identical seeds vs. healthy trajectory divergence (Jaccard event distance < 0.95, wealth Euclidean distance > 5.0, action Shannon entropy H > 1.2 bits) across distinct seeds, guaranteeing non-stagnant emergent simulation dynamics.
30. **Logical Invariants & Systemic Conservation**: Core conservation laws: total wealth changes only through valid economic mechanisms (labor, purchases, fines, dowry, debt redemption); critical hunger strictly overrides secondary work/social pursuits; and nocturnal diurnal modifiers naturally drive circadian sleep schedules.
31. **LLM Qualitative Verisimilitude & Biographical Diary Benchmark (VVI)**: Evaluates chronological lifetime journals across 5 human realism dimensions: Psychological Coherence, Diurnal Rhythm, Socio-Relational Grounding, Material/Economic Adaptation, and Crisis Resilience, benchmarked against real-world human village history.
32. **Consolidated Domain-Driven Testing**: Test suite is organized into 17 clean, high-performance domain test modules (`tests/test_01_*` to `tests/test_17_*`), executing 95 tests with 100% pass rate in ~7.6 seconds.

---

## 2. REPOSITORY FILE TAXONOMY & MODULE MAP

```
.
├── requirements.txt                    # Python environment dependencies
├── pyproject.toml                      # Standard PIP package setup manifest
├── run_tests.py                        # Automated test runner script (Runs all 17 suites)
├── run_simulation.py                   # Standalone simulation execution script
├── AI_SYSTEM_CONTEXT_AND_EXTENSION_SPEC.md # This specification file
├── DOCUMENT_STANDARDS.md               # Standards & Conventions for JSON Data & Blueprints
├── docs/                               # System Documentation & Benchmarks
│   ├── MASTER_SPECIFICATION_V36.md
│   ├── CODE_GUIDELINES_V36.md
│   └── LLM_VERISIMILITUDE_BENCHMARK_REPORT.md # Qualitative Human Realism Evaluation Dossier
├── src/
│   ├── api/                            # REST & Real-Time WebSocket API Subsystem
│   ├── core/                           # Subsystem Pipeline, WorldContext, Clock, SeededRandom, EventBus
│   ├── simulation/                     # Decoupled SimulationEngine Microkernel & SimulationRunner
│   ├── subsystems/                     # Modular Domain Subsystems (ISimulationSubsystem)
│   │   ├── biosphere.py                # BiosphereSubsystem (Climate & Micro-climates)
│   │   ├── infrastructure.py           # InfrastructureSubsystem (Water Sanitation & Silt)
│   │   ├── superstitions.py            # SuperstitionsSubsystem (Omens & Panics)
│   │   ├── cognitive.py                # CognitiveAgentSubsystem (Autonomy, Needs, Feelings, Habits)
│   │   ├── economy.py                  # EconomySubsystem (Spoilage, Debt, Credit Instruments)
│   │   ├── guilds.py                   # GuildCartelSubsystem (Price Floors & Audits)
│   │   ├── urban.py                    # UrbanLifecycleSubsystem (Degradation, Repurposing, Crises)
│   │   └── lineage.py                  # LineageAllianceSubsystem (Dowries & Feuds)
│   ├── world/                          # Urban Growth, Micro-Climates, Topology, Blueprints
│   ├── entities/                       # NPC (with Biographical Log), InteractiveObject, ItemInstance
│   ├── ai/                             # Utility Evaluator, GOAP Planner, Cognitive Planning
│   ├── behaviours/                     # ActionRegistry: Intimacy, Domestic, Illicit, Strolls, Cults
│   ├── npc/                            # MemorySystem, Kinship, LifeStage, MoralErosionTracker
│   ├── society/                        # Romance, Cults, Scandals/Ostracism, Lineage, Superstitions
│   ├── economy/                        # CreditInstruments, GuildCartels, Indenture, OrderBook, Pricing
│   ├── diagnostics/                    # Verification & Benchmarks
│   │   ├── simulation_integrity.py     # SimulationIntegrityAuditor (Bitwise Determinism & Divergence)
│   │   ├── verisimilitude_benchmark.py # BiographicalDiaryCompiler & VerisimilitudeBenchmarkEngine
│   │   └── run_verisimilitude_benchmark.py # CLI Runner for Verisimilitude Dossier
│   └── configuration/                  # ContentLoader, SchemaValidator, ConstraintSolver
├── data/
│   ├── scenarios/                      # Scenario manifests (oakwood_baseline.json)
│   ├── settlements/                    # Settlement graph definitions
│   ├── buildings/                      # Data-driven building blueprints (blueprints.json)
│   ├── npcs/instances/                 # 34 NPC JSON profiles
│   ├── objects/                        # 35 Interactive object definitions
│   ├── items/                          # Item definitions
│   ├── production/                     # Crafting recipes
│   └── settings/                       # subsystems_manifest.json, urban_planning_config.json, etc.
└── tests/                              # Consolidated 17-Domain Test Suite
    ├── test_01_core_and_infrastructure.py
    ├── test_02_world_topology_and_entities.py
    ├── test_03_ai_senses_and_cognition.py
    ├── test_04_economy_production_and_trade.py
    ├── test_05_society_justice_and_psychology.py
    ├── test_06_procedural_setup_and_audit.py
    ├── test_07_api_and_realtime_runner.py
    ├── test_08_social_learning_and_channels.py
    ├── test_09_expanded_content_feelings_and_intimacy.py
    ├── test_10_cults_scandals_and_dark_underworld.py
    ├── test_11_dynamic_settlement_growth_and_placement.py
    ├── test_12_adaptive_urban_repurposing.py
    ├── test_13_extended_world_mechanics.py
    ├── test_14_subsystem_pipeline_kernel.py
    ├── test_15_simulation_integrity_and_diversity.py
    ├── test_16_logical_invariants_and_simulation_dynamics.py
    └── test_17_llm_verisimilitude_and_diary_benchmark.py
```

---

## 3. CONSOLIDATED TEST SUITE TAXONOMY

The test suite is structured into 17 domain-specific test modules:

| Test Module | Domain Scope | Covered Subsystems |
|---|---|---|
| `test_01_core_and_infrastructure.py` | Core Primitives | Path Resolution, SimulationClock, SeededRandom, EventBus, EventStore, ContentLoader, SchemaValidator |
| `test_02_world_topology_and_entities.py` | Spatial & Entities | BaseEntity, ItemDefinition/Instance, InteractiveObject, WeightedNodeTopology, SpatialGridIndex, SteeringAgent, PermissionsEngine, WorldMutationEngine, LocalResourceNodes |
| `test_03_ai_senses_and_cognition.py` | AI & Cognition | UtilityEvaluator (S-Curves/Softmax), GOAPPlanner (A*), FSMController, PerceptionSystem, SensoryHub, Stratified MemorySystem, ConversationalInquiryEngine, ReflectionEngine |
| `test_04_economy_production_and_trade.py` | Economy & Market | OrderBook (Central Limit), BargainingEngine, ProductionManager, Recipe, SpoilageTracker, DynamicPricingEngine, DebtManager, MacroEconomicTracker |
| `test_05_society_justice_and_psychology.py` | Society & Psychology | FactionHostilityMatrix, CoalitionManager, MunicipalTreasury, InterpersonalBond, CourtroomTrialEngine, UnderworldActivityEngine, AttachmentEngine, TriangularLoveModel, SocialPenetrationEngine, GoffmanFrontBackStage, MateRetentionEngine |
| `test_06_procedural_setup_and_audit.py` | Procedural & Audits | MacroZoningGrammar, MicroNPCArchetypeGrammar, ConstraintSolver, KinshipGraph, SettlementHistoryGenerator, PrebalanceEngine, TownSetupEngine, IntentionalityAuditor |
| `test_07_api_and_realtime_runner.py` | API & Real-Time | FastAPI Endpoints, Control Actions, Visual DTO Projections, Real-time SimulationRunner, StateMutator, WebSocket RPC Bridge |
| `test_08_social_learning_and_channels.py` | Social Learning | NoticeBoardEngine, WorkplaceChatterEngine, TavernSocialGatheringEngine, EpistemicBeliefEngine |
| `test_09_expanded_content_feelings_and_intimacy.py` | Content, Feelings & Intimacy | Physical Intimacy, Courtship Gifts, Domestic Hearth, Heirlooms, Personal Diary, Blackmail Extortion, Illicit Distillation, Feelings Profile & Moods, Couple Strolls, Cooperative Tasks, Polyamorous Agreements & Compersion, Restorative Mediation |
| `test_10_cults_scandals_and_dark_underworld.py` | Cults, Scandals & Dark Underworld | Clandestine Cult Orders, Esoteric Rites, Moral Panics & Inquisitions, Taboos & Social Ostracism Shunning, Survival Indenture Peonage, Contraband Fencing, Vice Dens & Lotus Resin, Moral Alignment Degradation & Crises of Conscience |
| `test_11_dynamic_settlement_growth_and_placement.py` | Urban Growth & Object Placement | Data-Driven Zoning & Road Hierarchy, Intelligent District Building Attachment, Building Degradation Lifecycles, Economic Maintenance & Ruins Evictions, Demolition & Redevelopment, Functional Anchor Object & Item Placement |
| `test_12_adaptive_urban_repurposing.py` | Adaptive Repurposing & Civic Crisis Planning | Business Distress to Illicit Speakeasy/Fencing Mutation, Ruin Conversion to Occult Sanctums, Responsive Medical Deficit Emergency Clinics, Fire Watchtowers & Reservoirs, Security Checkpoints, Prosperity Gentrification |
| `test_13_extended_world_mechanics.py` | Climate, Sanitation, Cognition & Lineage | Micro-Climates & Thermal Dynamics, Water Sanitation & Well Silt Decay, Subjective Fog-of-War Expectations, Habituation Loops & Withdrawal, Promissory Notes & Secondary Discounting, Guild Cartels & Price Floors, Marriage Dowry Feuds, Celestial Omens & Scapegoating |
| `test_14_subsystem_pipeline_kernel.py` | Subsystem Pipeline Microkernel Architecture | SubsystemPipelineManager, WorldContext Facade, Topological Stage Execution Ordering (PRE_TICK -> COGNITIVE -> EXECUTION -> POST_TICK), Priority Ordering, Frequency Interval Gating (1, 60, 1440), Dynamic Runtime Registration, Event Broadcasting, Subsystem State Persistence |
| `test_15_simulation_integrity_and_diversity.py` | Simulation Integrity & Diversity | 100% Bitwise Determinism for Identical Seeds, Trajectory Divergence Across Distinct Seeds, Action Choice Shannon Entropy (H > 1.2 bits), State Space Coverage, Longitudinal Divergence Scaling |
| `test_16_logical_invariants_and_simulation_dynamics.py` | Logical Invariants & Simulation Dynamics | Currency Supply Conservation, Starvation Need Override of Routine Work, Diurnal Circadian Sleep/Rest Domination at Night, Thermal Insulation and Hearth Warmth in Winter, 72-Hour Multi-Day Deadlock-Free Stability |
| `test_17_llm_verisimilitude_and_diary_benchmark.py` | LLM Verisimilitude & Diary Benchmark | Biographical Diary Extraction, Psychological Coherence vs. Physical State, Diurnal Human Rhythm Realism, Material/Labor Rationality, Adversity Coping, Village Verisimilitude Index (VVI > 80.0) |

---

## 4. REAL-TIME API & VISUAL DTO CONTRACTS

### 4.1 Endpoints
* `GET /api/v1/simulation/status`: Returns `WorldStateDTO`.
* `POST /api/v1/simulation/control`: Executes action (`start`, `pause`, `resume`, `stop`, `step`, `set_tps`).
* `GET /api/v1/spatial/graph`: Returns `SpatialGraphDTO` with projected 2D/3D visual coordinates.
* `GET /api/v1/npcs`: Returns dictionary of `NPCVisualDTO` objects with live feelings, moral alignment, and dominant mood.
* `GET /api/v1/npcs/{npc_id}`: Detailed NPC state, needs, feelings, moral erosion, memories, relationships, and active GOAP plan.
* `GET /api/v1/objects`: Returns dictionary of `InteractiveObjectDTO` objects.
* `GET /api/v1/economy`: Gini coefficient, total currency supply, order book metrics, active indenture contracts, credit instruments.
* `POST /api/v1/mutate/npc/{npc_id}`: Live mutation of wealth, location, needs, feelings, vices, moral erosion, state.
* `POST /api/v1/mutate/npc/{npc_id}/action`: Forces immediate GOAP action or state on NPC.
* `POST /api/v1/mutate/object/{object_id}`: Modifies interactive object lock states and capabilities.
* `POST /api/v1/mutate/environment`: Modifies weather, season, and world tension.
* `POST /api/v1/mutate/events/inject`: Injects arbitrary domain event into live EventBus.
* `GET /api/v1/events/stream`: Server-Sent Events (SSE) live update stream.
* `WS /api/v1/ws/live`: Real-time WebSocket connection streaming `SimulationTickBatchDTO` payloads on every tick.
* `WS /api/v1/ws/bridge`: Bidirectional WebSocket connection executing inbound RPC commands (`MUTATE_NPC`, `FORCE_ACTION`, `MUTATE_OBJECT`, `MUTATE_ENV`, `INJECT_EVENT`).

---

## 5. EXTENSION DIRECTIVES FOR AI AGENTS

When extending this codebase, AI agents MUST adhere to the following rules:
1. **Never hardcode absolute file paths**. Always import `get_default_data_dir()` from `src.core.path_utils`.
2. **Never invoke `random.random()` or `time.time()` inside simulation logic**. Always pass `self.random` (`SeededRandom`) or simulation clock ticks.
3. **Always declare new domains as an `ISimulationSubsystem`** inside `src/subsystems/` and register them via `data/settings/subsystems_manifest.json` rather than cluttering `SimulationEngine`.
4. **Always create or update test files** in `tests/` (`test_01_*` through `test_17_*`) and verify 100% pass rate via `python3 run_tests.py`.
5. **Expose new state variables in DTOs** inside `src/api/dtos.py` so external 2D/3D visual frontends can render new mechanics.
