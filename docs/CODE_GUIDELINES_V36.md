# Code Guidelines & Architecture Rules Document (V36)
**Project**: Headless Visual-Agnostic Social Simulation Engine  
**Standard**: Modular Microkernel & Pipelined Subsystems

---

## 1. Golden Architectural Invariants

### 1.1 Zero Hardcoding Policy
* **Never hardcode game mechanics, pricing, thresholds, or timers in Python files**.
* All configuration parameters, district profiles, object anchor slots, mutation rules, crisis tenders, and subsystem manifests must reside in external JSON files in `data/settings/`, `data/buildings/`, `data/items/`, or `data/objects/`.
* The Python engine is purely an execution interpreter of externalized data contracts.

### 1.2 Path Resolution
* **Never use hardcoded absolute paths** (e.g., `/workspace/...` or `C:\...`).
* Always resolve paths dynamically using `src.core.path_utils.get_default_data_dir()` or `Path(__file__).resolve().parent`.

### 1.3 Seed Determinism
* **Never call `random.random()`, `random.choice()`, or `time.time()` inside simulation logic**.
* All randomness must route through `context.random` (`SeededRandom`), and virtual time must route through `context.clock` (`SimulationClock`).
* Given identical seeds and inputs, the simulation state trajectory must remain bitwise identical across resets.

---

## 2. Subsystem Authoring Guidelines

When implementing a new simulation domain or extending an existing one:

1. **Implement `ISimulationSubsystem` (`src/core/subsystem.py`)**:
   ```python
   from src.core.subsystem import ISimulationSubsystem, TickStage, TickFrequency
   from src.core.context import WorldContext

   class CustomDomainSubsystem(ISimulationSubsystem):
       subsystem_id = "custom_domain"
       tick_stage = TickStage.POST_TICK_MAINTENANCE
       tick_frequency = TickFrequency.DAILY
       execution_priority = 50

       def initialize(self, context: WorldContext) -> None:
           self.data = context.loader.loaded_data.get("custom_domain_config", {})

       def on_tick(self, tick: int, context: WorldContext) -> None:
           # Domain logic here
           pass
   ```
2. **Declare in `data/settings/subsystems_manifest.json`**:
   Register the new subsystem in the external JSON manifest with its execution stage, frequency, and priority.
3. **Use `WorldContext` for State Access**:
   Never import other domain subsystems directly. Access shared state through `context.settlements`, `context.npcs`, `context.objects`, or `context.get_service()`.
4. **Broadcast via `EventBus`**:
   Communicate across domain boundaries using domain events:
   ```python
   context.publish_event(
       event_type="custom_domain_event",
       source="custom_domain",
       payload={"key": "value"}
   )
   ```

---

## 3. Testing Requirements

* Every new domain feature or subsystem must include automated tests in `tests/` following the `test_{NN}_{domain}.py` naming convention.
* Tests must run and pass cleanly via `python3 run_tests.py` with 100% pass rate.
* Test execution time across the entire suite should remain under 5 seconds.
