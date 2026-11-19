"""Matrix settings, fixed by rules that see only the missingness pattern (never the scores)."""
import numpy as np
from mteb_matrix import load_long, wide, peel, task_type


def mteb_setting(name, col='main_score', path='data/mteb_long.parquet'):
    """returns dict(X raw (M,N) with NaN, obs, models, tasks, ttype, cost (N,) median eval time)."""
    d = load_long(path)
    X = wide(d, 'main_score')                        # the block is defined by missingness of the primary score only
    Xv = wide(d, col).reindex(index=X.index, columns=X.columns)       # values: ablation columns (main_score_first) share that block
    ev = d.pivot_table(index='model', columns='task', values='evaluation_time', aggfunc='mean').reindex(index=X.index, columns=X.columns)
    obs = X.notna().values
    if name == 'A1':        # full peel: largest complete block reachable by lowest-coverage peeling
        r, c = peel(obs)
    elif name == 'A2':      # 30 most-covered tasks x all models complete on them
        c = np.argsort(-obs.sum(0), kind='stable')[:30]
        r = np.where(obs[:, c].all(1))[0]
    elif name == 'B':       # sparse: tasks with >= 40 models; models with >= 5 kept tasks
        c = np.where(obs.sum(0) >= 40)[0]
        r = np.where(obs[:, c].sum(1) >= 5)[0]
    else:
        raise ValueError(name)
    Xs = Xv.values[np.ix_(r, c)]
    tasks = list(X.columns[c])
    cost = np.nanmedian(ev.values[np.ix_(r, c)], axis=0)
    return dict(X=Xs, obs=~np.isnan(Xs), models=list(X.index[r]), tasks=tasks,
                ttype=np.array([task_type(t) for t in tasks]), cost=cost, name=name,
                groups=np.array([m.split('__')[0] for m in X.index[r]]))     # family = organisation prefix of the model id (as in E6)


def llm_setting(name):
    """Second-kind matrices (generative LLMs). Fixed by availability only. groups = family labels for group folds."""
    import pandas as pd
    if name == 'OLMB40':
        d = pd.read_parquet('data/llm_dense_olmb_subtasks.parquet')
        cols = [c for c in d.columns[3:43]]
        assert len(cols) == 40 and cols[0].startswith('bbh') and cols[-1] == 'mmlu_pro_acc'
        X = d[cols].values.astype(float); models = list(d.model_id)
        groups = d.family_group.fillna(d.model_id).astype(str).values
        tt = np.array([c.split('_')[0] for c in cols])
        dates = pd.to_datetime(d.upload_date, errors='coerce')
    elif name == 'HELMMMLU':
        d = pd.read_parquet('data/llm_dense_matrix.parquet')
        cols = [c for c in d.columns if c.startswith('mmlu_') and c != 'mmlu_all_subjects_em']
        X = d[cols].values.astype(float); models = list(d.model)
        groups = d.creator_organization.astype(str).values; tt = np.array(['mmlu'] * len(cols))
        dates = pd.to_datetime(d.release_date, errors='coerce')
    elif name == 'HELMLITE':
        d = pd.read_parquet('data/helm_lite_matrix.parquet')
        cols = ['narrativeqa_f1', 'naturalquestions_openbook_f1', 'naturalquestions_closedbook_f1', 'openbookqa_em', 'mmlu_em',
                'math_equiv_cot', 'gsm8k_em', 'legalbench_em', 'medqa_em', 'wmt14_bleu4']
        X = d[cols].values.astype(float); models = list(d.model)
        groups = d.creator_organization.astype(str).values; tt = np.array(cols)
        dates = pd.to_datetime(d.release_date, errors='coerce')
    elif name == 'OLMB6':
        d = pd.read_parquet('data/olmb_matrix.parquet')
        cols = ['ifeval_norm', 'bbh_norm', 'math_lvl5_norm', 'gpqa_norm', 'musr_norm', 'mmlu_pro_norm']
        X = d[cols].values.astype(float); models = list(d.eval_name)
        groups = d.family_group.fillna(d.model_id).astype(str).values; tt = np.array(cols)
        dates = pd.to_datetime(d.submission_date, errors='coerce')
    elif name == 'LIVEBENCH':
        d = pd.read_parquet('data/livebench_matrix.parquet')
        cols = ['LCB_generation', 'coding_completion', 'connections', 'paraphrase', 'plot_unscrambling', 'story_generation', 'typos']
        X = d[cols].values.astype(float); models = list(d.model)
        groups = d.model.astype(str).str.split('-').str[0].values; tt = np.array(cols)
        dates = pd.to_datetime(d.first_tstamp, errors='coerce')
    else:
        raise ValueError(name)
    return dict(X=X, obs=~np.isnan(X), models=models, tasks=cols, ttype=tt, cost=None, name=name, groups=groups,
                date=dates.values.astype('datetime64[D]').astype(float))
