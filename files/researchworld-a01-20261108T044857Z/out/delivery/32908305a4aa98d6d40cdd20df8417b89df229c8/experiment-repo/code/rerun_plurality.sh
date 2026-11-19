#!/bin/bash
# Plurality-only reruns (fast: about a minute each) into results/plur/, then patched into the run files with code/patch_rule_rows.py.
# Launch from the repository root; each line is one job on `local-compute`. Used after every change of the plurality solver.
cd /hutian/repo
R=results; P=results/plur; S3="2,3,5,10,20,50,100"; SH="2,3,5,10,20,40"; mkdir -p $P
launch() { name=$1; shift; ht-resource run local-compute --note "plurality rerun v2: $name" -- bash -c "cd /hutian/repo && $* > logs/plur_$name.log 2>&1" | grep '"ref"'; }
launch ollb_ord50 "python3 -u code/run_core.py ollb emp99,ceil plurality top50 $P/ollb_primary_ordinal_top50.csv"
launch helm_primary "python3 -u code/run_core.py helm emp99T,emp99P,emp95T plurality all $P/helm_primary.csv"
launch helm_capsweep "python3 -u code/run_core.py helm ceil,front0,gain5,gain10,gain20 plurality all $P/helm_capsweep.csv"
launch top500 "python3 -u code/run_core.py ollb_top500 emp99,ceil plurality all $P/var_ollb_top500.csv"
launch rob_ollb_noise_ord "python3 -u code/run_robust.py noise ollb plurality emp99 $P/rob_ollb_noise_ord_emp99.csv --R 60 --strata $S3"
launch rob_ollb_taskboot_ord "python3 -u code/run_robust.py taskboot ollb plurality emp99 $P/rob_ollb_taskboot_ord_emp99.csv --R 60 --strata $S3"
launch rob_helm_noise "python3 -u code/run_robust.py noise helm plurality emp99T $P/rob_helm_noise_emp99T.csv --R 200 --strata $SH"
launch rob_helm_taskboot "python3 -u code/run_robust.py taskboot helm plurality emp99T $P/rob_helm_taskboot_emp99T.csv --R 200 --strata $SH"
launch rob_helm_tasksub "python3 -u code/run_robust.py tasksub helm plurality emp99T $P/rob_helm_tasksub_emp99T.csv --R 60"
launch rob_helm_tasksubcommon "python3 -u code/run_robust.py tasksub_common helm plurality emp99T $P/rob_helm_tasksubcommon_emp99T.csv --R 60"
launch survival_ollb "python3 -u code/run_survival.py ollb $P/survival_ollb_emp99.csv --R 300"
launch survival_helm "python3 -u code/run_survival.py helm $P/survival_helm_emp99.csv --R 200"
