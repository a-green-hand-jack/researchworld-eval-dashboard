# Paper validation feedback

- generated_at: 2026-11-11T13:02:34.319960+00:00
- paper_dir: `work/results/r03/claude/20261111_111139/paper`
- ok: `False`

## Hard errors
- figure validation failed: figure_manifest.json failed schema validation: figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].path_png: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].n_panels: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].panels_per_row: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].categories_per_panel: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].series_per_panel: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].max_label_chars: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].font_sizes: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].uses_abbrev_labels: Field required; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].files: Extra inputs are not permitted; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].panel_count: Extra inputs are not permitted; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].panels: Extra inputs are not permitted; figures.0.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].required: Extra inputs are not permitted; figures.0.function-after[validate_panel_lengths(), RichFigureManifestFigure]: Value error, either font_sizes or min_font_size_pt must be provided; Missing required figure from strategy: protocol_overview; Missing required figure from strategy: main_results; paper.tex references figure missing from figure_manifest.json: figures/protocol_overview.png; paper.tex references figure missing from figure_manifest.json: figures/main_results.pdf

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `6204`
- substantive_element_count: `9`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/r03/claude/20261111_111139/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/r03/claude/20261111_111139/paper/scientific-evidence/verification-report.json`
- total_references: `52`
- resolved_references: `17`
- anchored_references: `35`
- dangling_references: `0`
- manifests_checked: `3`
