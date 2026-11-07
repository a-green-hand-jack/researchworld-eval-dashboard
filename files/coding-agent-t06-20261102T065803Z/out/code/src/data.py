"""Frozen-snapshot loaders. No conversation content is exported."""
from pathlib import Path
import numpy as np
import pandas as pd
from bt import Panel

ROOT = Path(__file__).resolve().parents[1]


def make(name, d, home=False):
    d = d[d.model_a != d.model_b].copy()
    names = sorted(set(d.model_a) | set(d.model_b))
    idx = {s:i for i,s in enumerate(names)}
    a = d.model_a.map(idx).to_numpy(); b = d.model_b.map(idx).to_numpy()
    y = d.y.to_numpy().astype(float)
    # Canonical orientation so aggregation and order-invariance are explicit.
    swap = a > b
    aa = np.minimum(a,b); bb = np.maximum(a,b)
    y[swap] = 1-y[swap]
    h = d.home.to_numpy().astype(float) if home else None
    if home: h[swap] *= -1
    return Panel(name, names, aa, bb, y, d.cluster.to_numpy(), h)


def mt_frame(kind):
    d = pd.read_parquet(ROOT/f'data/raw/mt_{kind}.parquet')
    d['y'] = d.winner.map({'model_a':1.,'model_b':0.,'tie':.5,'tie (inconsistent)':.5})
    assert d.y.notna().all()
    swap = d.model_a > d.model_b
    a,b = d.model_a.copy(),d.model_b.copy()
    d.loc[swap,'model_a'] = b[swap];d.loc[swap,'model_b'] = a[swap]
    d.loc[swap,'y'] = 1-d.loc[swap,'y']
    d['cluster'] = d.question_id
    return d


def load_panels(matched=True):
    d = pd.read_csv(ROOT/'data/raw/arena.csv',usecols=[
        'id','model_a','model_b','winner_model_a','winner_model_b','winner_tie'])
    assert np.all(d[['winner_model_a','winner_model_b','winner_tie']].sum(axis=1)==1)
    d['y'] = d.winner_model_a+.5*d.winner_tie;d['cluster']=d.id
    panels=[make('Arena',d)]
    h,g = mt_frame('human'),mt_frame('gpt4')
    panels += [make('MT-human',h),make('MT-GPT4',g)]
    d = pd.read_csv(ROOT/'data/raw/nba.csv')
    d = d[(d._iscopy==0)&(d.is_playoffs==0)&(d.lg_id=='NBA')].copy()
    d['model_a']=d.team_id;d['model_b']=d.opp_id
    d['y']=(d.game_result=='W').astype(float);d['cluster']=d.game_id
    d['home']=d.game_location.map({'H':1.,'A':-1.,'N':0.})
    for year in range(2010,2016):
        panels.append(make(f'NBA-{year}',d[d.year_id==year]))
    if matched:
        hm,gm = matched_mt(20261102)
        panels += [make('Matched-human',hm),make('Matched-GPT4',gm)]
    return panels


def matched_mt(seed):
    h,g=mt_frame('human'),mt_frame('gpt4')
    keys=['question_id','turn','model_a','model_b']
    rng=np.random.default_rng(seed)
    h=h.assign(_u=rng.random(len(h))).sort_values('_u').drop_duplicates(keys)
    common=h[keys].merge(g[keys],on=keys).sort_values(keys)
    h=common.merge(h,on=keys);g=common.merge(g,on=keys)
    assert (h[keys].to_numpy()==g[keys].to_numpy()).all()
    return h,g


def nba_home(year):
    d=pd.read_csv(ROOT/'data/raw/nba.csv')
    d=d[(d._iscopy==0)&(d.is_playoffs==0)&(d.lg_id=='NBA')&(d.year_id==year)].copy()
    d['model_a']=d.team_id;d['model_b']=d.opp_id
    d['y']=(d.game_result=='W').astype(float);d['cluster']=d.game_id
    d['home']=d.game_location.map({'H':1.,'A':-1.,'N':0.})
    return make(f'NBA-{year}-home',d,True)
