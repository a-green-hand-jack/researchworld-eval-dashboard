"""Planning calculations only: these are not empirical study results."""
import json
from math import ceil, sqrt
from scipy.stats import binom

rows=[]
for n in (20,99,100,499):
    k=ceil((n+1)*.9)
    sd=sqrt(k*(n+1-k)/((n+1)**2*(n+2)))
    rows.append(dict(calibration_n=n,score_coverage_sd=sd,
        R100_mean_normal_95_halfwidth=1.96*sd/sqrt(100),
        probability_group1_count_below_9=float(binom.cdf(8,n,.2))))
print(json.dumps(dict(kind='analytical planning calculation, not experiment',
    assumptions='iid continuous fixed trained score; alpha=.1; 100 independent calibrations; group probability .2; no finite-test noise included',
    calculations=rows,core_dataset_replications=100*2*2*2,
    core_method_environment_rows=100*2*2*2*7*2,
    low_dimensional_uniform_candidates=100*2*2*2*32*4096,
    amendment=dict(kind='v1.1 planning amendment; not measured runtime',
    low_dimensional_uniform_candidates_8192=100*2*2*2*32*8192,
    candidate_array_bytes_8192=32*8192*3*8,
    rows_eight_methods=800*2*8,rows_ten_methods=800*2*10)),indent=2))
