import hashlib
import json
from pathlib import Path


def main():
    # @evidence[[analysis_summary.json]]
    # @evidence[[paper_data.json]]
    summary = json.loads(Path('analysis_summary.json').read_text())
    claims = []

    def add(claim, sources=None, files=None, refs=None, scope='final fixed-game evaluation'):
        claims.append({'claim': claim, 'source_ids': sources or ['final.evidence.episodes'], 'citation_keys': refs or [], 'evidence_refs': files or ['paper_data.json#/final_evaluation/evaluation_evidence/episodes'], 'scope': scope})

    add('Final qualification independently reports completed/qualified/true. This concerns documented integrity, coverage, execution and controls, not deployment validity.', ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'], ['source_evidence/evaluation/evaluate_final.py#L1253-L1273'])
    add('Aggregate final normalized reference agreement is 0.9975639445869278, rounded to 0.99756 in the abstract.', ['final.metric.reference_fidelity'])
    add('All final structure-aware reference top-three overlaps and repeat-pair top-three/sign agreements equal one; these are separate assessments.', ['final.metric.top3_overlap', 'final.evidence.episodes'])
    add('Stored vectors have zero maximum coordinate range across repeats within each fixed cap/model/query.', files=['analysis_summary.json#/max_repeat_vector_difference'])
    add(f"Pure reference sign agreement is {summary['reference_sign_mean']:.10f}, not the mixed evaluator sign metric.", ['final.evidence.episodes', 'final.metric.signed_agreement'], ['analysis_summary.json#/reference_sign_mean', 'source_evidence/evaluation/evaluate_final.py#L1038-L1053'])
    add('Mean normalized endpoint residual is 1.27919753412707e-11, control pass rate one, failed-call fraction zero and replay error zero.', ['final.metric.efficiency_error', 'final.metric.control_pass_rate', 'final.metric.failed_fraction', 'final.metric.replay_error'])
    add('The recorded full workload takes 700.3707705293782 wall seconds, rounded to 700.37, including references, comparators, training and overhead; candidate-only latency is unavailable.', ['final.metric.wall_seconds'], ['source_evidence/evaluation/evaluate_final.py#L1310-L1343', 'paper_data.json#/final_evaluation/metrics/wall_seconds'])
    methods = [
        ('Four final dataset/model conditions are German logistic, German forest, ACS logistic and ACS forest; no additional task list or downstream study is present.', ['paper_data.json#/final_evaluation/evaluation_evidence/episodes']),
        ('Final seeds are 104729, 130363 and 155921; caps 64/256/1024; six repeats per cap; sixteen fixed queries and training-background rows per fitted condition.', ['source_evidence/evaluation/evaluate_final.py#L34-L36', 'source_evidence/evaluation/evaluate_final.py#L1316-L1319', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes']),
        ('Final German retained splits are 300/100/100 records and twenty groups; ACS 20000/6667/6667 and ten groups. These are protocol counts, not independent explained-sample counts.', ['source_evidence/evaluation/capture.py#L61-L155', 'source_evidence/evaluation/data_provenance.json', 'source_evidence/evaluation/evaluate_final.py#L687-L718']),
        ('German uses original class code 2. ACS uses 2024 PUMS, native RELSHIPP without a RELP crosswalk, the retained adult filter and PINCP>50000 target.', ['source_evidence/evaluation/capture.py#L72-L155', 'source_evidence/evaluation/data_provenance.json']),
        ('German development/final content groups are disjoint. ACS uses California development and New York final data after excluding raw predictor-content overlaps.', ['source_evidence/evaluation/capture.py#L72-L155', 'source_evidence/evaluation/data_provenance.json']),
        ('Training-fitted ordinal vocabularies use unseen code -1; numeric medians and standardization are training fitted; queries/background use fixed ordering.', ['source_evidence/evaluation/evaluate_final.py#L687-L718', 'source_evidence/evaluation/evaluate_final.py#L838-L842']),
        ('Logistic regression uses lbfgs, max_iter 500 and tolerance 1e-7. Forests use sixty-four trees, depth six and n_jobs one.', ['source_evidence/evaluation/evaluate_final.py#L833-L837']),
        ('ACS references enumerate ten-feature finite games; German references average two independent cap-4096 library estimates. Their half-difference is a proxy, not a calibrated interval.', ['source_evidence/evaluation/evaluate_final.py#L774-L796', 'source_evidence/evaluation/evaluate_final.py#L849-L858']),
        ('Stored 95-percent intervals use 1000 bootstrap resamples of sixteen query-level means after cap/repeat averaging, conditional on one fitted model/reference.', ['source_evidence/evaluation/evaluate_final.py#L1154-L1159']),
        ('The normalized L1 agreement floor is 0.001; signs at magnitude at most 1e-8 are zero; top-three ties follow coordinate order. Endpoint residual is capped at one.', ['source_evidence/evaluation/evaluate_final.py#L1014-L1030']),
        ('Library KernelExplainer uses identity link, l1_reg zero and nsamples equal to cap. Two independent split-cap calls each use floor(cap/2).', ['source_evidence/evaluation/evaluate_final.py#L757-L772', 'source_evidence/evaluation/evaluate_final.py#L860-L868']),
        ('Forest attribution uses signed leaf-game beta-integral coefficients over all trees/background rows, intersecting repeated splits and retaining float32 predictor-input semantics.', ['source_evidence/selected/forest.py#L11-L81', 'source_evidence/evaluation/evaluate_final.py#L720-L755']),
        ('Probability-scale logistic integration uses ceil(d/2) inclusion nodes, eight-node frequency panels, cutoff eight and at most 2048 frequency nodes; tail tolerance 1e-10 and mesh/efficiency tolerances 1e-8.', ['source_evidence/selected/logistic_fourier.py#L12-L140']),
        ('Two consecutive mesh agreements are required. Failure for any background row rejects integration; frequency-tail control is not a rigorous discretization bound.', ['source_evidence/selected/logistic_fourier.py#L43-L140']),
        ('Dispatch uses forest structure directly, then generic enumeration when cap covers 2^d-2 nontrivial coalitions before logistic integration; branch counts are unrecorded.', ['source_evidence/selected/reliability.py#L163-L197']),
        ('The sampled fallback combines independent complete paths and importance-corrected constrained regression. Alpha 0.05 separation is used only with at least two paths; acceptance coverage is absent.', ['source_evidence/selected/reliability.py#L66-L197']),
        ('The release contains independent validation routines without retained executions. They are not additional empirical controls.', ['source_evidence/selected/validate_forest.py', 'source_evidence/selected/validate_logistic_fourier.py']),
        ('Recorded dependencies include NumPy 2.1.3, SciPy 1.15.3, scikit-learn 1.6.1, SHAP 0.48.0, pandas 2.2.3 and folktables 0.0.12; a fresh full-lock installation was not tested.', ['source_evidence/evaluation/requirements.txt']),
    ]
    for claim, files in methods:
        add(claim, files=files, scope='final protocol and readable implementation evidence, not additional measurements')
    results = [
        ('German reference mean absolute coordinate half-differences are about 1.05e-4 logistic and 1.20e-4 forest; no error decomposition follows.', ['analysis_summary.json#/reference_uncertainty']),
        ('Seed-104729 query-bootstrap intervals round to [0.99618,0.99709] German logistic and [0.99292,0.99442] German forest.', ['paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/fidelity_instance_bootstrap_ci95', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/1/observations/fidelity_instance_bootstrap_ci95']),
        ('Final cap-64 structure agreement is 0.9966/0.9937 German logistic/forest, versus library 0.9347/0.8806; ACS structure rounds to one versus library 0.9577/0.9636.', ['analysis_summary.json#/final']),
        ('At cap 1024 final library means are 0.9889/0.9802 German logistic/forest and round to one for both ACS cases. This does not establish necessity of structure-aware access.', ['analysis_summary.json#/final']),
        ('Split-cap German means at cap 64 are 0.3341/0.2995, recovering to 0.9699/0.9448 at cap 256; recorded diagnostics do not isolate a cause.', ['analysis_summary.json#/final']),
        ('Final validation accuracy is 0.67 German logistic, 0.65--0.69 German forest, about 0.7609 ACS logistic and 0.7755--0.7773 ACS forest. Converged logistic fits use 19 and 13 iterations respectively.', ['paper_data.json#/final_evaluation/evaluation_evidence/episodes']),
    ]
    for claim, files in results:
        add(claim, files=files)
    development_sources = ['result.top_program_01', 'result.top_program_02', 'result.top_program_03']
    add('Development uses seeds 1729/2718, eight queries, four repeated calls, caps 64/256; comparisons are supporting evidence, not held-out confirmation.', development_sources, ['paper_data.json#/all_programs','source_evidence/evaluation/evaluate.py#L1316-L1319'], scope='development only')
    add('German cap-64 forest agreement changes from 0.858--0.870 to 0.9924--0.9929 with leaf computation; logistic from 0.946--0.951 to about 0.9963 with integration.', development_sources, ['analysis_summary.json#/development'], scope='development only')
    add('Custom sampled development means are nonmonotone from cap 64 to 256: ACS forest about 0.9674 to 0.9512 and German logistic 0.9488 to 0.9137; no unique cause is established.', development_sources, ['analysis_summary.json#/development'], scope='development only')
    for row in summary['final']:
        add(f"Final table seed {row['seed']}, {row['case']}, cap {row['cap']}: agreement library {row['standard'][0]:.10f}, split cap {row['multistart'][0]:.10f}, structure {row['structure'][0]:.10f}; structure reference signs {row['structure'][2]:.10f}, repeat metrics {row['repeat']}, stored conditional query CI {row['bootstrap_ci95']}.", files=['analysis_summary.json#/final','paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    for row in summary['development']:
        source = ['result.top_program_03', 'result.top_program_02', 'result.top_program_01'][row['configuration']]
        add(f"Development figure: configuration {row['configuration']}, seed {row['seed']}, {row['case']}, cap {row['cap']}: agreement {row['agreement']:.10f}.", [source], ['analysis_summary.json#/development','paper_data.json#/all_programs'], scope='development only')
    for reference in json.loads(Path('references_provenance.json').read_text())['references']:
        add('Bibliographic context only: ' + reference['title'] + '. Not an evaluated comparator unless independently measured.', [reference['id']], [reference['local_record']], [reference['citation_key']], scope='literature context')
    Path('claims_grounding.json').write_text(json.dumps({'claims': claims, 'interpretation_policy': 'Final qualification is independent of selection. No final failure is present. Repeatability, reference agreement and deployment validity remain distinct; code locations support implementation claims.'}, indent=2))
    files = sorted(Path('source_evidence').rglob('*'))
    manifest = {'files': [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in files if path.is_file() and path.name != 'MANIFEST.json']}
    Path('source_evidence/MANIFEST.json').write_text(json.dumps(manifest, indent=2))
    inputs = ['@evidence[[paper_data.json]]', '@evidence[[analysis_summary.json]]', '@evidence[[references_provenance.json]]', '@evidence[[source_evidence/MANIFEST.json]]']
    for file, kind in [('claims_grounding.json','derived'), ('paper.tex','manuscript')]:
        sidecar = {'schema_name': 'scientific-evidence.artifact-manifest', 'artifact': {'path': file, 'kind': kind, 'sha256': hashlib.sha256(Path(file).read_bytes()).hexdigest()}, 'derived_from': inputs, 'generated_by': {'script_path': 'build_claims.py'}}
        if kind == 'manuscript':
            sidecar.pop('generated_by')
            sidecar['notes'] = 'Manuscript authored by the writing assistant from the listed artifacts; build_claims.py records its provenance but does not generate the prose.'
        Path(file + '.prov.json').write_text(json.dumps(sidecar, indent=2))
    print('Wrote', len(claims), 'grounded claims')


if __name__ == '__main__':
    main()
