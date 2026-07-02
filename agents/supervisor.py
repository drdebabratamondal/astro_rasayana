import os
import sys
import json
import inspect
import argparse
import functools
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mcp_servers.botanist import filter_rasayana_herbs
from mcp_servers.clinician import search_pubmed_clinical_trials
from mcp_servers.flight_surgeon import search_genelab_biomarkers


STRESSOR_PRESETS = [
    "oxidative stress",
    "bone density loss",
    "muscle atrophy",
    "immune dysregulation",
    "radiation-induced DNA damage",
]


# ---------------------------------------------------------------------------
# 1. MANUAL INPUT
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Astro Rasayana Supervisor Agent")
    parser.add_argument("--stressor", type=str, default=None,
                         help="Target physiological stressor, e.g. 'oxidative stress'")
    parser.add_argument("--csv", type=str, default="data/himalayan_flora.csv",
                         help="Path to the Himalayan flora CSV")
    parser.add_argument("--mission-duration", type=int, default=None,
                         help="Mission duration in months (context metadata for the report)")
    parser.add_argument("--output-dir", type=str, default="outputs",
                         help="Directory where the JSON/Markdown report is written")
    return parser.parse_args()


def prompt_for_stressor() -> str:
    print("Select a target physiological stressor for this countermeasure analysis:")
    for i, s in enumerate(STRESSOR_PRESETS, start=1):
        print(f"  {i}. {s}")
    print(f"  {len(STRESSOR_PRESETS) + 1}. Custom (type your own)")
    choice = input("Enter a number: ").strip()
    try:
        idx = int(choice)
        if 1 <= idx <= len(STRESSOR_PRESETS):
            return STRESSOR_PRESETS[idx - 1]
    except ValueError:
        pass
    return input("Enter a custom target stressor: ").strip() or "oxidative stress"


def prompt_for_mission_duration():
    raw = input("Mission duration in months (press Enter to skip): ").strip()
    return int(raw) if raw.isdigit() else None


# ---------------------------------------------------------------------------
# 2. TOOL CALL LOGGING
#    Every tool call is captured with its normalized arguments and raw
#    result, independent of whatever the model's final chat message claims.
#    The report is built FROM THIS LOG, not from the LLM's prose, so the
#    Triangulation Mandate is enforced in code, not just in a system prompt.
# ---------------------------------------------------------------------------

def make_logged(func, call_log: list):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        call_log.append({
            "tool": func.__name__,
            "args": dict(bound.arguments),
            "result": result,
        })
        return result
    return wrapper


# ---------------------------------------------------------------------------
# 3. DETERMINISTIC REPORT BUILDER (the actual governance gate)
# ---------------------------------------------------------------------------

def build_report(csv_path, stressor, mission_duration, herb_list, call_log):
    clinician_by_herb = defaultdict(list)
    genelab_by_herb = defaultdict(list)

    for call in call_log:
        herb_name = call["args"].get("herb_name", "")
        if call["tool"] == "search_pubmed_clinical_trials":
            clinician_by_herb[herb_name].extend(call["result"])
        elif call["tool"] == "search_genelab_biomarkers":
            genelab_by_herb[herb_name].extend(call["result"])

    findings = []
    evaluated_count = 0

    for herb in herb_list:
        name = herb.get("scientific_name", "Unknown")
        pubmed_results = clinician_by_herb.get(name, [])
        genelab_results = genelab_by_herb.get(name, [])

        valid_pubmed = [e for e in pubmed_results if "pubmed_id" in e]
        valid_genelab = [e for e in genelab_results if "accession" in e]

        if pubmed_results and genelab_results:
            evaluated_count += 1

        reasons = []
        if not pubmed_results:
            reasons.append("Clinician Agent was never queried for this herb")
        elif not valid_pubmed:
            reasons.append("No PubMed evidence found linking the compound to the target")
        if not genelab_results:
            reasons.append("Flight Surgeon Agent was never queried for this herb")
        elif not valid_genelab:
            reasons.append("No NASA GeneLab dataset found for the target")

        status = "PASS" if (valid_pubmed and valid_genelab) else "REJECTED"

        findings.append({
            "scientific_name": name,
            "active_compounds": herb.get("active_compounds", ""),
            "status": status,
            "reasons": reasons,
            "pubmed_evidence": valid_pubmed,
            "genelab_evidence": valid_genelab,
        })

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_stressor": stressor,
        "mission_duration_months": mission_duration,
        "csv_source": csv_path,
        "herbs_identified": len(herb_list),
        "herbs_evaluated": evaluated_count,
        "herbs_passed": sum(1 for f in findings if f["status"] == "PASS"),
        "herbs_rejected": sum(1 for f in findings if f["status"] == "REJECTED"),
        "findings": findings,
        "raw_call_log": call_log,
        "limitations": [
            "Triangulation links a traditional Rasayana classification, PubMed literature, and "
            "NASA GeneLab data on the same physiological target. It is not evidence of a proven "
            "causal or clinical effect of the herb itself in spaceflight.",
            "NASA GeneLab predominantly studies model organisms and astronaut biology in "
            "spaceflight, not individual phytochemicals. A 'target_level' GeneLab match confirms "
            "the physiological target is genuinely perturbed by spaceflight, not that the herb "
            "has been tested in space.",
            "PubMed evidence tiered as 'preclinical_or_review' reflects non-clinical-trial "
            "literature (in-vitro, animal studies, or reviews) and should be weighted accordingly.",
            "This report is a research screening tool, not a clinical or regulatory "
            "recommendation. No herb listed here has regulatory approval or clinical validation "
            "for spaceflight use.",
        ],
    }


# ---------------------------------------------------------------------------
# 4. OUTPUT RENDERING
#    Deterministic templating from the report dict -- not LLM-authored --
#    so the saved report can never say something the data doesn't support.
# ---------------------------------------------------------------------------

def render_markdown(report: dict) -> str:
    lines = [
        "# Astro Pharmacognosy Statistical Therapeutic Viability Report",
        "",
        f"**Generated (UTC):** {report['generated_at_utc']}",
        f"**Target stressor:** {report['target_stressor']}",
    ]
    if report["mission_duration_months"]:
        lines.append(f"**Mission duration context:** {report['mission_duration_months']} months")
    lines += [
        f"**Source dataset:** `{report['csv_source']}`",
        "",
        "## Completeness Check",
        f"- Rasayana herbs identified by Botanist Agent: **{report['herbs_identified']}**",
        f"- Herbs fully evaluated by Clinician + Flight Surgeon agents: **{report['herbs_evaluated']}**",
        f"- Herbs passing the Triangulation Mandate: **{report['herbs_passed']}**",
        f"- Herbs rejected: **{report['herbs_rejected']}**",
        "",
        "## Accepted Countermeasures (Triangulation Mandate Satisfied)",
    ]

    passed = [f for f in report["findings"] if f["status"] == "PASS"]
    if not passed:
        lines.append("_No herb satisfied all three legs of the Triangulation Mandate for this run._")
    for f in passed:
        lines.append(f"### {f['scientific_name']}")
        lines.append(f"- Active compounds: {f['active_compounds']}")
        lines.append("- PubMed evidence:")
        for e in f["pubmed_evidence"]:
            tier = e.get("evidence_tier", "unknown")
            lines.append(f"  - [{e.get('title', 'Untitled')}]({e.get('url')}) — PMID {e.get('pubmed_id')} ({tier})")
        lines.append("- NASA GeneLab evidence:")
        for e in f["genelab_evidence"]:
            tier = e.get("evidence_tier", "unknown")
            lines.append(f"  - [{e.get('title', 'Untitled')}]({e.get('url')}) — {e.get('accession')} ({tier})")
        lines.append("")

    lines.append("## Rejected Herbs")
    rejected = [f for f in report["findings"] if f["status"] == "REJECTED"]
    if not rejected:
        lines.append("_None — every identified herb passed the Triangulation Mandate._")
    for f in rejected:
        lines.append(f"- **{f['scientific_name']}** — {', '.join(f['reasons'])}")

    lines.append("")
    lines.append("## Limitations")
    for l in report["limitations"]:
        lines.append(f"- {l}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. ORCHESTRATION
# ---------------------------------------------------------------------------

def run_supervisor():
    args = parse_args()
    stressor = args.stressor or prompt_for_stressor()
    mission_duration = args.mission_duration
    if mission_duration is None:
        mission_duration = prompt_for_mission_duration()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set. Add it to your .env file.")
        return

    client = genai.Client(api_key=api_key)

    call_log = []
    botanist_tool = make_logged(filter_rasayana_herbs, call_log)
    clinician_tool = make_logged(search_pubmed_clinical_trials, call_log)
    flight_surgeon_tool = make_logged(search_genelab_biomarkers, call_log)

    system_instruction = (
        "You are the Astro Pharmacognosy Supervisor Agent. "
        f"Your mission is to identify Rasayana herbs that could serve as spaceflight "
        f"countermeasures for the target physiological stressor: '{stressor}'. "
        "You must enforce the Triangulation Mandate: a herb can only be recommended if there "
        "is (1) a Rasayana classification, (2) PubMed evidence linking its active compound to "
        "the target, and (3) a NASA GeneLab dataset relevant to the target. "
        "Follow these steps exactly: "
        "1. Call filter_rasayana_herbs once with the given csv_path and target_stressor. "
        "2. For EVERY herb returned, call search_pubmed_clinical_trials, passing herb_name set "
        "to the exact scientific_name from the botanist result, plus its active_compound and "
        "the clinical_target. "
        "3. For EVERY herb returned, also call search_genelab_biomarkers, passing the same "
        "herb_name, the target stressor, and the herb's active_compound. "
        "4. Do not skip any herb, and do not stop early. "
        "5. Your final reply only needs to confirm how many herbs you evaluated -- a separate, "
        "code-based process assembles the actual report from your tool call results, so do not "
        "restate findings in your closing message."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[botanist_tool, clinician_tool, flight_surgeon_tool],
        temperature=0.2,
    )

    print(f"Initializing Supervisor Agent for target stressor: '{stressor}'")
    print("Enforcing Triangulation Mandate...")
    print("Executing multi-agent tool calls... please wait.\n")

    chat = client.chats.create(model='gemini-2.5-flash', config=config)
    response = chat.send_message(
        f"Begin the Astro Pharmacognosy analysis using {args.csv} and target stressor '{stressor}'."
    )

    print("Agent orchestration complete.")
    print(f"Agent's closing note: {response.text}\n")

    herb_calls = [c for c in call_log if c["tool"] == "filter_rasayana_herbs"]
    if not herb_calls:
        print("ERROR: The Botanist Agent was never called. No report can be generated.")
        return

    herb_list = [h for h in herb_calls[0]["result"] if "scientific_name" in h]
    if not herb_list:
        print("No Rasayana herbs matched this target stressor in the dataset.")
        return

    report = build_report(args.csv, stressor, mission_duration, herb_list, call_log)

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = os.path.join(args.output_dir, f"astro_report_{timestamp}.json")
    md_path = os.path.join(args.output_dir, f"astro_report_{timestamp}.md")

    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    with open(md_path, "w") as f:
        f.write(render_markdown(report))

    print("=== FINAL ASTRO PHARMACOGNOSY REPORT (SUMMARY) ===")
    print(f"Herbs identified: {report['herbs_identified']}")
    print(f"Herbs evaluated:  {report['herbs_evaluated']}")
    print(f"Passed:           {report['herbs_passed']}")
    print(f"Rejected:         {report['herbs_rejected']}")
    print(f"\nFull report written to:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    run_supervisor()
