Superseded derived outputs, not final evidence. The first scale summary used
per-row rather than consistently vectorized mean-rank metadata. Floating point
reduction differences assigned 22 HELM models an extra rank, including its mean
leader; it incorrectly included that leader in the nonleading summary. Raw
optimization inputs and costs were unaffected (every model was optimized).
`src/fix_final_scale_ranks.py` corrected only rank_mean, preserving all other
CSV field text exactly, independently on the canonical and clean computations.
The source runner now uses the consistent mean vector directly. New final
summaries use corrected metadata, and their checker requires legacy denominator
agreement as well as median agreement. See final_scales_rank_repair.json.
