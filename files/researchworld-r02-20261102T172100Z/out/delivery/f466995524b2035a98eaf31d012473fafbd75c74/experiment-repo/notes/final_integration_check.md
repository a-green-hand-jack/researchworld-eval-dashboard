# Analysis-owner check of the integrated manuscript

Checked paper-repo main `a71cdc607a6477ed8aa249ad218f456f141cc080`, fetched during activation `852239e9f89ea96c442a8731867c2f5e`. This checks the answer to paper-repo#20 against the actual delivered root PDF, not an earlier manuscript draft. Root `paper.pdf` SHA-256: `b167d4d11410cbce913a5439d3b7b76cdcb12f7b6a2250b64198fd2d45f3039f`.

Re-read experiment-repo#1 Research objective, the completed commitment (#2), the context Brief and the supplied analysis evidence map. The analysis scope remains a reproducible, uncertainty-qualified synthetic study of observed composition responses. No further experiment is required by this integration check.

## Corrections requested in paper-repo#20

Both are resolved in the actual PDF extracted with `pdftotext -layout`:

- Main design chronology (p4, lines141–147) explicitly says the plan owner had not inspected core outcomes when requesting TV/KL, whereas analysis had inspected core/oracle outcomes before freezing those source-driven additions. The supplement's own outcomes were unknown when frozen. The text no longer represents the extension as fully blind or part of the original core.
- Abstract, main scope/results/limitations, appendix B and Figure6 distinguish direct original-clr membership from the inverse-image region `{y:T_epsilon(y) in C_epsilon(x)}`. The latter has exactly the measured transformed event and hence the same original-response coverage and CI, including zeros. The main results give `0.8990 [0.8954, 0.9026]` for the K10/epsilon1e-8 inverse image and distinguish the direct-clr diagnostic `0.4721 [0.4702, 0.4740]`. They correctly assert neither new simulation nor measured original-simplex area for the inverse image.

## Numerical handoff verification

Used `git show origin/main:<path>` to compare every delivered file under `analysis/` and `results/` against experiment-repo main: **55 files, zero differences**. Recomputed every entry of `manuscript/claim_provenance.json` from the recorded result file and exact filters/columns: **45 claims, all hashes/selectors/printed values match**. This was a deterministic file/provenance verification, not repeated numerical experiments.

Read the actual PDF's principal result and interpretation passages against `analysis/evidence_map.md`: simultaneous versus coordinate coverage; low/high observed-group results and the negative learned-scale result at K10; paired common-area comparisons and unresolved orderings; TV/raw-max duplication and forward-KL control; paired mixture-shift loss, oracle marginal restoration and oracle group miss; realized-calibration finite-test diagnostics; rank/tie/infinite behavior; boundary/replacement distinctions; and independent-replication, pointwise uncertainty. These agree with the supplied evidence and its stated limits. Table3 preserves the source-driven chronology, non-independent K3 TV geometry and unresolved area contrasts.

The requested analysis corrections are satisfied, and the integrated numerical claims checked here are supported by the supplied analysis. No analysis revision or new resource computation is pending from this check. This is an analysis-owner handoff check; the report/presentation owners retain their functions and independent final acceptance remains with internal-review-repo.
