# Capacity versus decay clock: interface-limited candidate

Attempt: `cycle_01_capacity_decay_clock_attempt_01`  
Idea: `cycle_01_capacity_decay_clock`  
Program: `program_1`

## Implemented control

`program.py:handle` retains the starter's exact reset/recipe/schedule contract,
validation and state transitions. Every seed and workload receives the same
recipe: `initial_lr=0.01`, `decay_rate=1.0`. The prescribed schedule therefore
returns the constant rate `0.01`. There are no extra response fields, external
dependencies, hidden observations or self-owned training jobs.

The scientific motivation is a fixed-rate decay clock. For constant learning
rate eta and fixed AdamW decay lambda with 0 <= eta*lambda < 1, the cumulative
shrinkage clock is `-step*log1p(-eta*lambda)`. Raising eta increases that clock
per update when lambda is positive; zero decay remains zero. This algebra does
not imply improved accuracy: changing eta also changes gradient updates and
stability. The recipe uses the permitted maximum to provide more decay exposure
within the fixed training budget, not a measured optimum. It differs from the
original proposed learning rate of 0.001 and is not a confirmatory test of that
proposal. The actual decay values are not supplied to this controller.

## Scientific work not implementable through this interface

The proposed experiment uses modular addition p=31, training fraction 0.4,
widths 16/32/64/128 and five paired seeds. It requires label-free initial-logit
calibration, a separate pilot, independently randomized-label fitting controls,
zero/positive-decay interventions, sustained 0.99 crossing measurements,
administrative censoring, paired-seed bootstrap intervals and saved run records.
None of these controls or observations is exposed by the RPC interface.
The documented evaluator instead owns its 194-input/97-logit network family,
data, optimizer, training and measurements. This candidate does not substitute
the proposed settings, invent additional RPC inputs, or claim to run those
experiments. It cannot log an exact observed decay clock without decay inputs.

The original falsifiable prediction remains untested: wider fitting-capable
networks should fit true and random labels earlier, while true-label
generalization times remain within a factor of two over an eightfold width
range, with an uncertainty interval contained inside that equivalence region.
A fixed-rate controller alone cannot establish, reject or quantify that claim.

## Evidence and reproduction status

No candidate code, tests, training, optimizer, benchmark or evaluation was
executed during preparation. No performance improvement, confidence interval,
paper, figure, or empirical research conclusion is claimed. The harness owns
the subsequent official evaluation. No external sources were retrieved and no
forbidden literature was encountered. Reproduction of the implemented policy
requires only the starter's documented RPC sequence; seed values affect neither
the recipe nor the schedule. A research paper would require actual experiments
and evidence not available at this stage.
