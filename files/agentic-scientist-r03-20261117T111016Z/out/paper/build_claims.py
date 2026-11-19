import json
from pathlib import Path


def main():
    """@evidence[[paper_data.json#/final_evaluation]]
    @evidence[[references_provenance.json#/references]]
    """
    claims = []

    def add(text, sources, locations=None):
        claim = dict(claim=text, source_ids=sources, citation_keys=[])
        if locations:
            claim['source_locations'] = locations
        claims.append(claim)

    episodes = ['final.evidence.episodes']
    implementation = ['result.best_correct_score']
    add('Final evaluation completed and qualified; qualification is not evidence of universal validity or superiority.', ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'])
    add('The final frozen MTEB plane has 126 rows and 135 task/subset columns, not independent benchmark suites; results revision is 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383.', episodes, ['source_evidence/resources/final/manifest.json:1', 'source_evidence/evaluate_final.py:715'])
    add('English text-only main-score extraction preserves bounded noncorrelations and maps correlations by (x+1)/2; task-definition revision 5a83aafe4e7140d0606b96f59448c704f31dbf76, global support 32 and row support 12 are manifest rules.', episodes, ['source_evidence/evaluate_final.py:685', 'source_evidence/resources/final/manifest.json:1'])
    add('History/test alias and normalized content separation are checked; family holdout additionally separates heuristic family labels. This does not certify true ancestry or pretraining independence.', episodes, ['source_evidence/evaluate_final.py:715'])
    add('A shuffled approximately two-thirds reservoir, cut at least eight, is disjoint from a sealed target set fixed across budgets and methods; only observed cells are retrospectively evaluated.', episodes, ['source_evidence/evaluate_final.py:851'])
    add('Rank-four ridge ALS with ridge 0.1, fifty sweeps and Gaussian factor initialization SD 0.1 fits observed entries only; historical means remain fixed.', implementation + episodes, ['source_evidence/selected/src/program.py:363', 'source_evidence/evaluate_final.py:920'])
    add('Ridge conditioning and the all-column integrated-variance acquisition formula describe the evaluated source. The rank-one algebra is a surrogate reduction, not an MAE or calibrated posterior guarantee; selection is independent of revealed values.', implementation, ['source_evidence/selected/src/program.py:395'])
    add('Donor-excluded auxiliary predictions yield residuals only for observed donor targets; shared-anchor kernel weights are multiplied by overlap fraction, use a 0.025 scale floor, and vanish at zero overlap.', implementation, ['source_evidence/selected/src/program.py:51', 'source_evidence/selected/src/program.py:97', 'source_evidence/selected/src/program.py:145'])
    add('Weighted median residual correction uses effective count (sum w)^2/max(sum(w^2),1e-12) in prediction and calibration, excludes queried columns, clips to [0,1], and leaves the base unchanged at total weight at most 1e-12 or at zero blend. Effective count measures concentration only when the denominator floor is inactive; an active floor introduces absolute-weight-scale dependence without certifying geometric support.', implementation, ['source_evidence/selected/src/program.py:164', 'source_evidence/selected/src/program.py:177', 'source_evidence/selected/src/program.py:194', 'source_evidence/selected/src/program.py:300'])
    add('History-only nested calibration uses two validation folds and two donor folds, at most 16 validation rows, 128 donors, 12 auxiliary sweeps, and pool cap min(512,max(64,floor(196608/N))).', implementation, ['source_evidence/selected/src/program.py:200'])
    add('Calibration grid h={0.35,0.75,1.5}, tau={4,16}, alpha={0,0.25,0.5,1} includes exact zero fallback; historical finite-cell pooling differs from fixed-target outer row averaging.', implementation, ['source_evidence/selected/src/program.py:200'])
    add('ALS arithmetic cost O(E r^2+(M+N)r^3) per sweep and donor-by-column residual storage are direct algebraic consequences of the inspected dense-solve loops, not measured runtime or novel theory.', implementation, ['source_evidence/selected/src/program.py:51', 'source_evidence/selected/src/program.py:363'])
    add('Five final references are column mean, query mean, random-query low-rank, variance-query low-rank, and linear ridge; query policies differ and centered missing entries in linear ridge are zero-filled.', episodes, ['source_evidence/evaluate_final.py:870'])
    add('Constant history preserves masks and replaces observed values by column means. Column shifting rolls each value/mask pair by an independent nonzero offset, preserving per-column observed multisets; controls match model holdout.', episodes, ['source_evidence/evaluate_final.py:808', 'source_evidence/resources/final/plan.json:1'])
    add('Budgets 1,2,4,8 use nested prefixes; seeds 6841,8089,9011; history/test sizes 94/32 except final family split 93/33; six primary condition/seed averages have equal weight.', episodes, ['source_evidence/resources/final/plan.json:1', 'source_evidence/evaluate_final.py:970'])
    add('Aggregate MAE 0.040807843083862115, RMSE 0.06432104648676243, strongest aggregate baseline 0.045249969215420516, gain 0.004442126131558401, relative reduction 9.816860008%.', ['final.metric.mae','final.metric.rmse','final.metric.baseline_mae','final.metric.delta_best_baseline'], ['derived_results.json:1'])
    add('All six estimators and both holdouts in Table 1, the complete budget table, and seed table reproduce retained episode arrays; the studied configuration has lower aggregate MAE in each holdout than every reference.', episodes, ['derived_results.json:1','tables/main_comparison.tex:1','tables/budget_details.tex:1','tables/seed_details.tex:1'])
    add('Studied MAE model/family=0.038312665669/0.043303020499 versus linear ridge 0.045116500008/0.045383438423; partitions differ, so no causal effect of family membership is inferred.', episodes, ['derived_results.json:1'])
    add('Studied seed MAEs 0.038496586319,0.041126033629,0.042800909303 (sample SD 0.002169731091); linear-ridge seed MAEs 0.041657905965,0.045940218194,0.048151783488. Seeds share source data.', episodes, ['derived_results.json:1'])
    add('Primary budget MAEs 0.045233341978,0.042208509062,0.039639061083,0.036150460213 decrease over k=1,2,4,8. Each holdout seed-mean curve decreases, without per-model monotonicity or sufficient-budget claims.', ['final.metric.mae_k1','final.metric.mae_k2','final.metric.mae_k4','final.metric.mae_k8'] + episodes, ['derived_results.json:1'])
    add('At eight queries studied model/family errors are 0.034476748972/0.037824171454, versus ridge 0.039273276354/0.039840694780.', episodes, ['derived_results.json:1'])
    add('Paired component resampling uses 400 draws and RNG 424242; quantiles .005/.995 for each of five baselines precede separate minima of lower and upper bounds. These are not a conventional single-comparator interval.', episodes + ['final.metric.gain_ci_low','final.metric.gain_ci_high'], ['source_evidence/evaluate_final.py:999','derived_results.json:1'])
    add('Reported bound minima [0.0021032442082077377,0.009199712663056218] are reconstructed exactly; all baseline-specific intervals in the supplement come from the same retained paired arrays.', ['final.metric.gain_ci_low','final.metric.gain_ci_high'] + episodes, ['derived_results.json:1'])
    add('Matched model-holdout intact MAE 0.038312665669 rises to 0.064367113099 under constant history and 0.068569520893 under column shifts; shifted column mean is 0.064367113099 and variance low-rank 0.070913935972. The method loses to column mean under shifts.', ['final.metric.constant_control_mae','final.metric.permuted_control_mae'] + episodes, ['derived_results.json:1'])
    add('Constant-history column means and all centered historical linear references equal the studied sealed-target MAE; controls do not isolate any component.', episodes, ['derived_results.json:1'])
    add('All-unqueried changing-target diagnostic MAEs A/B/C/D=0.036645358811/0.042420107742/0.065275510462/0.063523296739; not a common-target comparison.', episodes, ['derived_results.json:1'])
    add('Reset replay query sequences matched and maximum absolute prediction difference was zero; diagnostics do not certify all possible leakage checks.', ['final.metric.reset_max_abs_delta','final.qualification.outcome'], ['source_evidence/evaluate_final.py:976'])
    add('No matched final residual-off, unconditional-residual, donor-only, support-gating, temporal, cross-leaderboard or missingness-stratified result is available; sequential development does not isolate causal components.', episodes + implementation, ['source_evidence/selected/src/program.py:200'])
    add('Two development configurations have numeric results; one support-gating evaluation has no retained numeric performance and an unknown failure cause. It is not a measured loss.', ['result.total_attempts','result.total_evaluated_programs'], ['paper_data.json:1'])
    add('Manifest records current CC0-1.0 evidence and Apache-2.0 metadata but absence of a results license at the pinned snapshot; historical licensing remains qualified.', episodes, ['source_evidence/resources/final/manifest.json:1'])
    references = json.loads(Path('references_provenance.json').read_text())['references']
    for reference in references:
        claims.append(dict(claim='Literature positioning limited to consulted content: ' + reference['title'], source_ids=[reference['id']], citation_keys=[reference['citation_key']], source_locations=[reference['evidence_path']]))
    Path('claims_grounding.json').write_text(json.dumps(dict(claims=claims), indent=2))


if __name__ == '__main__':
    main()
