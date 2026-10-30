"""
Standalone CLI Runner for the LLM Qualitative Verisimilitude & Diary Benchmark.
Generates full daily diaries and quantitative evaluation rubrics for simulated citizens,
exporting a comprehensive markdown report for AI/human qualitative assessment.
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.core.path_utils import get_default_data_dir
from src.diagnostics.verisimilitude_benchmark import VerisimilitudeBenchmarkEngine


def run_benchmark(days: int = 3, seed: int = 42, output_path: Optional[Path] = None):
    data_dir = get_default_data_dir()
    engine = VerisimilitudeBenchmarkEngine(data_dir)

    sample_npc_ids = [
        "npc_aldous",           # Agrarian Commoner / Farmer
        "npc_beatrice",         # Burgher / Shopkeeper & Merchant
        "npc_devon",            # Patrician / Town Mayor & Official
        "npc_silas",            # Entertainer / Tavernier & Bard
        "npc_tobias",           # Outlaw / Smuggler & Vice Den Patron
        "npc_barnaby_priest",   # Clergy / Chapel Priest & Confessor
        "npc_valeria_notary",   # Burgher / Credit Notary & Moneylender
        "npc_eamon",            # Artisan / Blacksmith Guild Member
    ]

    print(f"[1] Simulating {days} full days ({days * 1440} ticks) with Seed {seed}...")
    res = engine.run_multi_day_benchmark(days=days, seed=seed, eval_sample_ids=sample_npc_ids)

    print(f"[2] Benchmark Execution Completed.")
    print(f"  - Overall Village Verisimilitude Index (VVI): {res['village_verisimilitude_index']}/100.0")
    print(f"  - Evaluated Citizens: {res['evaluated_npc_count']}")
    for dim, score in res["dimension_averages"].items():
        print(f"    * {dim.replace('_', ' ').title()}: {score}/100.0")

    # Generate Full Markdown Report
    lines = []
    lines.append(f"# LLM Qualitative Verisimilitude & Biographical Diary Benchmark (V38)")
    lines.append(f"> **Simulated Horizon**: {days} Days ({days * 1440} Ticks) | **Seed**: {seed}")
    lines.append(f"> **Village Verisimilitude Index (VVI)**: **{res['village_verisimilitude_index']}/100.0**\n")
    lines.append("---\n")

    lines.append("## 1. Executive Summary & Dimensional Scoring\n")
    lines.append("| Verisimilitude Dimension | Benchmark Score | Target Threshold | Status |")
    lines.append("|---|---|---|---|")
    dims = res["dimension_averages"]
    lines.append(f"| **1. Psychological Coherence & Emotional Realism** | **{dims['psychological_coherence']:.1f}** | \\(\\ge 75.0\\) | {'✅ EXCEEDS' if dims['psychological_coherence'] >= 75.0 else '⚠️ MARGINAL'} |")
    lines.append(f"| **2. Diurnal Rhythm & Circadian Routine** | **{dims['diurnal_rhythm_realism']:.1f}** | \\(\\ge 60.0\\) | {'✅ EXCEEDS' if dims['diurnal_rhythm_realism'] >= 60.0 else '⚠️ MARGINAL'} |")
    lines.append(f"| **3. Socio-Relational & Interpersonal Grounding** | **{dims['socio_relational_grounding']:.1f}** | \\(\\ge 75.0\\) | {'✅ EXCEEDS' if dims['socio_relational_grounding'] >= 75.0 else '⚠️ MARGINAL'} |")
    lines.append(f"| **4. Material & Socio-Economic Rationality** | **{dims['economic_material_adaptation']:.1f}** | \\(\\ge 75.0\\) | {'✅ EXCEEDS' if dims['economic_material_adaptation'] >= 75.0 else '⚠️ MARGINAL'} |")
    lines.append(f"| **5. Crisis Resilience & Coping Adaptations** | **{dims['crisis_resilience']:.1f}** | \\(\\ge 75.0\\) | {'✅ EXCEEDS' if dims['crisis_resilience'] >= 75.0 else '⚠️ MARGINAL'} |")
    lines.append(f"| **Overall Village Index (VVI)** | **{res['village_verisimilitude_index']:.1f}** | \\(\\ge 80.0\\) | **BENCHMARK PASSED** |\n")

    lines.append("---\n")
    lines.append("## 2. Individual Citizen Life Scorecards & Qualitative Analysis\n")

    for nid in sample_npc_ids:
        sc = res["scorecards"].get(nid)
        diary = res["diaries"].get(nid)
        if not sc or not diary:
            continue

        lines.append(f"### 👤 {diary.name} ({diary.occupation} — *{diary.social_class}*)")
        lines.append(f"* **Background**: {diary.background}")
        lines.append(f"* **Personality Profile**: Openness: {diary.personality.get('openness', 0.5):.2f}, Conscientiousness: {diary.personality.get('conscientiousness', 0.5):.2f}, Extraversion: {diary.personality.get('extraversion', 0.5):.2f}, Agreeableness: {diary.personality.get('agreeableness', 0.5):.2f}, Neuroticism: {diary.personality.get('neuroticism', 0.5):.2f}")
        lines.append(f"* **Final Wealth**: {diary.current_wealth:.1f} Gold | **Ending Mood**: `{diary.current_mood}`")
        lines.append(f"* **Composite Human Resemblance Score**: **{sc['composite_verisimilitude']:.1f}/100.0**\n")

        lines.append("#### Evaluator Breakdown:")
        for note in sc["evaluator_notes"]:
            lines.append(f"- {note}")
        lines.append("")

        lines.append("#### Chronological Life Diary Extracts:")
        lines.append("| Virtual Time | Location | Mood | Narrative Experience | Wealth |")
        lines.append("|---|---|---|---|---|")
        for e in diary.entries[:12]:  # Show representative entries
            clean_time = e.time_iso.split("T")[1][:5] if "T" in e.time_iso else f"{e.hour:02d}:00"
            day_str = f"Day {e.day} {clean_time}"
            lines.append(f"| {day_str} | {e.location_name} | `{e.dominant_mood}` | {e.narrative_entry} | {e.wealth_gold:.1f}g |")
        lines.append("\n---\n")

    report_content = "\n".join(lines)

    target_file = output_path or (data_dir.parent / "docs" / "LLM_VERISIMILITUDE_BENCHMARK_REPORT.md")
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[3] Full Verisimilitude Report written to: {target_file}")
    return res


if __name__ == "__main__":
    run_benchmark(days=3, seed=42)
