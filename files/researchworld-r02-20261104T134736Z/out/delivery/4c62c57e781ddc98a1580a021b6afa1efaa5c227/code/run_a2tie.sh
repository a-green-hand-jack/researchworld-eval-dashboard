#!/bin/bash
# A2 tie case: x-free DGP (wscale=0) with rounded compositions. MM=olsmean: fitted CLR-OLS mean (varies with x through estimation noise, scores
# stay continuous); MM=constmean: intercept-only mean model (predictions identical for all x, rounded targets give tied scores).
cd "$(dirname "$0")"
MM=$1; CM=false; [ "$MM" = constmean ] && CM=true
for d in 1 2; do for n in 50 200 1000; do
python3 -u -m cpsimplex.exp_a --config "{\"kind\":\"dirichlet\",\"K\":3,\"hetero\":0,\"wscale\":0.0,\"a\":1.6094379,\"digits\":$d,\"n_cal\":$n,\"n_tr\":500,\"n_te\":2000,\"alpha\":0.1,\"volume\":false,\"const_mean\":$CM,\"methods\":[\"euc\",\"aitch\",\"hell\"]}" \
  --reps 2000 --seed0 50000 --tag A2tie_${MM}_digits${d}_n${n} --out ../results/raw/A2tie_${MM}_digits${d}_n${n}.csv | tail -1
done; done
