"""Render supplied rank, boundary, oracle and calibration-tail evidence."""
import argparse, hashlib, json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from render import select, save, SHORT

CLR=['clr_l2','clr_scaled','clr_mondrian']
COLORS=['#0072B2','#D55E00','#009E73']


def boundary(summary,root):
    fig,axs=plt.subplots(2,2,figsize=(5.5,4.1),constrained_layout=True)
    for i,k in enumerate([3,10]):
        for j,target in enumerate(['zeros_transformed','zeros_original_clr_diagnostic']):
            ax=axs[i,j]
            for m,c,ls in zip(CLR,COLORS,['-','--',':']):
                rows=select(summary,k=k,ncal=499,scenario=target,shift=False,alpha=.1,method=m,metric='coverage').sort_values('epsilon')
                if len(rows)!=3: raise ValueError('Expected three prespecified epsilon values')
                ax.errorbar(rows.epsilon,rows['mean'],yerr=[rows['mean']-rows.ci_low,rows.ci_high-rows['mean']],color=c,ls=ls,marker='o',ms=3,lw=1.1,label=SHORT[m])
            if j:
                rows=select(summary,k=k,ncal=499,scenario='zeros_original_raw',shift=False,alpha=.1,method='raw_l2',metric='coverage').sort_values('epsilon')
                if len(rows)!=3: raise ValueError('Missing raw original-target reference')
                ax.errorbar(rows.epsilon,rows['mean'],yerr=[rows['mean']-rows.ci_low,rows.ci_high-rows['mean']],color='.25',ls='-.',marker='^',ms=3,lw=1,label='Raw Euclidean, original')
            ax.axhline(.9,color='.3',ls=(0,(3,2)),lw=.8)
            ax.set_xscale('log'); ax.set_xticks([1e-8,1e-4,1e-2])
            ax.set_ylim(0,1.02); ax.grid(axis='y',color='.9',lw=.5)
            ax.set_title(f'K={k}, '+('transformed / pullback' if j==0 else 'direct original check'),loc='left')
            ax.set_xlabel(r'Replacement $\epsilon$')
            if j==0: ax.set_ylabel('Simultaneous coverage')
    handles,labels=axs[0,1].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False,fontsize=7.5)
    save(fig,'boundary_targets',root)
    caption=(r'\textbf{Replacement changes the coverage target.} Exact zeros arise by censoring components below 0.025 and reclosing. '
             r'The fixed transform is $T_\epsilon(y)_j=\max(y_j,\epsilon)/\sum_l\max(y_l,\epsilon)$. '
             r'Left: clr methods calibrate and test on $T_\epsilon(Y)$. These same values and intervals exactly equal original-response coverage of the inverse-image region $\{y:T_\epsilon(y)\in C_\epsilon(x)\}$ by event identity; this is not another simulation. Right: those same finite clr regions are tested against original $Y$, rejecting boundary points, '
             r'while the raw Euclidean reference separately calibrates and tests on original $Y$. All fits use transformed training responses. '
             r'Dots are means and bars pointwise 95\% $t$ intervals across 50 independent datasets, with 1000 training, 499 calibration and 5000 iid test observations each. '
             r'The same original datasets are reused across replacement values. The dashed line marks 0.90; the original-clr check has no nominal guarantee. '
             r'The right-panel diagnostic is a different region from the left-panel inverse image. Replacement does not inherently prevent coverage of original zeros. No inverse-image area was estimated, and this censoring test does not establish structural-zero performance.')
    (root/'figures'/'boundary_targets_caption.tex').write_text(caption+'\n')
    summary.to_csv(root/'tables'/'boundary_estimates.csv',index=False)


def oracle(summary,paired,root):
    methods=['clr_l2','clr_mondrian','clr_weighted']
    fig,axs=plt.subplots(2,2,figsize=(5.5,4),constrained_layout=True)
    for j,k in enumerate([3,10]):
        cell=select(summary,k=k,ncal=499,scenario='heterogeneous',shift=True,alpha=.1,epsilon=1e-6)
        for metric,offset,color,marker,label in [('coverage',-.1,'#0072B2','o','Marginal'),('coverage_g1',.1,'#D55E00','s','Group 1')]:
            for y,m in enumerate(methods):
                rows=select(cell,method=m,metric=metric)
                if len(rows)!=1: raise ValueError('Missing oracle coverage cell')
                r=rows.iloc[0]
                axs[0,j].plot([r.ci_low,r.ci_high],[y+offset]*2,color=color,lw=1.1)
                axs[0,j].plot(r['mean'],y+offset,marker=marker,color=color,ms=4,label=label if y==0 else None)
        axs[0,j].set_yticks(range(3),[SHORT[m] for m in methods] if j==0 else ['']*3)
        axs[0,j].set_ylim(2.5,-.5); axs[0,j].axvline(.9,color='.3',ls='--',lw=.8)
        axs[0,j].set_xlim(0,1.02); axs[0,j].set_xticks([0,.5,1])
        axs[0,j].set_title(f'{chr(97+j)}) Shifted coverage, K={k}',loc='left')
        axs[0,j].set_xlabel('Simultaneous coverage')
    cell=select(summary,k=3,ncal=499,scenario='heterogeneous',shift=True,alpha=.1,epsilon=1e-6,metric='volume_fraction')
    for y,m in enumerate(methods):
        r=select(cell,method=m).iloc[0]
        axs[1,0].plot([r.ci_low,r.ci_high],[y]*2,color='#0072B2',lw=1.1)
        axs[1,0].plot(r['mean'],y,'o',color='#0072B2',ms=4)
    axs[1,0].set_yticks(range(3),[SHORT[m] for m in methods]); axs[1,0].set_ylim(2.5,-.5)
    axs[1,0].set_xlim(left=0); axs[1,0].set_title('c) Shifted area, K=3',loc='left'); axs[1,0].set_xlabel('Fraction of simplex area')
    cell=select(paired,k=3,ncal=499,scenario='heterogeneous',shift=True,alpha=.1,epsilon=1e-6,method_a='clr_weighted',metric='volume_fraction')
    for y,b in enumerate(['clr_l2','clr_mondrian']):
        rows=select(cell,method_b=b)
        if len(rows)!=1: raise ValueError('Missing paired oracle area contrast')
        r=rows.iloc[0]
        axs[1,1].plot([r.ci_low,r.ci_high],[y]*2,color='#0072B2',lw=1.1)
        axs[1,1].plot(r.mean_difference,y,'o',color='#0072B2',ms=4)
    axs[1,1].set_yticks([0,1],['Oracle − global','Oracle − group']); axs[1,1].set_ylim(1.5,-.5)
    axs[1,1].axvline(0,color='.3',ls='--',lw=.8); axs[1,1].set_title('d) Paired area differences',loc='left'); axs[1,1].set_xlabel('Area difference')
    handles,labels=axs[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
    save(fig,'oracle_shift',root)
    caption=(r'\textbf{Known-ratio weighting under the controlled mixture shift.} Heterogeneous mechanism, calibration size 499; test group-1 probability changes from 0.2 to 0.8 with within-group laws fixed. '
             r'Panels (a,b) show shifted marginal and higher-noise-group joint coverage; (c) shows shifted-feature-averaged Euclidean simplex-area fractions at $K=3$; '
             r'(d) shows within-seed paired oracle-minus-global and oracle-minus-group area differences. Dots/bars are means/pointwise 95\% $t$ intervals across independent dataset replications, not simultaneous bands. '
             r'Oracle weights use exact generator density ratios with test weight at infinity. This does not evaluate learned ratios or arbitrary-shift robustness. Area needs the coverage context in (a,b).')
    (root/'figures'/'oracle_shift_caption.tex').write_text(caption+'\n')


def tables(rank,diagnostics,shifts,root):
    rank.to_csv(root/'tables'/'rank_checks.csv',index=False)
    diagnostics.to_csv(root/'tables'/'calibration_diagnostics.csv',index=False)
    shifts.to_csv(root/'tables'/'paired_shift_estimates.csv',index=False)
    lines=[r'\begin{longtable}{rrlrrrr}',r'\toprule',r'$n$ & $\alpha$ & Scores & Rank & Theory & Test [95\% CI] & Calibration [95\% CI] \\',r'\midrule',r'\endhead']
    for _,r in rank.sort_values(['law','alpha','ncal']).iterrows():
        idx=r'$\infty$' if r.infinite_threshold else str(int(r['rank']))
        test=f'{r.test_coverage:.4f} [{r.test_ci_low:.4f}, {r.test_ci_high:.4f}]'
        calibration=f'{r.calibration_coverage_mean:.3f} [{r.calibration_ci_low:.3f}, {r.calibration_ci_high:.3f}]'
        lines.append(f'{int(r.ncal)} & {r.alpha:g} & {r.law} & {idx} & {r.theory_coverage:.3f} & {test} & {calibration}'+r' \\')
    lines += [r'\bottomrule',r'\end{longtable}']
    (root/'tables'/'rank_checks.tex').write_text('\n'.join(lines)+'\n')
    (root/'tables'/'rank_checks_caption.tex').write_text(r'\textbf{Finite ranks and ties.} Each row uses 20,000 independent trials. Rank is $\lceil(n+1)(1-\alpha)\rceil$; $\infty$ denotes the whole-domain fallback. Theory is exact expected coverage including conservative Bernoulli ties. Test intervals are 95\% Wilson; calibration coverage (CDF at the threshold) has a pointwise 95\% $t$ interval for its trial mean. Variance checks and seeds remain in \texttt{tables/rank\_checks.csv}.'+'\n')
    cell=select(diagnostics,scenario='heterogeneous',shift=False,alpha=.1,epsilon=1e-6)
    cell=cell[cell.method.isin(CLR)].sort_values(['k','ncal','method'])
    lines=[r'\begin{tabular}{rrlrr}',r'\toprule',r'$K$ & $n$ & Method & Coverage 10th percentile & Fraction below .85 [95\% CI] \\',r'\midrule']
    for _,r in cell.iterrows():
        p=r.empirical_fraction_below_nominal_minus_05
        lines.append(f'{int(r.k)} & {int(r.ncal)} & {SHORT[r.method]} & {r.coverage_q10:.3f} & {p:.2f} [{r.fraction_below_tolerance_ci_low:.2f}, {r.fraction_below_tolerance_ci_high:.2f}]'+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (root/'tables'/'calibration_tails.tex').write_text('\n'.join(lines)+'\n')
    (root/'tables'/'calibration_tails_caption.tex').write_text(r'\textbf{Finite-test lower tails across calibrated datasets.} Heterogeneous iid cells; 100 independent replications each. The coverage 10th percentile is descriptive; the fraction of replications with 5000-test-point coverage below .85 has a pointwise 95\% Wilson interval. These are not certified population conditional-coverage probabilities because finite-test noise remains. Full diagnostics and infinite-region counts are in \texttt{tables/calibration\_diagnostics.csv}.'+'\n')


def prior_area(paired,root):
    """All supplied source-score comparisons at the main calibration size."""
    lines=[r'\begin{tabular}{llrr}',r'\toprule',r'Mechanism & Area difference & IID [95\% CI] & Shifted [95\% CI] \\',r'\midrule']
    for scenario in ['homogeneous','heterogeneous']:
        for a in ['tv','kl_forward']:
            for b in ['raw_l2','raw_linf','clr_l2']:
                values=[]
                for shift in [False,True]:
                    rows=select(paired,k=3,ncal=499,scenario=scenario,shift=shift,epsilon=1e-6,alpha=.1,method_a=a,method_b=b,metric='volume_fraction')
                    if len(rows)!=1: raise ValueError('Missing prior-score paired area comparison')
                    r=rows.iloc[0]
                    values.append(f'{r.mean_difference:.4f} [{r.ci_low:.4f}, {r.ci_high:.4f}]')
                label={'raw_l2':'Euclidean','raw_linf':'Maximum','clr_l2':'Aitchison'}[b]
                lines.append(scenario+' & '+('TV' if a=='tv' else 'KL')+' $-$ '+label+' & '+' & '.join(values)+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (root/'tables'/'prior_score_area.tex').write_text('\n'.join(lines)+'\n')
    (root/'tables'/'prior_score_area_caption.tex').write_text(r'\textbf{Source-driven score controls under a shared fitted predictor.} $K=3$, calibration size 499; paired within-seed area differences with pointwise 95\% $t$ intervals over 100 independent datasets. Negative values favor the first score only for the chosen uniform Euclidean simplex-area measure; judge them with subgroup and shifted coverage, not alone. Intervals including zero leave the ordering unresolved. TV is exactly raw maximum at $K=3$, including the zero paired differences shown here; these are not independent geometries. KL is forward $D_{\rm KL}(y\Vert\hat\mu)$. These controls were requested from permitted prior work after core results were inspected, before their own outcomes were known; they compare scores, not the prior study full fitted pipeline. Candidate-resolution diagnostics and all other cells are in \texttt{tables/area\_precision.csv} and \texttt{tables/paired\_method\_estimates.csv}.'+'\n')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--results-root',required=True,type=Path); ap.add_argument('--output-root',required=True,type=Path); ap.add_argument('--source-commit',required=True); args=ap.parse_args()
    root=args.output_root
    for name in ['figures','tables']: (root/name).mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'axes.spines.right':False,'axes.spines.top':False})
    paths=['main_summary/summary.csv','main_summary/paired_contrasts.csv','main_summary/diagnostics.csv','main_summary/shift_contrasts.csv','boundary_summary/summary.csv','rank_checks.csv','boundary_summary/epsilon_contrasts.csv','boundary_summary/zero_prevalence.csv','boundary_summary/pullback_equivalence.csv','main_summary/area_precision.csv']
    summary,paired,diagnostics,shifts,zeros,rank,epsilon,prevalence,pullback,precision=[pd.read_csv(args.results_root/p) for p in paths]
    epsilon.to_csv(root/'tables'/'paired_epsilon_estimates.csv',index=False)
    prevalence.to_csv(root/'tables'/'zero_prevalence.csv',index=False)
    pullback.to_csv(root/'tables'/'pullback_equivalence.csv',index=False)
    precision.to_csv(root/'tables'/'area_precision.csv',index=False)
    paired.to_csv(root/'tables'/'paired_method_estimates.csv',index=False)
    prior_area(paired,root)
    oracle(summary,paired,root); boundary(zeros,root); tables(rank,diagnostics,shifts,root)
    manifest={'source_repository':'world/experiment-repo','source_commit':args.source_commit,'inputs':{p:hashlib.sha256((args.results_root/p).read_bytes()).hexdigest() for p in paths},'generator':'presentation/supplement.py','notes':'Uses supplied estimates without re-estimating analysis. No pilot inputs.'}
    (root/'figures'/'supplement_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
