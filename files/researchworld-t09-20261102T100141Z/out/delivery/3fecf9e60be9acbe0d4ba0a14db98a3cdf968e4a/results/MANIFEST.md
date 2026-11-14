# Manifest

Code revision at export: `a88fc0e8e2fda7fdc1fbd6b7f840193bda59d7c4`

Base seed: 20261102 (per cell/graph via numpy SeedSequence, see code/netgate/sim.py).

Inputs (sha256 verified against data.md): socfb-Stanford3.zip b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d; facebook_combined.txt.gz 125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7.

| experiment | cells | graph draws per cell | reps per graph draw | rows in replicates |
|---|---|---|---|---|
| E0_valid | 4 | [1, 4] | [500, 1000] | 34000 |
| E10_coverage | 16 | [10] | [300] | 96000 |
| E11_grapherr | 24 | [8, 12] | [40, 50] | 84480 |
| E1_size | 5 | [8] | [250] | 90000 |
| E2_degree | 12 | [8] | [250] | 216000 |
| E3_gamma | 6 | [8] | [250] | 108000 |
| E4_curv | 90 | [5] | [200] | 990000 |
| E5_graphs | 10 | [1, 8] | [250, 2000] | 180000 |
| E6_spec | 15 | [8] | [250] | 270000 |
| E7_model | 6 | [4] | [80] | 9600 |
| E8_design | 24 | [6] | [250] | 176235 |
| E9_noise | 9 | [8] | [250] | 162000 |
| MAIN | 72 | [1, 5] | [100, 500] | 504000 |
| MAIN_realdraws | 24 | [8] | [60] | 161280 |
| MAIN_s2 | 48 | [5] | [100] | 336000 |

Files: `replicates.parquet` (b3b609c9b183), `summary.csv` (0db562025893), `diagnostics.csv` (3632bb971500), `config.json` (0fabfff4778a)
