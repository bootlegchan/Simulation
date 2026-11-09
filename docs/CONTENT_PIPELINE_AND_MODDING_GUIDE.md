# Content Creation Pipeline & Architectural Modding Guide (v145)

> **TARGET AUDIENCE**: AI Coding Agents, Systems Engineers, and Content Creators.  
> **STANDARD**: 100% Declarative, Self-Contained Content Packs with Zero Python Code Coupling & Pure Continuous Field Dynamics.  
> **ENGINE**: Stage-Pipelined Microkernel Social Simulation Engine.

---

## 1. Core Operating Principles & Invariants

1. **Zero-Code Coupling Principle**:
   - Never add content (new items, recipes, occupations, buildings, diseases, substances, factions, decrees, recreation games, penal sentences, dilemmas, or life goals) by creating hardcoded Python `Enum` values or `if/elif` string branches in engine source files (`src/`).
   - All content additions must be expressed purely through declarative JSON files located in `data/settings/` or modular content packs in `data/packs/<pack_id>/`.

2. **Hard Invariant: Absolute Prohibition of Implicit Finite State Machines (FSMs)**:
   - **No Discrete Phase State Enums as Decision Controllers**: Do not use discrete phase enums (e.g. `DailyRhythmPhase`, `CitizenState`) to gate or switch agent utilities. Phase and rhythm classifications may exist strictly as *diagnostic/read-only observers*, never as utility override switches.
   - **No Artificial Utility Cliffs or Forced Overrides**: Never inject artificial step-function overrides (e.g. `env_mods["rest"] = +90.0`, `chosen_drive = "rest"`). All actions must be sampled via continuous multinomial logit from smooth utility equations.
   - **Pure Continuous Field Dynamics**: Sleep pressure, vocational alignment, hunger urgency, and social interest must emerge from smooth, continuous mathematical gradients (power laws, S-curves, Borbély Process S & Process C models).
   - **Zero Spatial Teleportation**: When an agent accepts a job posting, shifts tasks, or heads home to rest, they must physically navigate room-by-room along the `SpatialGraph`. Instantaneous room reassignment (`npc.location_id = target_room`) without traversal is strictly prohibited.
   - **Smooth Somatic Urgency over Step Preemptions**: Biological safety imperatives must out-compete scheduled labor via exponential somatic utility curves rather than hardcoded `if hunger >= 85: force_action` interrupt switches.

3. **Self-Contained Content Pack Architecture**:
   - Each gameplay expansion, trade guild, district, or seasonal event lives inside its own isolated folder: `data/packs/<pack_id>/`.
   - Packs are self-describing via `pack.json`. Removing a feature from the game is as simple as deleting or disabling (`"enabled": false`) its pack folder.

4. **Topological Dependency Ordering**:
   - Packs declare explicit dependencies in `pack.json` (e.g. `"dependencies": ["base_oakwood"]`).
   - The engine automatically resolves and loads packs in strict topological order using Kahn's algorithm. Circular dependencies and missing dependencies are caught and reported during initialization.

5. **Non-Destructive Overrides (RFC 7396 JSON Merge Patch)**:
   - When modifying existing game content (adjusting item prices, tuning NPC traits, changing building rooms), packs use `patches.json` or `patches/*.json` using the RFC 7396 merge patch standard.
   - Never edit base scenario files directly when creating modular expansions.

6. **Bidirectional Spatial Integrity**:
   - Doorway connections between rooms are automatically linked reciprocally by `SpatialGraph` and `WeightedNodeTopology`.
   - All rooms in a settlement must possess a navigable path to a public circulation hub (Market Plaza / Town Square).

7. **Pre-Flight Validation & Regression Safety**:
   - Every pack must pass the automated referential linter (`python3 lint_content.py --strict`).
   - Every economic pack must pass the headless balance regression harness (`python3 test_pack_balance.py --pack <pack_id> --days 5`), verifying closed-loop wealth conservation and zero starvation deaths.
   - All automated unit and longitudinal simulation tests (`python3 run_tests.py --all`) must pass with 100% success rate.

---

## 2. Directory Structure of a Content Pack

A content pack folder (`data/packs/<pack_id>/`) supports modular asset manifests:

```text
data/packs/<pack_id>/
├── pack.json             # Manifest declaring ID, name, version, and dependencies (REQUIRED)
├── items.json            # Custom commodities, tools, luxuries, containers, consumables
├── recipes.json          # Crafting recipes, inputs, outputs, and workstation capabilities
├── objects.json          # Interactive objects, furniture, workbenches, affordance tools
├── npcs.json             # Profiled agent character sheets, traits, and starting resources
├── buildings.json        # Architectural structures, rooms, and doorway portals
├── occupations.json      # Vocational profiles, primary skills, hazard rates, shift windows
├── supply_chains.json    # Multi-stage production chains and continuous scarcity curves
├── factions.json         # Political/guild factions with platforms and member criteria
├── decrees.json          # Municipal ordinances, curfews, and sumptuary price caps
├── drives.json           # Declarative custom behavioral drives and action strategies
├── attractors.json       # Ambient spatial affordance fields (aromas, warmth, music, shadows)
├── diseases.json         # Custom pathogens, transmission vectors, and curative items
├── substances.json       # Custom narcotics, tonics, tolerance rates, and withdrawal timelines
├── recreation_games.json # Custom leisure contests, sports, evaluated attributes, and wagers
├── penal_sentences.json  # Custom judicial sentences, pillory durations, and penal labor
├── dilemmas.json         # Custom moral dilemma crises and therapeutic coping mechanisms
├── life_goals.json       # Custom long-term life aspirations and utility steering biases
├── romance_bonds.json    # Custom romantic/spousal bonds and relationship agreements
├── relationship_stages.json # Custom relationship stage definitions and agreement models
├── social_clubs.json     # Custom social societies, group norms, and meeting halls
├── fraternal_aid.json    # Custom mutual aid lodges, dues, and sickness benefits
├── resource_nodes.json   # Custom regional harvesting nodes (timber, stone, clay, herbs)
├── soil_plots.json       # Custom agricultural soil fertility and crop rotation plots
├── gatherings.json       # Custom prolonged collective festivals, conclaves, and tournaments
├── commitments.json      # Custom bilateral social commitment contract specifications
├── lawsuits.json         # Custom courtroom lawsuits, filing fees, and judicial sentences
└── patches.json          # RFC 7396 delta patches modifying existing base data
```

---

## 3. Continuous Field Equations (Mathematical Reference)

### 3.1 Homeostatic Sleep Pressure (Process S)
$$\text{Fatigue} = \max(0.0, 100.0 - \text{Energy})$$
$$U_{\text{rest}} = 0.25 \cdot \text{Fatigue} + 6.0 \cdot \left(\frac{\text{Fatigue}}{22.0}\right)^{2.3} + \text{InertiaBonus}$$
*At $\text{Energy} = 90$, $U_{\text{rest}} \approx 3.5$. At $\text{Energy} = 20$, $U_{\text{rest}} \approx 140.5$.*

### 3.2 Continuous Vocational Alignment
$$\Phi_{\text{work}}(t) = \begin{cases} 
1.0 & \text{if within shift window} \\
0.75 \cdot \text{Willingness} & \text{if within overtime window and rested} \\
0.40 & \text{if } \le 1.5\text{h before shift start (commute pull)} \\
0.05 + 0.25 \cdot \text{PovertyFactor} & \text{otherwise}
\end{cases}$$

$$\Delta U_{\text{work}} = (\Phi_{\text{work}}(t) - 0.5) \cdot 60.0 \cdot \left(\frac{\text{Energy}}{100.0}\right)$$

### 3.3 Dynamic S-Curve Metabolic Hunger Decay
$$\text{Exertion } E = (0.70 \cdot P \cdot \text{WorkFactor}) + (0.30 \cdot M)$$
$$\text{Decay Rate} = \text{BaseRate} \cdot E^{1.15} \quad (\text{clamped between } 0.018 \text{ and } 0.180/\text{tick})$$
- Rest / Sleep: $0.018/\text{tick}$.
- Awake Sedentary: $0.031/\text{tick}$.
- Heavy Labor: $0.074 - 0.097/\text{tick}$.

---

## 4. Multi-Channel Information Propagation

The simulation avoids omniscient agent querying by routing information through 5 physical networks:
1. **Civic Notice Boards**: Public vouchers, decrees, ordinances posted in squares and halls.
2. **Community Gossip**: Peer small talk in taverns diffusing rumors and prices.
3. **Justice Reporting**: Citizen incident reports to watchmen triggering investigative alerts.
4. **Shadow Network**: Backroom whispers and chalk marks appraising wealthy targets and contraband contracts.
5. **Vocational Study**: Workstation apprentice instruction transferring craft skills.
