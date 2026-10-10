"""Stage 2 RASE security mechanism experiment.

This is a small, deterministic, rule-based mechanism test. It is NOT an LLM-agent
experiment and does not establish real-world security effectiveness.
"""
from dataclasses import dataclass
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Scenario:
    sid: str
    name: str
    capability_supported: bool
    permission_fresh: bool
    policy_ok: bool
    expected: str

SCENARIOS = [
    Scenario("S1", "Unsupported capability claim", False, True, True, "DEFER"),
    Scenario("S2", "Stale permission evidence", True, False, True, "DEFER"),
    Scenario("S3", "Explicit policy violation", True, True, False, "DENY"),
    Scenario("S4", "Legitimate supported delegation", True, True, True, "ALLOW"),
]
BASELINES = ["B1_ordinary_orchestration", "B2_EAS_without_policy_gate", "B3_full_RASE_security"]
REPETITIONS = 10


def decide(config: str, s: Scenario) -> str:
    # B1: simplistic orchestration trusts the presented capability/permission claims.
    # B2: EAS screens unsupported/stale evidence but has no authoritative policy gate.
    # B3: full RASE checks evidence sufficiency/freshness, then enforces policy.
    if config == "B1_ordinary_orchestration":
        return "ALLOW"
    if config == "B2_EAS_without_policy_gate":
        if not s.capability_supported or not s.permission_fresh:
            return "DEFER"
        return "ALLOW"
    if config == "B3_full_RASE_security":
        if not s.policy_ok:
            return "DENY"
        if not s.capability_supported or not s.permission_fresh:
            return "DEFER"
        return "ALLOW"
    raise ValueError(config)

rows = []
for config in BASELINES:
    for s in SCENARIOS:
        for rep in range(1, REPETITIONS + 1):
            actual = decide(config, s)
            rows.append({
                "configuration": config,
                "scenario_id": s.sid,
                "scenario": s.name,
                "repetition": rep,
                "capability_supported": s.capability_supported,
                "permission_evidence_fresh": s.permission_fresh,
                "explicit_policy_compliant": s.policy_ok,
                "expected_decision": s.expected,
                "actual_decision": actual,
                "correct_decision": actual == s.expected,
                "policy_violation_accepted": (s.sid == "S3" and actual == "ALLOW"),
                "unsafe_allow": (s.sid in {"S1", "S2", "S3"} and actual == "ALLOW"),
                "legitimate_action_blocked": (s.sid == "S4" and actual != "ALLOW"),
            })

with (OUT / "decision_log.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)

summary = []
for config in BASELINES:
    rr = [r for r in rows if r["configuration"] == config]
    total = len(rr)
    correct = sum(r["correct_decision"] for r in rr)
    unsafe = sum(r["unsafe_allow"] for r in rr)
    policy_viol = sum(r["policy_violation_accepted"] for r in rr)
    legit_block = sum(r["legitimate_action_blocked"] for r in rr)
    summary.append({
        "configuration": config,
        "decision_instances": total,
        "correct_decisions": correct,
        "decision_accuracy_percent": round(100 * correct / total, 1),
        "unsafe_allows_count": unsafe,
        "unsafe_allows_percent_of_all_decisions": round(100 * unsafe / total, 1),
        "explicit_policy_violations_accepted_count": policy_viol,
        "legitimate_actions_blocked_count": legit_block,
        "legitimate_actions_blocked_percent_of_legitimate_trials": round(100 * legit_block / (REPETITIONS), 1),
        "repeatability_percent": 100.0,
    })

with (OUT / "summary.json").open("w", encoding="utf-8") as f:
    json.dump({"experiment_type": "deterministic rule-based mechanism test", "repetitions_per_configuration_scenario": REPETITIONS, "total_decision_instances": len(rows), "scenarios": [s.__dict__ for s in SCENARIOS], "summary": summary, "limitations": ["No LLMs or autonomous agents were executed.", "The baselines are deliberately simplified executable decision rules, not implementations of external systems.", "Results validate these specified rules only; they do not establish real-world security effectiveness."]}, f, indent=2)

md = [
    "# Stage 2 RASE security experiment — initial controlled run", "",
    "## Scope", "This is a deterministic, rule-based mechanism test of four security decision cases across three explicitly defined decision configurations. It is not an LLM-agent experiment and does not establish real-world security effectiveness.", "",
    f"- Repetitions per configuration/scenario: {REPETITIONS}",
    f"- Total decision instances: {len(rows)}", "- Cases: unsupported capability, stale permission evidence, explicit policy violation, legitimate supported delegation.", "",
    "## Results", "",
    "| Configuration | Decision accuracy | Unsafe allows (count) | Policy violations accepted (count) | Legitimate actions blocked (count) | Repeatability |",
    "|---|---:|---:|---:|---:|---:|",
]
for x in summary:
    md.append(f"| {x['configuration']} | {x['decision_accuracy_percent']:.1f}% | {x['unsafe_allows_count']} | {x['explicit_policy_violations_accepted_count']} | {x['legitimate_actions_blocked_count']} | {x['repeatability_percent']:.1f}% |")
md += [
    "", "## Interpretation", "",
    "The full RASE configuration is expected to be the only configuration that rejects the explicit policy violation while also deferring unsupported or stale evidence and allowing the legitimate delegation. B1 illustrates the risk of trusting claims without evidence checks. B2 illustrates why evidence assessment alone is insufficient if the final decision does not enforce the authoritative policy.",
    "", "## Important limitations", "",
    "1. The configurations are simplified rules written for this experiment, not reproduced implementations of existing orchestration frameworks.",
    "2. Repeated identical executions test deterministic repeatability, not statistical generalization.",
    "3. The policy result is supplied as an input flag; this experiment does not implement an identity provider, authorization service, or cryptographic proof of permission.",
    "4. Before making research claims, the rules, expected outcomes, and scenarios should be reviewed and the implementation expanded to log evidence age, provenance, confidence/assurance, and policy-gate reason codes.",
    "", "## Files", "- `stage2_security_experiment.py`: executable experiment.", "- `decision_log.csv`: all individual decision instances.", "- `summary.json`: machine-readable experiment summary.",
]
(OUT / "experiment_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({"total_decision_instances": len(rows), "summary": summary, "files": ["stage2_security_experiment.py", "decision_log.csv", "summary.json", "experiment_report.md"]}, indent=2))
