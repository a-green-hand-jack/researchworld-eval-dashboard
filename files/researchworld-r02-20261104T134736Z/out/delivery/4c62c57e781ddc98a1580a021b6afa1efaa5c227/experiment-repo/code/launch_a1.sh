#!/bin/bash
# Prints the (TAG REPS CONFIG) manifest of the A1 grid; each line is passed to run_a1.sh.
L=0.69314718  # unused
for k in dirichlet logisticnormal; do
  for hf in "0 linear" "0.5 linear" "1.0 linear" "0.5 quad"; do set -- $hf
    echo "A1_${k}_K3_h$1_$2 200 {\"kind\":\"$k\",\"K\":3,\"hetero\":$1,\"form\":\"$2\"}"; done
  for h in 0 0.5; do echo "A1_${k}_K5_h${h}_linear 100 {\"kind\":\"$k\",\"K\":5,\"hetero\":$h}"; done
  echo "A1_${k}_K10_h0.5_linear 100 {\"kind\":\"$k\",\"K\":10,\"hetero\":0.5,\"volume\":false}"
done
echo 'A1_dirichlet_K3_h0.5_prec5 100 {"kind":"dirichlet","K":3,"hetero":0.5,"a":1.6094379}'
echo 'A1_dirichlet_K3_h0.5_prec80 100 {"kind":"dirichlet","K":3,"hetero":0.5,"a":4.3820266}'
echo 'A1_logisticnormal_K3_h0.5_sig1.0 100 {"kind":"logisticnormal","K":3,"hetero":0.5,"s":0.0}'
echo 'A1_logisticnormal_K3_h0.5_sig0.25 100 {"kind":"logisticnormal","K":3,"hetero":0.5,"s":-1.3862944}'
echo 'A1_dirichlet_K3_h0.5_prec5_round2 100 {"kind":"dirichlet","K":3,"hetero":0.5,"a":1.6094379,"digits":2}'
echo 'A1_logisticnormal_K3_h0.5_sig1.0_round2 100 {"kind":"logisticnormal","K":3,"hetero":0.5,"s":0.0,"digits":2}'
