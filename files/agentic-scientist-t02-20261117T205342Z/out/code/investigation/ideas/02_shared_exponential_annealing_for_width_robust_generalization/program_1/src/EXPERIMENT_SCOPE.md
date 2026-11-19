# Shared exponential annealing: interface-limited candidate

Attempt: `cycle_02_shared_exponential_annealing_attempt_01`  
Idea: `cycle_02_shared_exponential_annealing`  
Program: `program_1`

## Implemented control

`program.py:handle` preserves the starter's entrypoint, request validation,
reset isolation, increasing block-step bookkeeping and exact response fields.
Every valid seed and workload receives `initial_lr=0.01`, `decay_rate=0.1`.
The only policy change from the incumbent is decay_rate from 1.0 to 0.1;
equivalent numeric literals in guards and scheduling use leading zeros.
The schedule remains exactly
`max(0.0001, min(0.01, initial_lr * decay_rate ** (step / steps)))`.
Normalization uses the supplied workload, including smoke workloads. There
are no added observations, diagnostic response keys or external training jobs.
The program specification is unchanged.

## Falsifiable prediction and limitations

The optimization hypothesis is that large early updates followed by smaller
late updates improve the official aggregate outcome relative to the incumbent
constant-rate controller. The operational prediction requires correctness and
the canonical improvement gate: combined_score greater than the supplied
incumbent value 0.0013285757680326544. That incumbent value is task-provided
context, not a measurement made during this preparation. A failed improvement
gate falsifies this candidate comparison; execution or correctness failure
leaves the optimization prediction unestablished.

The proposed balance between representation acquisition and late refinement is
untested. Annealing also changes cumulative learning rate, effective optimization
time and cumulative AdamW shrinkage, so any aggregate gain cannot isolate that
mechanism. The same recipe is applied across widths, operations and decay arms;
no such identities or observations enter the controller. An aggregate result
cannot establish a width interaction, grokking onset or independent-seed
uncertainty. Width-specific trajectories and a full research paper require
separately authorized experiments and observations unavailable at this stage.

## Evidence and reproduction status

No candidate code, tests, training, optimizer, benchmark or evaluation was
executed during preparation. Performance, statistical uncertainty and scientific
conclusions remain unknown; no paper or empirical findings are claimed.
The harness owns the only subsequent official evaluation. Reproduction uses
the unchanged documented reset/recipe/schedule RPC sequence. No external
sources were accessed and no forbidden literature was encountered.
