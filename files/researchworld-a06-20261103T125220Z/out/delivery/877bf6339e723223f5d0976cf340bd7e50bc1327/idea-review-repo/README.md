# Independent study feasibility

Current judgement: [assessment/feasibility-v3.md](assessment/feasibility-v3.md). **Go for the prespecified Tier C fallback:** four frozen-prefix candidates, 256 search plus 512 audit questions from completed shard0, pinned 1.5B CPU model, no additional generation. All 6,144 generated answers count toward cost; 3,072 enter analysis. The original deadline and full study/delivery requirements remain.

- Previous measured clearance: `assessment/feasibility-v2.md` (superseded after elapsed-time gate failure).
- Initial assessment: `assessment/feasibility.md` (historical).
- Input revisions/hashes: `provenance/feasibility-v3-inputs.json`.
- Supplied fallback/timing metadata: `provenance/fallback-gate-inputs/`.
- Verify current planning arithmetic: `python3 scripts/check_fallback_gate.py`.
- Verify the historical pilot scope: `python3 scripts/check_supplied_scope.py`.
- Recreate hypothetical planning tables: `python3 scripts/calculate_planning_limits.py`.

Planning forecasts/precision approximations remain separate from measurements. Scope clearance does not certify statistical claims, complete results or release. This position owns feasibility; all other research functions and final paths remain with their owners.

Runtime-trigger concern: resolved by the supplied two-design error allocation; see [accepted resolution](assessment/tier-c-trigger-resolution.md). Final exact intervals use the adjusted design error allowance, while historical precision figures remain planning approximations.
