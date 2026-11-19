"""Build an explicit claim map without extending the host evidence registry."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    claims = []

    def add(text, source_ids, refs, keys=None, scope=None):
        record = {"claim": text, "source_ids": source_ids, "citation_keys": keys or [], "evidence_refs": refs}
        if scope:
            record["source_scope_note"] = scope
        claims.append(record)

    final = ["final.evidence.episodes"]
    final_ref = ["paper_data.json#/final_evaluation/evaluation_evidence/episodes"]
    development = ["result.top_program_01"]
    development_ref = ["paper_data.json#/best_correct/evaluation_evidence/episodes"]
    selection_note = "The registry ID identifies the selected configuration only; it does not substantiate the scientific numbers. The raw evidence_refs, not the selection score, support this claim."
    add("The final evaluation completed, did not qualify, and has a false qualification decision; the supplied diagnostics do not identify the cause.",
        ["final.qualification.status", "final.qualification.outcome", "final.qualification.correct"],
        ["paper_data.json#/final_evaluation", "paper_data.json#/grounding_sources/final.qualification.outcome"])
    add("Five of nine planned final width-seed records are retained, with coverage 3/2/0 at widths 32/128/256; absent records are not measured non-events or accuracy losses.",
        final + ["final.metric.complete_episode_fraction"], final_ref)
    add("The two retained width-128 studied final records show delayed events; all three width-32 held-out onsets are right-censored at 24000 updates.", final, final_ref)
    add("Development fitting onsets in seed order 101/211 are 2200/2800 at width32, 300/300 at width128, and 200/200 at width256.",
        development, development_ref, scope=selection_note)
    add("Development widest-minus-narrowest paired fit differences are -2000 and -2600 updates; fitting is earlier but endpoint accuracy is nonmonotone in width in both retained seeds.",
        development, development_ref + ["derived/summary.json#/paired/development_256_minus_32"], scope=selection_note)
    add("Development studied endpoint means plus sample SD are 74.68+/-4.47, 29.33+/-3.68, and 39.35+/-3.49 percent at widths32/128/256, over two seeds each.",
        development, development_ref + ["derived/summary.json#/cells"], scope=selection_note)
    add("The task is modulo97 addition, learned by two summed embeddings, GELU, and linear output, with widths32/128/256 and 9441/37473/74849 parameters.",
        final, final_ref + ["source_evidence/task/evaluate_final.py#L801", "derived/observations.json#/rows"],
        scope="Model and training details are substantively supported by readable source whose digest matches the final evaluator; the final evidence supplies measured parameter counts and widths.")
    add("Development/final pools have4704/4705 disjoint pairs with per-seed train/evaluation sizes2822/1882 and2823/1882, respectively; measured results cover one modular operation.",
        final + development,
        ["source_evidence/task/resources/search/dataset.json", "source_evidence/task/resources/final/dataset.json"] + final_ref + development_ref,
        scope="Pool/split definitions come from inspectable resources used by the evaluated implementation, not an aggregate score.")
    add("The studied learning-rate/decay/initialization configuration is(0.003,1,0.5), common to all retained widths and seeds; reference(0.001,1,1) differs in two settings.",
        final, final_ref + ["source_evidence/task/evaluate_final.py#L795", "source_evidence/controllers/studied/src/program.py#L37"])
    add("Zero decay changes only the studied decay to0; norm matching rescales to the same-seed width128 global norm, not to equal capacity or function.",
        final, final_ref + ["source_evidence/task/evaluate_final.py#L795", "source_evidence/task/evaluate_final.py#L821"])
    add("Width128 norm-matched scientific curves and initial/final hashes duplicate the studied records; they are not additional independent delayed events.", final, final_ref + development_ref)
    add("Development uses seeds101/211 at6000 updates; final uses60613/70717/80821 at24000, with checkpoints every100 updates; pools and seeds differ along with duration.",
        final + development, final_ref + development_ref)
    add("Training-fit/held-out onsets require thresholds0.99/0.95 sustained for three consecutive checkpoints, timestamped at the first; a delayed event requires at least1000 updates between onsets.",
        final, ["source_evidence/task/evaluate_final.py#L1001"] + final_ref)
    add("Final width128 seeds60613/70717 fit at300/200 and generalize at17600/19200; observed delays are17300/19000 updates; endpoints98.353/97.768 percent.",
        final, final_ref + ["derived/observations.json#/rows"])
    add("Final width32 seeds60613/70717/80821 fit at2600/2400/3000, have censored held-out onset at24000, and endpoints80.925/88.842/73.433 percent.",
        final, final_ref + ["derived/observations.json#/rows"])
    add("The retained seed-paired final width128-minus32 endpoint differences are17.428 and8.927 percentage points, not the planned256-minus32 contrast.",
        final, final_ref + ["derived/summary.json#/paired/final_128_minus_32"])
    add("Conditional on retained final records, event counts2/2 and0/3 have exact95-percent binomial intervals[0.158,1] and[0,0.708]; these exploratory intervals neither resolve missingness nor establish population or mechanistic validity.",
        final, final_ref + ["derived/summary.json#/cells", "scripts/build_artifacts.py"])
    add("Retained final no-decay width32 endpoints0.478--0.797 percent and width128 endpoints0 percent coexist with fit onsets1300--1600 and200, respectively; this is a finite-horizon configuration contrast only.",
        final, final_ref + ["derived/observations.json#/rows"])
    add("Development norm-matched width32 endpoints70.510/56.164 percent exceed width128 endpoints31.934/26.727 in both seeds; scalar norm matching does not remove that ordering.",
        development, development_ref, scope=selection_note)
    add("Retained final reference endpoints54.570--65.037 percent atwidth32 and80.659--84.272 atwidth128 show no sustained held-out threshold crossing; these are multi-setting reference comparisons.",
        final, final_ref + ["derived/observations.json#/rows"])
    add("Final event fraction0.222222 is design-weighted over nine cells, mean endpoint functional0.488133 includes missing-cell zero weighting, and capped delay0.945833 includes missing-cell cap weighting; these are not population event rates, observed endpoint means, or uncensored mean event times.",
        ["final.metric.grokking_incidence", "final.metric.mean_final_accuracy", "final.metric.restricted_mean_delay"],
        ["paper_data.json#/final_evaluation/metrics", "source_evidence/task/evaluate_final.py#L1066"])
    add("The descriptive mean of the five observed final studied endpoints is0.878640, distinct from the failure-weighted registry functional.",
        final, final_ref + ["derived/summary.json#/final_observed_endpoint_mean"])
    add("Related development settings are(0.003,1,1),(0.003,1,0.5),(0.006,0.5,0.5); the faster setting has an unavailable width256 seed211 record, not a measured zero or known failure cause.",
        ["result.top_program_01", "result.top_program_02"],
        [f"paper_data.json#/all_programs/{index}/evaluation_evidence/episodes" for index in range(3)],
        scope="Selection IDs identify related selected configurations only. All sensitivity numbers and missingness are supported by explicit raw registry pointers, not these scalar IDs.")
    add("The evaluated source uses CPU float32, full-batch AdamW, deterministic algorithms, at most two CPU threads and one inter-op thread; requirements pin numpy2.1.3 and torch2.5.1+cpu.",
        final, ["source_evidence/task/evaluate_final.py#L765", "source_evidence/task/evaluate_final.py#L781", "source_evidence/task/requirements.txt"])
    add("The readable final evaluator digest matches the registry evaluator digest; hash agreement is provenance, while code contents support architecture and optimizer details.",
        final, ["derived/source_manifest.json", "source_evidence/task/evaluate_final.py", "paper_data.json#/final_evaluation/evaluator_sha256"])
    add("Recorded selected-development seed evaluation durations are981/754 seconds, and final seed totals3199/2794/3488 seconds after rounding; incomplete final coverage prevents extrapolating complete-grid runtime.",
        final + development, final_ref + development_ref + ["derived/summary.json#/runtime_by_scope_seconds"])
    add("All five retained final studied endpoints have training accuracy1.0, with different residual train cross-entropies; initial/final global norms increase in every record, including delayed-event records. Table norms/losses are individual measured endpoints, not a norm-trajectory mediation test.",
        final, final_ref + ["derived/observations.json#/rows", "derived/norm_loss_records.tex"])
    literature = [
        ("2201.02177", "Power2022GrokkingGB", "Power et al. document delayed generalization on small algorithmic datasets."),
        ("2301.05217", "Nanda2023Progress", "Nanda et al. reverse-engineer a Fourier-based modular-addition computation in small Transformers; our architecture and measurements do not establish the same mechanism."),
        ("2210.01117", "Liu2022OmnigrokGB", "Liu et al. relate grokking to loss landscapes as a function of weight norm."),
        ("2309.02390", "Varma2023ExplainingGT", "Varma et al. propose differing learning speeds and norm efficiencies of memorizing and generalizing circuits."),
        ("2310.06110", "Kumar2023GrokkingAT", "Kumar et al. study lazy-to-rich dynamics, including polynomial regression exhibiting grokking without regularization."),
        ("2303.06173", "Davies2023Unifying", "Davies et al. connect grokking and double descent through pattern-learning speeds and capacity variation."),
        ("1912.02292", "Nakkiran2020Double", "Nakkiran et al. document nonmonotone generalization as model size or duration varies; the present narrow sweep does not establish double descent."),
        ("1711.05101", "Loshchilov2019AdamW", "AdamW decouples weight decay from adaptive loss-gradient updates; nominal shrinkage is not a measured complete dynamical clock."),
    ]
    for identifier, key, text in literature:
        add(text, ["ref.arxiv." + identifier], ["source_evidence/literature/" + identifier + "_opening.txt"], [key])
    (ROOT / "claims_grounding.json").write_text(json.dumps({"claims": claims,
        "mapping_policy": "Host paper_data.json is read-only. Scientific raw pointers supplement selection identity IDs; no scalar search ID is used as substantive support for trajectory values. Final qualification remains failed with unknown cause."}, indent=2) + "\n")

    (ROOT / "claims_grounding.json.prov.json").write_text(json.dumps({
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": "claims_grounding.json", "kind": "derived"},
        "derived_from": ["@evidence[[paper_data.json]]", "@evidence[[references_provenance.json]]", "@evidence[[scripts/build_claims.py]]"],
        "generated_by": {"script_path": "scripts/build_claims.py"}
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
