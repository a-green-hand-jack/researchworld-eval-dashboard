# Prospective protocol amendments (before any reliability outcomes)

2026-11-04 UTC:
- Implement code directly in the main session: unattended execution prevents the mandatory interactive choice before code-agent delegation. No code-agent is dispatched, no code-generation preference is inferred.
- Keep planner-selected California 2018 ACSIncome, not the initially considered Alabama alternative. Use publicly downloadable Census file and package task filter. At most20,000 eligible rows, as in plan.
- Environment is Python3.11 if the preflight confirms it; freeze actual versions rather than assuming.
- Pilot/reference qualification and later any deviations are recorded in experiment_log.md. The prospective plan remains unchanged.
