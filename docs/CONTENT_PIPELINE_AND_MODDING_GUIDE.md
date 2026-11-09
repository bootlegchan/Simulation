# Content Creation Pipeline & Architectural Modding Guide (v168)

> **TARGET AUDIENCE**: AI Coding Agents, Systems Engineers, and Content Creators.  
> **STANDARD**: 100% Declarative, Self-Contained Content Packs with Zero Python Code Coupling, Pure Continuous Field Dynamics, and Opportunistic Means-End Volition.  
> **ENGINE**: Stage-Pipelined Microkernel Social Simulation Engine with Hierarchical Asynchronous Event-Scheduled Time (HAEST).

---

## 1. Core Operating Principles & Invariants

1. **Zero-Code Coupling Principle**:
   - Never add content (new items, recipes, occupations, buildings, diseases, substances, factions, decrees, recreation games, penal sentences, dilemmas, life goals, or problem-solving paths) by writing hardcoded Python `Enum` values or `if/elif` string branches in engine source files (`src/`).
   - All content additions must be expressed purely through declarative JSON files located in `data/settings/` or modular content packs in `data/packs/<pack_id>/`.

2. **Hard Invariant: Absolute Prohibition of Implicit Finite State Machines (FSMs)**:
   - **No Discrete Phase State Enums as Decision Controllers**: Do not use discrete phase enums (e.g. `DailyRhythmPhase`, `CitizenState`) to gate or switch agent utilities. Phase and rhythm classifications exist strictly as *diagnostic/read-only observers*, never as utility override switches.
   - **No Artificial Utility Cliffs or Forced Overrides**: Never inject artificial step-function overrides (e.g. `env_mods["rest"] = +90.0`, `chosen_drive = "rest"`). All actions must be sampled via continuous multinomial logit from smooth utility equations.
   - **Pure Continuous Field Dynamics**: Sleep pressure, vocational alignment, hunger urgency, moral resistance, and social interest must emerge from smooth, continuous mathematical gradients (power laws, S-curves, Borbély Process S & Process C models).
   - **Zero Spatial Teleportation**: When an agent accepts a job posting, shifts tasks, or heads home to rest, they must physically navigate room-by-room along the `SpatialGraph`. Instantaneous room reassignment (`npc.location_id = target_room`) without traversal is strictly prohibited.
   - **Smooth Somatic Urgency over Step Preemptions**: Biological safety imperatives must out-compete scheduled labor via exponential somatic utility curves rather than hardcoded `if hunger >= 85: force_action` interrupt switches.

3. **Opportunistic Means-End Volition (No Hardcoded Roadblocks)**:
   - Humans are opportunistic problem solvers. When a conventional path is blocked (e.g. lacking coin for bakery bread, lacking a private bedchamber for courtship, or lacking certified skill for a job posting), agents **must not trigger an arbitrary failure gate or freeze**.
   - Instead, unmet desire tension accumulates, expanding the agent's attentional horizon and activating alternative pathways across three continuous tiers:
     1. **Conventional**: Approved, standard, lawful actions.
     2. **Compensatory**: Resourceful, adaptive compromises (borrowing from trusted friends, foraging, renting an inn room, self-study).
     3. **Transgressive**: Risky, unapproved, or illicit acts (petty shoplifting, trespassing indoors, black market contracts).
   - Transgressive viability scales smoothly via the **Continuous Moral Elasticity Friction Equation**.

4. **Self-Contained Content Pack Architecture**:
   - Each gameplay expansion, trade guild, district, or seasonal event lives inside its own isolated folder: `data/packs/<pack_id>/`.
   - Packs are self-describing via `pack.json`. Removing a feature from the game is as simple as deleting or disabling (`"enabled": false`) its pack folder.

5. **Topological Dependency Ordering**:
   - Packs declare explicit dependencies in `pack.json` (e.g. `"dependencies": ["base_oakwood"]`).
   - The engine automatically resolves and loads packs in strict topological order using Kahn's algorithm. Circular dependencies and missing dependencies are caught and reported during initialization.

6. **Non-Destructive Overrides (RFC 7396 JSON Merge Patch)**:
   - When modifying existing game content (adjusting item prices, tuning NPC traits, changing building rooms), packs use `patches.json` or `patches/*.json` using the RFC 7396 merge patch standard.
   - Never edit base scenario files directly when creating modular expansions.

7. **Bidirectional Spatial Integrity**:
   - Doorway connections between rooms are automatically linked reciprocally by `SpatialGraph` and `WeightedNodeTopology`.
   - All rooms in a settlement must possess a navigable path to a public circulation hub (Market Plaza / Town Square).

8. **Pre-Flight Validation & Regression Safety**:
   - Every pack must pass the automated referential linter (`python3 lint_content.py --strict`).
   - Every economic pack must pass the balance regression harness, verifying closed-loop wealth conservation and demographic stability.
   - All automated unit and longitudinal simulation tests (`python3 run_tests.py`) must pass with 100% success rate.

---

## 2. Directory Structure of the Declarative Data Manifests

```text
data/
├── items/items.json                    # Global commodity, tool, and consumable definitions
├── npcs/npcs.json                      # Baseline character sheets, personality, and social profiles
├── objects/objects.json                # Interactive affordance objects, workbenches, and beds
├── scenarios/oakwood_baseline.json     # Scenario orchestrator and initial settlement state
├── settlements/oakwood.json            # Architectural layout, buildings, rooms, and portals
├── settings/                           # Global declarative parameter manifests:
│   ├── attentional_mindspace.json      # Miller 7±2 thought streams, saliency weights, and profiles
│   ├── civic_governance.json           # Taxes, court fees, building/clergy exemptions, living costs
│   ├── commitments.json                # Bilateral social commitment contracts and breach penalties
│   ├── courtroom_lawsuits_config.json  # Lawsuit categories, evidence thresholds, and fines
│   ├── culinary_economy.json           # Food preparation, vendor margins, and meal tiers
│   ├── decrees.json                    # Town council ordinances, curfews, and public mandates
│   ├── desire_hierarchy.json           # Maslow 5-tier weights, cohabitation, and overcrowding drag
│   ├── dilemmas.json                   # Moral crises, psychological guilt, and confession mechanics
│   ├── drives.json                     # Behavioral drive definitions and utility parameters
│   ├── epistemic_system.json           # Memory half-life, visibility tiers, and priming weights
│   ├── factions.json                   # Political factions, platforms, and voting thresholds
│   ├── fraternal_aid.json              # Mutual aid lodges, dues, alms box, and sickness relief
│   ├── job_posting_rules.json          # Official and illicit labor posting generation rules
│   ├── life_goals.json                 # Long-term character aspirations and fulfillment milestones
│   ├── means_end_volition.json         # Conventional, compensatory, and transgressive pathways
│   ├── occupations.json                # Vocational profiles, schedules, shifts, and base skills
│   ├── physiology.json                 # Need decay rates, sleep recovery, and feelings homeostasis
│   ├── recipes.json                    # Production recipes, craft stations, and input/output ratios
│   ├── recreation_games.json           # Leisure games, wagering limits, and victory mechanics
│   ├── romance_and_bonds.json          # Romance stages, chemistry, consent, rentals, and privacy
│   ├── supply_chains.json              # Industrial commodity recipes, inputs, and throughputs
│   ├── temporal_engine.json            # HAEST time intervals, leaping rules, and action durations
│   └── weather_and_climate.json        # Seasons, solar curves, thermodynamics, and exposure
└── packs/<pack_id>/                    # Modular, self-contained expansions
```

---

## 3. Mathematical Reference: Continuous Field Equations

### 3.1 Homeostatic Sleep Pressure (Process S & Process C)
$$\text{Fatigue} = \max(0.0, 100.0 - \text{Energy})$$
$$U_{\text{rest}} = 0.25 \cdot \text{Fatigue} + 6.0 \cdot \left(\frac{\text{Fatigue}}{22.0}\right)^{2.3} + \text{CircadianBias} + \text{InertiaBonus}$$
*At $\text{Energy} = 90$, $U_{\text{rest}} \approx 3.5$. At $\text{Energy} = 20$, $U_{\text{rest}} \approx 140.5$.*

### 3.2 Continuous Vocational Alignment
$$\Phi_{\text{work}}(t) = \begin{cases} 
1.0 & \text{if within scheduled shift window} \\
0.75 \cdot \text{Willingness} & \text{if within overtime window and rested} \\
0.40 & \text{if } \le 1.5\text{h before shift start (commute attraction)} \\
0.05 + 0.25 \cdot \text{PovertyFactor} & \text{otherwise}
\end{cases}$$

$$\Delta U_{\text{work}} = (\Phi_{\text{work}}(t) - 0.5) \cdot 60.0 \cdot \left(\frac{\text{Energy}}{100.0}\right)$$

### 3.3 Dynamic Metabolic Hunger Decay
$$\text{Exertion } E = (0.70 \cdot P \cdot \text{WorkMultiplier}) + (0.30 \cdot M)$$
$$\text{Hunger Decay Rate} = \text{BaseRate} \cdot E^{1.15} \quad (\text{clamped between } 0.018 \text{ and } 0.180/\text{tick})$$
- Rest / Sleep: $0.018/\text{tick}$.
- Awake Sedentary: $0.031/\text{tick}$.
- Heavy Blacksmithing / Smelting: $0.085 - 0.120/\text{tick}$.

### 3.4 Micro-Climate & Somatic Thermodynamics
- **Room Temperature**: Modulated by outdoor ambient climate, building insulation factor (Civic: 0.85, Residential: 0.70, Industrial: 0.55), active hearth heat output (+18.0°C), and occupant body heat (+0.35°C).
- **Somatic Comfort & Exposure**:
  - Optimal thermal band: 18.0°C to 23.0°C.
  - Shivering Threshold: Below 12.0°C, continuous shivering stress accumulates at rate $0.025 \cdot (1.0 + \text{deficit})$, dragging down contentment.
  - Freezing / Outdoor Sleep: Sleeping exposed outdoors reduces energy recovery by 50%, adds +6.0 stress, and penalizes contentment by -8.0 per shift.

### 3.5 Continuous Moral Elasticity Friction Equation
When considering transgressive pathways (theft, trespassing, black market jobs), an agent's moral resistance is dynamically discounted by physiological or psychological urgency:

$$\text{EffectiveResistance} = \frac{\text{Honor} \cdot 40.0 + \text{Conscientiousness} \cdot 25.0 + \text{Piety} \cdot 20.0 - \text{CrimePropensity} \cdot 35.0}{\max\left(1.0, \text{Urgency}^2\right)}$$

$$\text{Viability} = \text{DesirePull} - \text{EffectiveResistance}$$

- Under normal conditions ($\text{Urgency} = 1.0$), moral resistance holds firm at $40.0 - 60.0$, strictly suppressing theft.
- Under critical biological desperation ($\text{Hunger} \ge 85.0 \implies \text{Urgency} \approx 3.5$), the quadratic denominator ($\text{Urgency}^2 \approx 12.25$) reduces moral resistance by over **90%**, naturally opening transgressive options.

---

## 4. Multi-Channel Information & Epistemic Propagation

The simulation rejects omniscient data queries. Knowledge propagates through physical mediums:
1. **Civic Notice Boards**: Public municipal bulletins, ordinances, and court verdicts posted in central plazas and town halls. Agents scan boards during daily circulation with a 24-hour reading cooldown.
2. **Dyadic Gossip & Word-of-Mouth**: Co-located agents in taverns, markets, and workshops exchange rumors and opinions based on relational priority.
3. **Inscribed Epistemic Atoms**: Physical artifacts (ledgers, books, notes, forensic clues) carry knowledge in the spatial world.
4. **Memory Dynamics**: Epistemic traces in working memory decay exponentially with a half-life of 4,320 ticks (3 days), but can be rekindled through associative priming cues or permanent emotional anchors ($\text{EmotionalRelevance} \ge 1.8$).

---

## 5. Institutional Economy & Exemptions

1. **Non-Commercial Institution Financing (Member Levies & Tithes)**:
   - Non-commercial community institutions (churches, mutual aid lodges) do not sell commodities. Instead, their operating budgets derive from **regular member dues, tithes, and alms levies** paid by participating citizens.
   - The Parish Charitable Alms Box collects dues from community members, which in turn pays the priest's living stipend during sacred service shifts without minting unbacked fiat currency.
2. **Tax & Levy Exemptions**:
   - Buildings of category `SACRED` (chapels, monasteries) and `CIVIC` (town halls) are strictly exempt from commercial market stall fees and property levies.
   - Resident clergy are exempt from secular municipal income taxes and daily homestead upkeep levies.

---

## 6. Courtship Rendezvous & Spatial Seclusion

Consensual private intimacy evaluates spatial privacy across 4 distinct tiers:
1. **Home Bedchamber**: Private bedroom owned or resided in by either partner.
2. **Short-Term Inn Loft Rental**: Unhoused couples with modest coin pay 0.50g closed-loop to rent private quarters at the tavern.
3. **Secluded Unowned Spots**: Penniless couples retreat to quiet haylofts, meadows, or cellars, receiving a clandestine passion thrill (+8.0 passion).
4. **Clandestine Indoor Trespassing**: Driven by acute passion, lovers slip into unoccupied workshops after hours, risking detection and incurring guilt (+18.0) and stress (+12.0).

---

## 7. Aspirational Career Mobility & Vocational Study

Job postings requiring skills higher than an agent's current competence are not discarded:
- An ambitious citizen registers an **Aspirational Career Deficit**.
- During off-shift hours, this ambition primes thoughts of self-improvement, motivating the agent to:
  - **Observe Master Artisans** (+1.25 skill/hour) while co-located at work.
  - **Perform Bench Practice** (+0.90 skill/hour) at community workbenches.
  - **Conduct Vocational Study** (+0.75 skill/hour) with inscribed trade manuals.
- Once the skill deficit is closed, the agent qualifies and applies for the position.

---

## 8. Emotional Homeostasis & The Confession Loop

1. **Loneliness Coupling**: When social needs fall below 25.0, loneliness accumulates continuously:
   $$\Delta \text{Loneliness} = \left(\frac{25.0 - \text{Needs}_{\text{social}}}{25.0}\right) \cdot 0.008 \cdot \Delta t$$
2. **Transgressive Remorse**: Committing transgressive acts (theft, trespassing) spikes **Guilt (+20.0 to +35.0)**.
3. **Spiritual Absolution**: High guilt primes remorseful thoughts in attentional working memory, guiding the citizen to visit St. Jude's Chapel, confess to Father Barnaby, and receive formal absolution, relieving guilt (-35.0) and donating alms to the parish chest.
