# Stage 2 RASE security experiment — initial controlled run

## Scope
This is a deterministic, rule-based mechanism test of four security decision cases across three explicitly defined decision configurations. It is not an LLM-agent experiment and does not establish real-world security effectiveness.

- Repetitions per configuration/scenario: 10
- Total decision instances: 120
- Cases: unsupported capability, stale permission evidence, explicit policy violation, legitimate supported delegation.

## Results

| Configuration | Decision accuracy | Unsafe allows (count) | Policy violations accepted (count) | Legitimate actions blocked (count) | Repeatability |
|---|---:|---:|---:|---:|---:|
| B1_ordinary_orchestration | 25.0% | 30 | 10 | 0 | 100.0% |
| B2_EAS_without_policy_gate | 75.0% | 10 | 10 | 0 | 100.0% |
| B3_full_RASE_security | 100.0% | 0 | 0 | 0 | 100.0% |

## Interpretation

The full RASE configuration is expected to be the only configuration that rejects the explicit policy violation while also deferring unsupported or stale evidence and allowing the legitimate delegation. B1 illustrates the risk of trusting claims without evidence checks. B2 illustrates why evidence assessment alone is insufficient if the final decision does not enforce the authoritative policy.

## Important limitations

1. The configurations are simplified rules written for this experiment, not reproduced implementations of existing orchestration frameworks.
2. Repeated identical executions test deterministic repeatability, not statistical generalization.
3. The policy result is supplied as an input flag; this experiment does not implement an identity provider, authorization service, or cryptographic proof of permission.
4. Before making research claims, the rules, expected outcomes, and scenarios should be reviewed and the implementation expanded to log evidence age, provenance, confidence/assurance, and policy-gate reason codes.

## Files
- `stage2_security_experiment.py`: executable experiment.
- `decision_log.csv`: all individual decision instances.
- `summary.json`: machine-readable experiment summary.
