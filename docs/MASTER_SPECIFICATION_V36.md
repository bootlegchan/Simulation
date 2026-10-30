# Master Specification & Architecture Design Document (V36)
**Project**: Headless Visual-Agnostic Social Simulation Engine  
**Release**: Version 36 (Stage-Pipelined Subsystem Microkernel Architecture)  
**Status**: Production / Feature-Complete

---

## 1. Executive Architecture Summary

The simulation backend is a **headless, 100% seed-deterministic, visual-agnostic emergent society engine**. In Version 36, the system features a **Stage-Pipelined Subsystem Microkernel Architecture**:

1. **Lightweight Dispatch Kernel (`SimulationEngine`)**:
   * Does not contain hardcoded gameplay or business logic.
   * Manages the lifecycle state (`UNINITIALIZED`, `INITIALIZING`, `READY`, `RUNNING`, `PAUSED`, `STOPPED`), clock time, and core seed determinism.
   * Delegates all domain simulation work to the `SubsystemPipelineManager`.
2. **Unified World Context (`WorldContext`)**:
   * Serves as the central state facade and service container.
   * Provides clean accessor facades for entities (`settlements`, `npcs`, `objects`, `items`, `recipes`), topology (`spatial_graph`, `spatial_grid`), finance (`municipal_treasury`, `debt_manager`), and event broadcasting.
3. **Data-Driven Subsystem Registry (`data/settings/subsystems_manifest.json`)**:
   * Every domain subsystem is declared in an external JSON manifest specifying its Python module, class name, execution stage, priority, and tick frequency.
   * New subsystems can be added, disabled, or retimed without altering engine code.

---

## 2. Pipeline Execution Stages & Frequency Intervals

Simulation ticks execute through four deterministic stages in strict topological order:

$$\text{PRE\_TICK} \longrightarrow \text{COGNITIVE\_DECISION} \longrightarrow \text{EXECUTION\_ACTION} \longrightarrow \text{POST\_TICK\_MAINTENANCE}$$

### 2.1 Stage Breakdown

| Stage | Execution Scope | Configured Subsystems |
|:---|:---|:---|
| **`PRE_TICK`** | Environmental and macro-world state calculations that precede agent perception. | `BiosphereSubsystem` (hourly temperatures, micro-climates), `InfrastructureSubsystem` (water well silt decay), `SuperstitionsSubsystem` (celestial omens, moral panic surges). |
| **`COGNITIVE_DECISION`** | Autonomous agent cognition, drive evaluation, perception, and planning. | `CognitiveAgentSubsystem` (physiological need decay, dynamic emotional feelings, habituation loops, subjective fog-of-war planning). |
| **`EXECUTION_ACTION`** | Physical actions, multi-agent steering, economic order matching, and interpersonal interactions. | Agent action execution (`ActionRegistry`), spatial steering (`SteeringAgent`), order book double-auction clearing (`OrderBook`). |
| **`POST_TICK_MAINTENANCE`** | Physical decay, economic compounding, institutional audits, and settlement lifecycle. | `EconomySubsystem` (food spoilage, loan debt interest, credit discounting), `GuildCartelSubsystem` (price floor audits), `UrbanLifecycleSubsystem` (structural degradation, adaptive repurposing, civic crisis planning), `LineageAllianceSubsystem` (dowries, blood feuds). |

---

## 3. Subsystem Domain Details

### 3.1 Urban Metabolism & Adaptive Repurposing (`src/world/urban_growth.py`)
* **Hierarchical District Zoning**: Configured via `urban_planning_config.json`. Settlements expand organically along dedicated roads (`street_market`, `row_craftsmen`, `lane_residential`, `path_sanctuary`, `track_industrial`, `alley_shadows`).
* **5-Stage Structural Lifecycle**: Tracks `structural_integrity` across `PRISTINE` (85–100), `MAINTAINED` (50–84.9), `DILAPIDATED` (25–49.9), `CONDEMNED` (1–24.9), and `RUINS` (0.0).
* **Adaptive Business Repurposing**: Configured via `building_mutation_rules.json`. Failing businesses adapt to survive:
  * Failing taverns convert into underground gambling speakeasies and cellar moonshine stills.
  * Struggling workshops install black market fencing counters for stolen goods.
  * Abandoned ruins are occupied by clandestine cults as occult sanctums.
  * Prosperous homeowners gentrify modest cottages into gilded salon villas.
* **Responsive Civic Planning**: Configured via `civic_crisis_policies.json`. Disasters trigger municipal emergency interventions:
  * Medical building deficits prompt the construction of **Emergency Healing Clinics**.
  * Fire or arson destruction prompts the construction of **Watchtowers & Fire Brigade Depots**.
  * Crime surges prompt the construction of **Garrison Security Checkpoints** with street lanterns.

### 3.2 Environmental Micro-Climates & Sanitation (`src/world/climate_and_infrastructure.py`)
* **Diurnal Thermal Dynamics**: Computes ambient outdoor temperature by season and hour. Indoor temperatures depend on structural insulation and active hearth heating (+22°C delta). Unheated winter homes trigger shivering and hypothermia energy drain.
* **Infrastructure Sanitation**: Water sources (`object_town_well`, `object_water_trough`, `object_drainage_culvert`) accumulate silt over time. Stagnant water degrades into contaminated states, resolvable via chemical purification using mineral alum (`item_purification_alum`).

### 3.3 Subjective Cognition, Habits & Psychology (`src/ai/cognitive_planning.py`, `src/npc/moral_erosion.py`)
* **Fog-of-War Planning**: Agents plan using their subjective `mental_map` and memory half-lives rather than omniscient global simulation state. Stale information leads to expectation failures and wasted-trip stress.
* **Habituation Loops**: Routine behaviors (prayer, drinking, work) develop habit strength. High habits reduce action execution effort; missing routine behaviors induces acute withdrawal stress.
* **Moral Alignment & Dissonance**: Tracks moral degradation from `VIRTUOUS` to `AMORAL`. Honorable NPCs committing illicit crimes suffer a `CRISIS_OF_CONSCIENCE` mental breakdown, resolvable through spiritual confession.

### 3.4 Informal Credit, Cartels & Lineage Alliances (`src/economy/credit_and_guilds.py`, `src/society/lineage_and_superstitions.py`)
* **Promissory Credit & Secondary Markets**: Notaries issue signed promissory notes and notched tally-stick IOUs. Noteholders can trade secondary debts at an 80% cash discount.
* **Artisan Guild Cartels**: Enforces minimum price floors on iron swords, bread, and ale. Cartel members who undercut are fined; independent scavengers undercutting on the black market operate under higher evasion risks.
* **Lineage Dowry Alliances**: Clan heads negotiate formal marriage contracts and dowries. Breaching an executed marriage pact triggers an active clan blood feud (+70.0 animosity).
* **Superstitious Omens**: Celestial portents (Blood Moons, Murrain) amplify citizen hysteria. Highly neurotic or uneducated citizens designate and scapegoat town outcasts or pariahs.

---

## 4. Entity & Blueprint Catalogs

* **34 Profiled NPCs**: Spanning patrician mayors, merchants, guards, artisans, clergy, courtesans, scavengers, notaries, diviners, guildmasters, and beggars.
* **35 Interactive Objects**: Spanning canopy beds, stone hearths, writing desks, altars, gambling pits, fencing counters, triage sickbeds, alarm bells, water wells, and drainage culverts.
* **37 Item Definitions**: Spanning staple foods, weapons, medicinal balms, personal diaries, heirlooms, promissory notes, tally sticks, moonshine, lotus resin, and occult relics.
* **10 Crafting Recipes**: Spanning flour milling, bread baking, iron smelting, sword forging, elixir brewing, moonshine distillation, and alum purification.
