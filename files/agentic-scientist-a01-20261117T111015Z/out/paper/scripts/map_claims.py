import json
from pathlib import Path


EPISODES = ["final.evidence.episodes"]
CLAIMS = [
    ("The studied response modifies selected target coordinates by a common fraction of remaining headroom, fixes rivals, and counts support rather than training cost.", EPISODES, ["source_evidence/downstream/program/src/program.py#L16-L28"], []),
    ("Evaluated headroom fractions are one quarter, one half, and full headroom; strict first place requires a margin exceeding 1e-10.", EPISODES, ["source_evidence/downstream/program/src/program.py#L16-L28", "source_evidence/evaluation/evaluate_final.py#L731-L732"], []),
    ("The median averages the central pair on even panels; symmetric trimming removes floor(m/5) values from each tail.", EPISODES, ["source_evidence/downstream/program/src/program.py#L70-L79"], []),
    ("The primary panels have 57 HELM subjects and six Open LLM task coordinates; the separate BBH sensitivity uses 24 recorded subtasks.", EPISODES, ["source_evidence/data/records.json", "source_evidence/evaluation/evaluate_final.py#L614-L669", "derived/summary.json#auxiliary"], ["MMLU", "HELM", "BBH"]),
    ("The public score inputs are the pinned HELM release, contents revision, and distinct results revision acquired on the recorded date, with the reported extracted-record checksum.", EPISODES, ["source_evidence/data/manifest.json"], []),
    ("The pinned official Open LLM contents dataset card lists six Raw fields (IFEval, BBH, MATH level 5, GPQA, MUSR, MMLU-PRO), separately from parallel display-score fields; the analyzed inputs use the raw fields.", EPISODES + ["OpenLLMContents"], ["literature/OpenLLMContents.json#inspected_fields", "literature/OpenLLMContents.README.md", "source_evidence/data/manifest.json"], ["OpenLLMContents"]),
    ("The protocol samples one nonleading target in each of 24 score strata using seeds 1009, 1013, and 1019, paired across aggregation rules and ceilings.", EPISODES, ["source_evidence/evaluation/evaluate_final.py#L672-L745", "derived/summary.json#seeds"], []),
    ("Full-support failure certifies unattainability for these monotone aggregators; it is not merely a limited-search failure.", EPISODES, ["source_evidence/downstream/program/src/program.py#L99-L108"], []),
    ("The selected implementation enumerates supports up to six coordinates, solves larger means exactly by sorted headroom, and uses marginal greedy witnesses for larger order-statistic panels.", EPISODES, ["source_evidence/downstream/program/src/program.py#L109-L137"], []),
    ("Lower bounds are independently verified reference bounds; feasible large-panel order-statistic supports are upper bounds, not exact costs.", EPISODES, ["source_evidence/evaluation/evaluate_final.py#L761-L789", "source_evidence/evaluation/evaluate_final.py#L873-L925"], []),
    ("The fixed jointly attainable mean-median cohorts contain 18, 17, and 17 targets, and every cost included in their contrast is exact.", EPISODES, ["derived/summary.json#central"], []),
    ("In each fixed six-task cohort the average median-minus-mean support fraction is negative at half headroom and positive at full headroom; all reported values and abstract ranges are derived from the same exact contrasts.", EPISODES, ["derived/summary.json#central", "figures/exact_rule_contrast.pdf"], []),
    ("The primary grid contains 72 target decisions per rule-ceiling cell, not necessarily independent unique models.", EPISODES, ["derived/summary.json#grid"], []),
    ("Open LLM attainment counts at quarter, half, and full headroom differ across mean, median, and trimming as reported in the main text and complete grid.", EPISODES, ["derived/summary.json#grid", "derived/full_grid.tex"], []),
    ("HELM attainment counts at quarter, half, and full headroom are those in the main text and complete grid; all ordinary primary nonattainment is certified infeasible.", EPISODES, ["derived/summary.json#grid", "derived/full_grid.tex"], []),
    ("All primary targets attain first place at full headroom in the recorded panels.", EPISODES, ["derived/summary.json#grid"], []),
    ("Figure 3 certification intervals use equal seed weights and within-ceiling three-rule joint cohorts; the caption reports all cohort sizes.", EPISODES, ["derived/summary.json#support", "figures/attainability_and_support_scope.pdf"], []),
    ("HELM half-headroom order-statistic average upper bounds lie below the exact mean cost on the joint cohort, while full-headroom intervals overlap the mean and do not establish reversal of minimum costs.", EPISODES, ["derived/summary.json#support"], []),
    ("The reported six-task three-rule support averages are exact within their declared jointly attainable ceiling-specific cohorts, which differ across ceilings.", EPISODES, ["derived/summary.json#support"], []),
    ("The main half-headroom table reports all-target penalized effort for exact/witness, marginal greedy, random, and no-intervention policies; nonattainment contributes one.", EPISODES, ["derived/comparators.tex", "source_evidence/evaluation/evaluate_final.py#L873-L925"], []),
    ("The frozen procedure ties greedy on HELM and the six-task mean, and has smaller penalized effort on the six-task median and trimmed mean at half headroom.", EPISODES, ["derived/comparators.tex"], []),
    ("Every scalar in the complete primary table is reproduced from the ordinary primary evaluator decisions, with success and penalty semantics kept separate.", EPISODES, ["derived/full_grid.tex"], []),
    ("Recorded conditional paired policy intervals use 200 cluster bootstrap resamples, RNG seed 48271, and 95-percent percentile endpoints; these do not test cross-rule ordering.", EPISODES, ["source_evidence/evaluation/evaluate_final.py#L1046-L1068", "derived/paired_intervals.tex"], ["Efron"]),
    ("Every row of the supplementary policy interval table reproduces the recorded family, rule, ceiling, seed, comparator, difference, and interval endpoints.", EPISODES, ["derived/paired_intervals.tex"], []),
    ("Auxiliary HELM projections, Open LLM even slots, and BBH odd slots have separately reported counts; BBH revision matching does not establish identical evaluation settings.", EPISODES, ["derived/auxiliary.tex", "source_evidence/evaluation/evaluate_final.py#L718-L732", "source_evidence/data/manifest.json#reconciliation"], []),
    ("The completed final evaluation is qualified; this does not imply unrestricted validity or exact large-panel order-statistic costs.", ["final.qualification.status", "final.qualification.outcome", "final.qualification.correct"], ["paper_data.json#/final_evaluation"], []),
    ("The recorded final control pass fraction is one; candidate diagnostics remain unverified.", ["final.metric.control_pass_rate"] + EPISODES, ["paper_data.json#/final_evaluation/metrics/control_pass_rate", "paper_data.json#/final_evaluation/evaluation_evidence/candidate_diagnostics_trust"], []),
    ("The retained selection is the reference baseline, with no qualifying development winner and zero retained development-score change.", ["study.selection_kind", "study.investigation_outcome", "study.search_score_delta"], ["paper_data.json#/downstream_study"], []),
    ("Three development alternatives were scored and none unscored; their qualification-failure causes are not identified, and they are not controlled component ablations.", ["study.attempts.total", "study.attempts.scored", "study.attempts.unscored", "study.investigation_outcome"], ["paper_data.json#/downstream_study"], []),
    ("The reported source locations support the exact evaluated implementation, whose selected and baseline source copies match.", ["study.selection_kind"] + EPISODES, ["source_evidence/downstream/program/src/program.py", "source_evidence/downstream/baseline/src/program.py"], []),
    ("The final evaluator uses CPU computation, its documented wall and method reservations and advisory decision budget; dependency versions are the supplied versions.", EPISODES, ["source_evidence/evaluation/evaluate_final.py#L39-L54", "source_evidence/evaluation/requirements.txt", "derived/environment.json"], []),
    ("Raw-score documentation, normalization, content partitioning, and uncertain score-data redistribution rights are as recorded by the acquisition manifest.", EPISODES, ["source_evidence/data/manifest.json"], []),
    ("The study does not measure training responses, practical expenditure, causal contamination effects, or population superiority; the observed ordering is conditional and descriptively selected.", EPISODES, ["derived/summary.json#central", "source_evidence/downstream/program/src/program.py#L16-L28"], []),
]


def main():
    claims = [{"claim": claim, "source_ids": sources, "citation_keys": citations,
               "evidence_refs": ["@evidence"+"[["+path+"]]" for path in paths]}
              for claim, sources, paths, citations in CLAIMS]
    references = json.loads(Path("references_provenance.json").read_text())["references"]
    for reference in references:
        key = reference["citation_key"]
        if key == "OpenLLMContents":
            continue
        claims.append({"claim": "Literature positioning uses only the inspected abstract and canonical metadata of " + reference["title"] + ".",
                       "source_ids": [reference["id"]], "citation_keys": [key],
                       "evidence_refs": ["@evidence"+"[[literature/"+key+".json#abstract]]"]})
    Path("claims_grounding.json").write_text(json.dumps({"claims": claims}, indent=2)+"\n")


if __name__ == "__main__":
    main()
