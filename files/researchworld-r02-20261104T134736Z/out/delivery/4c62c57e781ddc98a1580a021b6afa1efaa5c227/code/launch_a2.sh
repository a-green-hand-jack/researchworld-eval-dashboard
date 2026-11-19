#!/bin/bash
# Manifest for A2 extensions: alpha, K, and tie/discretisation cases (TAG REPS CONFIG), methods limited, no volume.
M='"methods":["euc","l1","hell","aitch","kl_rev","euc/n","aitch/nq","dirnll"],"volume":false,"n_te":2000'
for n in 50 200 1000; do
  for al in 0.05 0.2; do echo "A2x_dirichlet_K3_n${n}_alpha${al} 2000 {\"kind\":\"dirichlet\",\"K\":3,\"hetero\":0.5,\"n_cal\":$n,\"alpha\":$al,$M}"; done
  for K in 5 10; do echo "A2x_dirichlet_K${K}_n${n} 2000 {\"kind\":\"dirichlet\",\"K\":$K,\"hetero\":0.5,\"n_cal\":$n,$M}"; done
  for dg in 1 2 3; do echo "A2x_dirichlet_K3_prec5_n${n}_round${dg} 2000 {\"kind\":\"dirichlet\",\"K\":3,\"hetero\":0.5,\"a\":1.6094379,\"n_cal\":$n,\"digits\":$dg,$M}"; done
done
