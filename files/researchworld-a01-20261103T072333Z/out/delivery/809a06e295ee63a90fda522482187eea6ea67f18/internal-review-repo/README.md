# Independent review records

Commitment: Forgejo issue #3. Technical audit: [reviews/analysis-v1.md](reviews/analysis-v1.md), with independent saved-result checks and reproduced-data hashes. This repository records evidence and findings; approval of a complete version occurs only through review of its exact paper-repo release/final PR head.

The independent verifier takes an analysis-package directory, for example:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/audit_analysis_v1.py /path/to/experiment-repo
```

It requires NumPy, pandas and SciPy from the research environment. Private raw downloads and source copies are excluded under `work/`.
