import hashlib
import json
import math
import re
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    data = json.loads((root / 'paper_data.json').read_text())
    # @evidence[[analysis/summary.json#/cell_rmse]] @evidence[[analysis/summary.json#/cell_signed_bias]]
    summary = json.loads((root / 'analysis/summary.json').read_text())
    methods = ['difference_in_means', 'own_treatment_ols', 'one_hop_ols']
    observations = {}
    for episode in data['final_evaluation']['evaluation_evidence']['episodes']:
        for case in episode['solution']['cases']:
            if case['kind'] != 'scientific':
                continue
            assert case['completed']
            validated = case['validated']
            errors = [validated['uncapped_error']]
            errors.extend(validated['baseline_estimates'][method] - validated['true_gate']
                          for method in methods)
            observations.setdefault((case['family'], case['mechanism']), []).append(errors)
    text = (root / 'paper.tex').read_text()
    table = text.split(r'\label{tab:cells}', 1)[1].split(r'\bottomrule', 1)[0]
    rows = [line for line in table.splitlines()
            if line.count('&') == 6 and 'ET bias' not in line]
    assert len(rows) == len(observations)
    checked_values = 0
    for index, row in enumerate(rows):
        family_index, condition_index = divmod(index, len(summary['conditions']))
        family = summary['families'][family_index]
        values = observations[(family, condition_index)]
        assert len(values) == summary['seed_count']
        rmse = [math.sqrt(sum(errors[column] ** 2 for errors in values) / len(values))
                for column in range(len(methods) + 1)]
        bias = sum(errors[0] for errors in values) / len(values)
        expected = rmse + [bias]
        derived = summary['cell_rmse'][family_index][condition_index] + [
            summary['cell_signed_bias'][family_index][condition_index][0]]
        assert all(math.isclose(actual, source, rel_tol=1e-12, abs_tol=1e-12)
                   for actual, source in zip(expected, derived))
        displayed = [float(re.sub(r'[^0-9.\-]', '', value))
                     for value in row.split('&')[2:]]
        assert len(displayed) == len(expected)
        assert displayed == [float(f'{value:.3f}') for value in expected], (family, row)
        checked_values += len(displayed)
    report = {
        'ok': True,
        'table_label': 'tab:cells',
        'rows_checked': len(rows),
        'numerical_cells_checked': checked_values,
        'decimal_places': 3,
        'summary_matches_recorded_episodes': True,
        'paper_sha256': hashlib.sha256((root / 'paper.tex').read_bytes()).hexdigest(),
        'new_scientific_evaluations': False,
    }
    output = root / 'analysis/table_precision_validation.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    provenance = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {
            'path': 'analysis/table_precision_validation.json',
            'kind': 'derived',
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        },
        'derived_from': ['@' + 'evidence[[' + target + ']]' for target in [
            'paper.tex', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes',
            'analysis/summary.json']],
        'generated_by': {'script_path': 'analysis/validate_table_precision.py'},
    }
    Path(str(output) + '.prov.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
