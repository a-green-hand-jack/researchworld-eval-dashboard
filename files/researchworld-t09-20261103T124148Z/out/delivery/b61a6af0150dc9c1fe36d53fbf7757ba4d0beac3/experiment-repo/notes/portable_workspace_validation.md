# Portable clean-workspace postprocessing

Request: experiment#10 and paper#24. This packaging repair does not change the
scientific modules/configs, original raw results, numerical claim values, figure
inputs, or original numerical audit/findings source identities. The new helper
and launcher wrapper implement the full-layout workflow in delivery_reproduction.md.
Existing results-only workspaces can be prepared without rerunning their102cells.

Validation used a separate workspace with byte-copied existing corrected102-cell
raw/metadata/exact-risk inputs. It did not independently simulate a new full study.
The complete numerical pipeline ran with a Python interpreter audit hook denying
any open under original experiment results/notes or paper results/analysis. It
passed full checkpoint/ledger,40800assignment integer-boundary, raw-to-summary,
676164supplementary arithmetic and graph-dependency audits, regenerated all94claim
routes, and actually computed the selected four-cell replay (115200rows;99.77s).
Summed pipeline-stage wall time was737.48s. These are this packaging validation's
measurements, separate from the original study's resource accounting.

All18summary/diagnostic CSVs match original bytes. All309production input files
(306raw/metadata/exact artifacts plus three configs) and27original numerical
receipt/reference files match their pre-run copies. A negative control confirms
the interpreter hook rejects an attempted original-results read. Source-layout
smoke checks confirm preparation copies no results, refuses existing receipts,
and fails on empty input instead of falling back to delivered results. The13
scientific tests and the presentation corrected-supply provenance guard pass.

The tracked outer validation job job-fe84db7aa4 ended with an immutability-assertion
failure **after** the workspace pipeline passed. Its initial snapshot also watched
Markdown instructions being edited during this repair. Comparing every reference
file established delivery_reproduction.md is the only original reference difference;
all numerical evidence is unchanged. A separate immutable-evidence/output verifier
passed, with no expensive computational stage repeated. This harness failure is
preserved and is not relabeled a successful resource job.

The first full pipeline used a temporary explicit-root extension to final_report.py.
To preserve the existing presentation source-hash contract, the final helper instead
invokes the unmodified findings script from its copied workspace location, which
natively selects that workspace. This final command was separately executed under
the same evidence-access guard; findings, findings_manifest and claim CSV match
original bytes. Other numerical stage commands are unchanged. The launcher source
binding was checked using intercepted child commands; no full production rerun is
claimed. The final package preserves all six checked audit/findings scripts exactly.

portable_workspace_validation.json contains the actual pipeline receipts, exact
CSV/input hashes,27receipt checks, replay details, guard negative control and native
findings verification. Fresh workspace receipts are separate from original receipts,
which remain history under analysis/reference_delivery. For a new host, actual raw
simulation timings stay in its own metadata and postprocessing timings in its own
workspace_postprocessing.json; original job ids/timings are not new-host evidence.

This supplies a reproducible workflow and internal packaging checks. Independent
release judgement and verification of the final report/guide remain with their owners.
