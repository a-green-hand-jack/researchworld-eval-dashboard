import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    records = json.loads((ROOT / "analysis_results.json").read_text())
    paper_data = json.loads((ROOT / "paper_data.json").read_text())
    references = json.loads((ROOT / "references_provenance.json").read_text())
    claims = []

    def add(text, source_ids=None, citation_keys=None, evidence_refs=None, **extra):
        claims.append({"claim": text, "source_ids": source_ids or ["final.evidence.episodes"],
                       "citation_keys": citation_keys or [], "evidence_refs": evidence_refs or [], **extra})

    add(f'The sealed record contains {records["repetitions"]} repetitions, {records["case_count"]} paired conditions per repetition, and seeds {records["seeds"][0]}–{records["seeds"][-1]}.',
        evidence_refs=["paper_data.json#/final_evaluation/evaluation_evidence/episodes"])
    for row in records["cases"]:
        case = row["case"]
        add(f'C{case} has the recorded truth(s) {row["truths"]}.', evidence_refs=[f'analysis_results.json#/cases/{case-1}/truths'])
        for method, value in row["methods"].items():
            add(f'C{case}, {method}: empirical coverage {value["coverage"]}, pointwise exact-binomial 95% limits [{value["coverage_lower95"]}, {value["coverage_upper95"]}]; mean width {value["width"]["mean"]}; zero-width intervals {value["zero_width_count"]}.',
                evidence_refs=[f'analysis_results.json#/cases/{case-1}/methods/{method}', "scripts/build_artifacts.py"],
                derivation="Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.")
        for method, value in row["differences"].items():
            add(f'C{case}, score-control minus {method} mean-width difference {value["mean"]}, pointwise paired-t 95% limits [{value["lower95"]}, {value["upper95"]}].',
                evidence_refs=[f'analysis_results.json#/cases/{case-1}/differences/{method}', "scripts/build_artifacts.py"],
                derivation="Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.")
    add("Only C2 has a negative score-control-minus-evaluated-PPI++ mean width difference; all six other paired differences are positive and their pointwise intervals exclude zero.",
        evidence_refs=["analysis_results.json#/cases"])
    add("Compared with labeled normal inference, score control is narrower in C1-C3 and wider in C4-C7. Compared with exact binomial it is narrower with negative pointwise intervals in C1-C4,C6,C7, and unresolved in C5.",
        evidence_refs=["analysis_results.json#/cases"])
    add("All seven score-control pointwise coverage intervals contain 0.95; none of these finite-sample estimates establishes nominal coverage or a finite-sample guarantee.",
        evidence_refs=["analysis_results.json#/cases", "source_evidence/calibration/METHOD.md"])
    for metric in ["coverage", "mean_width"]:
        add(f'Descriptive pooled {metric} is {paper_data["final_evaluation"]["metrics"][metric]}; no iid binomial interval is attached to the condition-pooled rate.',
            source_ids=["final.metric." + metric], evidence_refs=["paper_data.json#/final_evaluation/metrics/" + metric])
    add("Final evaluation status is completed and outcome is qualified, with correct=true in the qualification record. Acceptance does not establish nominal validity or implementation identity.",
        source_ids=["final.qualification.status", "final.qualification.outcome", "final.qualification.correct"],
        evidence_refs=["paper_data.json#/final_evaluation"], visible_translation="Completed and qualified; internal correctness field is not surfaced in visible manuscript.")
    add("Candidate diagnostics are unverified; gate-specific failure causes and condition sampling mechanisms are not supplied. No named task transfer or executed matched affine/spline ablation is evidenced.",
        evidence_refs=["paper_data.json#/final_evaluation/evaluation_evidence", "source_evidence/calibration/METHOD.md"])
    anchor = ["result.top_program_01"]
    source_role = "Registry source is an archived-method path anchor only; its scalar score does not substantiate implementation details or final source identity. Inspect the readable files in evidence_refs."
    add("The archived target is the binary superpopulation E[Y], with unchanged labeled outcomes and labeled/unlabeled frozen scalar scores, alpha=0.05, and no truth or condition identity supplied to inference.",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/program.py#L1-L44"], source_role=source_role)
    add("Archived calibration uses two complementary labeled folds and two unlabeled folds; training-only intercept, centering/scaling, ridge/GCV and quantile knots; heldout controls are clipped to [0,1].",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/program.py#L51-L102", "source_evidence/calibration/program.py#L123-L171"], source_role=source_role)
    add("Archived hyperparameters: training sizes <4 or score range <1e-12 retain the constant; feature scale floor 1e-8; up to three quartile knots at training size >=16; up to seven quantile knots at size>=64; penalties 0.001,0.01,0.1,1,10; GCV uses trace degrees of freedom and denominator floor 1/m.",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/program.py#L58-L93"], citation_keys=["HoerlKennard1970", "Golub1979GCV"], source_role=source_role)
    add("Archived fold estimator is residual mean plus rho times unlabeled calibrated mean with rho=N/(n+N), using fixed labeled-fold-size weights. Pooled residual/control variance and Wilson-style stabilization are approximate, not a finite-sample proof; n<16 uses labeled-only exact binomial inversion by a size-only rule.",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/program.py#L123-L185", "source_evidence/calibration/program.py#L246-L259"], source_role=source_role)
    add("For fixed square-integrable controls under independent common-population iid samples, the stated variance decomposition, conditional-mean oracle variance, excess rho*Var(g-m)/n and unrestricted affine projection gap hold. They are not measured oracle attainment or validity of the fitted-control interval.",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/METHOD.md", "source_evidence/calibration/study.py#L12-L26"], source_role=source_role)
    add("The separate unmeasured bounded construction uses empirical-Bernstein radii with log(4/delta), support lengths, singleton/full-range fallback, delta=alpha/(2K), and fixed nonnegative aggregation. A conditional union-bound coverage argument assumes independent iid common-population samples. These endpoints are not the primary returned track.",
        source_ids=anchor, evidence_refs=["source_evidence/calibration/program.py#L109-L185", "source_evidence/calibration/METHOD.md"], citation_keys=["MaurerPontil2009", "Hoeffding1963"], source_role=source_role)
    add("An affine-only matched function and oracle reporting helper are present but have no supplied measured results. No new experiments, bootstrap, jackknife or sensitivity sweep were run during drafting.",
        source_ids=anchor + ["final.evidence.episodes"], evidence_refs=["source_evidence/calibration/program.py#L188-L192", "source_evidence/calibration/study.py", "scripts/build_artifacts.py"], source_role=source_role)
    for ref in references["references"]:
        add("Literature context: " + ref["title"], source_ids=[ref["id"]], citation_keys=[ref["citation_key"]],
            evidence_refs=[ref.get("consulted_text_path", "literature/" + ref["citation_key"] + ".json")],
            scope="Bibliographic identity and consultation scope recorded in literature/; no numerical experimental claims sourced to references.")
    allowed = set(paper_data["grounding_sources"]) | {ref["id"] for ref in references["references"]}
    assert all(set(claim["source_ids"]) <= allowed for claim in claims)
    (ROOT / "claims_grounding.json").write_text(json.dumps({"claims": claims}, indent=2) + "\n")
    source_entries = []
    original = "results/ideas/02_honest_nonlinear_score_controls_with_a_finite_sample_safety_track/program_1/"
    for path in (ROOT / "source_evidence/calibration").iterdir():
        if path.suffix == ".json":
            continue
        relative = str(path.relative_to(ROOT))
        original_path = original + ("" if path.name.endswith(".toml") else "src/") + path.name
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        original_available = (ROOT / original_path).is_file()
        if original_available:
            assert path.read_bytes() == (ROOT / original_path).read_bytes()
        source_entries.append({"path": relative, "sha256": sha, "copied_from": original_path,
                               "mounted_original_checked": original_available})
        Path(str(path) + ".prov.json").write_text(json.dumps({
            "schema_name": "scientific-evidence.artifact-manifest",
            "artifact": {"path": relative, "kind": "source", "sha256": sha},
            "derived_from": ["@evidence[[source_evidence/manifest.json]]"],
            "notes": "Inspectable archived source; byte identity to the sealed final executable has not been independently established."}, indent=2) + "\n")
    (ROOT / "source_evidence/manifest.json").write_text(json.dumps({"sources": source_entries,
        "final_source_identity": "unverified", "final_tree_hash": paper_data["final_evaluation"]["program_tree_sha256"]}, indent=2) + "\n")
    print("Wrote", len(claims), "grounded claims and", len(source_entries), "source-file records.")


if __name__ == "__main__":
    main()
