# Voluntary self-audit checklist (not an ICLR 2027 requirement)

ICLR 2027 has no mandatory paper checklist. `deliverable.md` asks for the venue's checklist "if the venue requires one"; to still make the review criteria checkable, `paper-repo` may reproduce the following in the appendix (after the bibliography, outside the page limit), labelled "voluntary self-audit; not an ICLR form". Each item is answered Yes / No / N/A with the section or file that backs it, and "No" is written down rather than hidden.

1. Claims in the abstract and introduction match the evidence and its scope (which datasets, which k range, which split).
2. Limitations and failure cases are discussed (distribution shift, sparsity, mixed scales, small-N secondary leaderboards).
3. Theory: assumptions stated, proofs in the appendix, and the check against synthetic and real matrices reported.
4. Experimental setting: data versions (pinned SHAs), preprocessing, split protocol, selection of k, baselines and tuning are specified.
5. Uncertainty: repeats, seeds, confidence intervals / paired tests are reported for every headline comparison.
6. Compute: CPU only; runtime and hardware stated.
7. Code and data: scripts, environment lock, run commands, and the script-to-table/figure map are shipped; licences of the data are stated (several leaderboards declare none).
8. Every number, table and figure traces to a shipped script; no placeholder or illustrative numbers are presented as measured.
9. Citations: only works actually consulted; the forbidden-content log is stated.
10. Failed, abandoned and unfinished runs are reported as such.
