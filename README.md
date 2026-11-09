# Social Simulation Kernel (v168)

A stage-pipelined, closed-loop microkernel social simulation engine featuring pure continuous field dynamics, Hierarchical Asynchronous Event-Scheduled Time (HAEST), attentional mindspace cognition, elastic Maslow desire hierarchies, micro-climate thermodynamics, and opportunistic means-end volition.

---

## Quickstart & Verification

```bash
# Execute the full automated regression test suite (152+ unit and simulation tests)
python3 run_tests.py

# Run a 30-day baseline simulation of Oakwood Village with full telemetry
python3 run_simulation.py --days 30 --seed 42 --adaptive

# Run multi-seed longitudinal validation audit (Seeds 42, 1337, 777)
python3 run_multi_seed_audit.py

# Package clean production master release into /workspace/out/
python3 package_release.py --version v168
```

---

## Architectural Principles

1. **Zero-Code Coupling**: All gameplay assets, vocations, recipes, items, and rules are defined 100% declaratively in `data/settings/`, `data/scenarios/`, and `data/packs/`.
2. **No Implicit Finite State Machines**: Agent behaviors emerge from multinomial logit sampling over smooth continuous mathematical gradients (Process S sleep curves, metabolic S-curves, and quadratic moral elasticity).
3. **Opportunistic Means-End Volition**: When conventional paths are blocked, agents evaluate compensatory adaptations (borrowing, foraging, room rentals, vocational study) or transgressive alternatives (theft, trespassing), modulated by the **Continuous Moral Elasticity Equation**.
4. **Physical Spatial Graph & Closed-Loop Economy**: Agents physically traverse rooms with zero teleportation. Currency, commodities, and parish alms levies are strictly conserved with zero unbacked fiat minting.

---

## Directory Layout

- `src/` — Python microkernel modules:
  - `ai/` — Attentional mindspace, desire hierarchy, means-end volition, drive strategies, and preemption.
  - `configuration/` — Dynamic JSON loader, settings registry, and referential validator.
  - `core/` — Context, clock, spatial graph, and temporal scheduling.
  - `economy/` — Supply chains, job postings, taxation, work shifts, and intelligent dining.
  - `entities/` — NPCs, objects, items, status tags, and occupations.
  - `society/` — Epistemic memory engine, romance, fraternal aid lodges, social clubs, decrees, and dilemmas.
  - `world/` — Micro-climate, spatial thermodynamics, and urban settlement models.
- `data/` — Declarative JSON manifests (`settings/`, `settlements/`, `npcs/`, `items/`, `packs/`).
- `docs/` — Architectural standards and content creation guides (`CONTENT_PIPELINE_AND_MODDING_GUIDE.md`).
- `tests/` — Automated test suites:
  - `unit/` — Granular subsystem verification (`test_01` to `test_91`).
  - `simulation/` — Multi-run bitwise determinism and demographic stability tests.
