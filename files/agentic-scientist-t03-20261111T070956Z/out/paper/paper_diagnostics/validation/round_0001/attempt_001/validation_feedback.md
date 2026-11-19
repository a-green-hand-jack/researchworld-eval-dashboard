# Paper validation feedback

- generated_at: 2026-11-11T08:45:22.318270+00:00
- paper_dir: `work/results/t03/claude/20261111_071336/paper`
- ok: `False`

## Hard errors
- figure validation failed: figure_manifest.json failed schema validation: figures.1.function-after[validate_panel_lengths(), LegacyFigureManifestFigure].figure_type: Input should be 'grouped_bar', 'bar', 'line', 'box', 'violin', 'scatter', 'heatmap', 'table_matrix', 'table', 'composite' or 'diagram'; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].figure_type: Input should be 'grouped_bar', 'bar', 'line', 'box', 'violin', 'scatter', 'heatmap', 'table_matrix', 'table', 'composite' or 'diagram'; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].files: Field required; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].panel_count: Field required; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].panels: Field required; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].categories_per_panel: Extra inputs are not permitted; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].n_panels: Extra inputs are not permitted; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].path_pdf: Extra inputs are not permitted; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].path_png: Extra inputs are not permitted; figures.1.function-after[validate_panel_lengths(), RichFigureManifestFigure].series_per_panel: Extra inputs are not permitted; Missing required figure from strategy: protocol_overview; Missing required figure from strategy: main_comparison; paper.tex references figure missing from figure_manifest.json: figures/protocol_overview.png; paper.tex references figure missing from figure_manifest.json: figures/main_comparison.pdf; paper.tex references figure missing from figure_manifest.json: figures/error_accounting.pdf

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `6228`
- substantive_element_count: `10`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/t03/claude/20261111_071336/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t03/claude/20261111_071336/paper/scientific-evidence/verification-report.json`
- total_references: `60`
- resolved_references: `24`
- anchored_references: `36`
- dangling_references: `0`
- manifests_checked: `6`
