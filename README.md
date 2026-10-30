# Data-Driven Headless Social Simulation Engine (V38)

A modular, visual-agnostic, 100% seed-deterministic social simulation backend populated by autonomous NPCs with complex AI, dynamic economics, legal courtroom trials, psychological intimacy drives, multi-channel social learning, urban building lifecycles, and a **Stage-Pipelined Subsystem Microkernel Architecture**.

## 📁 Repository Structure

```
.
├── README.md                           # Master Project Overview & Setup Instructions
├── AI_SYSTEM_CONTEXT_AND_EXTENSION_SPEC.md # Machine-Optimized Specification for AI Agents
├── DOCUMENT_STANDARDS.md               # Standards & Conventions for JSON Data & Blueprints
├── pyproject.toml                      # Package configuration manifest
├── requirements.txt                    # Dependencies (FastAPI, uvicorn, pydantic, jsonschema)
├── run_tests.py                        # Consolidated test runner (95 Tests across 17 Modules)
├── run_simulation.py                   # Standalone simulation execution script
├── docs/                               # Complete System Documentation & Benchmarks
│   ├── MASTER_SPECIFICATION_V36.md     # Full architectural specification
│   ├── CODE_GUIDELINES_V36.md          # Architectural rules & design invariants
│   ├── PROFESSIONAL_SOCIAL_AUDIT.md    # Social, economic & psychological audit report
│   └── LLM_VERISIMILITUDE_BENCHMARK_REPORT.md # Qualitative Human Realism Evaluation Dossier
├── src/                                # Engine Source Code
│   ├── api/                            # REST, Server-Sent Events & WebSocket RPC Bridge
│   ├── core/                           # Clock, SeededRandom, EventBus, Context, Subsystem Pipeline
│   ├── simulation/                     # Decoupled SimulationEngine Microkernel & Runner
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
│   ├── ai/                             # S-Curve Utility Evaluator, GOAP Planner, Cognitive Planning
│   ├── behaviours/                     # ActionRegistry: Intimacy, Strolls, Cults, Indenture, Trade
│   ├── npc/                            # MemorySystem, Kinship, Moral Erosion, Lifecycle Aging
│   ├── society/                        # Romance, Cults, Scandals, Justice, Underworld, Lineage
│   ├── economy/                        # OrderBook, Bargaining, Pricing, Indenture, Cartels, Credit
│   ├── diagnostics/                    # Verification & Benchmarking
│   │   ├── simulation_integrity.py     # SimulationIntegrityAuditor (Determinism & Entropy)
│   │   ├── verisimilitude_benchmark.py # BiographicalDiaryCompiler & VerisimilitudeBenchmarkEngine
│   │   └── run_verisimilitude_benchmark.py # CLI Runner for Verisimilitude Dossier
│   └── configuration/                  # ContentLoader, SchemaValidator, ConstraintSolver
├── data/                               # Externalized Data Blueprints & Configurations
│   ├── scenarios/                      # Scenario manifests (oakwood_baseline.json)
│   ├── settlements/                    # Settlement graph blueprints (oakwood.json)
│   ├── buildings/                      # Data-driven building blueprints (blueprints.json)
│   ├── npcs/instances/                 # 34 Profiled NPC instances
│   ├── objects/                        # 35 Interactive object definitions
│   ├── items/                          # 37 Item definitions
│   ├── production/                     # 10 Crafting recipes
│   └── settings/                       # Subsystems manifest, urban planning, climate, etc.
└── tests/                              # Consolidated 17-Domain Test Suite (95 Tests)
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

## 🚀 Quick Start & Usage

### 1. Installation
```bash
pip install -r requirements.txt
pip install -e .
```

### 2. Run Test Suite (All 95 Tests)
```bash
python3 run_tests.py
```

### 3. Run Qualitative Verisimilitude & Diary Benchmark
```bash
python3 src/diagnostics/run_verisimilitude_benchmark.py
```

### 4. Start Live Real-Time API Server
```bash
python3 -m src.api.server
```

### 5. Direct Simulation Execution
```bash
python3 run_simulation.py
```
