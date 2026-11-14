# Figure audit

- Executed plot script: yes.
- All numerical panels load executed CSV summaries, same parameter filters as tables.
- Scales: linear; optimism/width percentage points, coverage percent.
- Error bars: conditional Monte Carlo uncertainty only.
- Full synthetic grids are supplementary CSV, not silently omitted from claims.
- Exact and approximate methods distinguished by labels/markers.
- Boundary/real-coverage ranges include all displayed means and error bars.
- PNG and PDF files emitted at 300 dpi / vector.
- Initial failure-precision legend was detected as misaligned with plotted handles during visual inspection; fixed with explicit handles/labels from the boundary axes and re-rendered.
- Final PNGs and rendered PDF pages 1, 6, and 8 inspected; no clipping, overlapping data labels, or absent required legends observed. Coverage panels use common x/y scales.
- Official table captions moved above tables; full core longtable given an explicit caption. No overfull boxes or undefined-reference/citation warnings in final LaTeX log.
- Status: REPAIRED; final checks passed.
