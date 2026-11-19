"""CPU-only fixed snapshot preprocessing, no network. Units are explicit."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def canonical(df):
    df=df.copy(); swap=df.a>df.b
    aa=df.loc[swap,'a'].copy();df.loc[swap,'a']=df.loc[swap,'b'];df.loc[swap,'b']=aa
    df.loc[swap,'y']=1-df.loc[swap,'y']
    if 'home' in df: df.loc[swap,'home']=-df.loc[swap,'home']
    else: df['home']=0.
    return df

def mt_frame(path):
    raw=pd.read_parquet(path)
    vals={'model_a':1.,'model_b':0.,'tie':.5,'tie (bothbad)':.5,'tie (inconsistent)':.5}
    assert set(raw.winner)<=set(vals),set(raw.winner)
    df=pd.DataFrame(dict(a=raw.model_a,b=raw.model_b,y=raw.winner.map(vals),cluster=raw.question_id,turn=raw.turn,judge=raw.judge))
    def digest(c):
        return hashlib.sha256(json.dumps(list(c),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    df['ha']=raw.conversation_a.map(digest);df['hb']=raw.conversation_b.map(digest)
    swap=df.a>df.b
    ha=df.loc[swap,'ha'].copy();df.loc[swap,'ha']=df.loc[swap,'hb'];df.loc[swap,'hb']=ha
    return canonical(df),raw

def prepare():
    out=ROOT/'data'/'processed';out.mkdir(exist_ok=True)
    audit={}; sets={}
    x=pd.read_csv(ROOT/'data'/'arena.csv',usecols=['id','model_a','model_b','winner_model_a','winner_model_b','winner_tie'])
    assert (x[['winner_model_a','winner_model_b','winner_tie']].sum(axis=1)==1).all()
    counts=pd.concat([x.model_a,x.model_b]).value_counts();keep=set(counts[counts>=500].index)
    d=x[x.model_a.isin(keep)&x.model_b.isin(keep)&(x.model_a!=x.model_b)].copy()
    sets['arena']=canonical(pd.DataFrame(dict(a=d.model_a,b=d.model_b,y=d.winner_model_a+.5*d.winner_tie,cluster=d.id)))
    audit['arena']=dict(raw_rows=len(x),retained=len(d),threshold=500,original_models=len(counts),retained_models=len(keep),duplicate_ids=int(x.id.duplicated().sum()),excluded_models=sorted(set(counts.index)-keep))
    h,hr=mt_frame(ROOT/'data'/'mt_human.parquet');g,gr=mt_frame(ROOT/'data'/'mt_gpt4.parquet')
    sets['mt_human_raw']=h;sets['mt_gpt4_raw']=g
    keys=['cluster','a','b','turn','ha','hb']
    hh=h.groupby(keys,sort=True).agg(y=('y','mean'),raters=('y','size'),tie_rate=('y',lambda a:np.mean(a==.5))).reset_index()
    gg=g.groupby(keys,sort=True).agg(y=('y','mean'),raters=('y','size')).reset_index()
    j=hh.merge(gg,on=keys,suffixes=('_h','_g'),validate='one_to_one')
    sets['mt_human_match']=j[keys].assign(y=j.y_h,home=0.)
    sets['mt_gpt4_match']=j[keys].assign(y=j.y_g,home=0.)
    # Shared decisive-cell subset is a sensitivity analysis, not a different judge population.
    decisive=(j.y_h!=.5)&(j.y_g!=.5)
    sets['mt_human_decisive']=sets['mt_human_match'][decisive].copy()
    sets['mt_gpt4_decisive']=sets['mt_gpt4_match'][decisive].copy()
    for seed in [11,22,33]:
        # A single actual human label per shared response cell, avoids pseudo-independent GPT replication.
        one=h.sample(frac=1,random_state=seed).drop_duplicates(keys)
        one=one.merge(j[keys],on=keys,validate='one_to_one')
        sets[f'mt_human_single_{seed}']=one
    audit['mt']=dict(human_rows=len(h),gpt_rows=len(g),human_cells=len(hh),gpt_cells=len(gg),matched_cells=len(j),matched_questions=int(j.cluster.nunique()),decisive_cells=int(decisive.sum()),human_mean_raters=float(j.raters_h.mean()),human_min_raters=int(j.raters_h.min()),human_max_raters=int(j.raters_h.max()),human_tie_rate=float((h.y==.5).mean()),gpt_tie_rate=float((g.y==.5).mean()),human_judges=h.judge.value_counts().to_dict(),human_duplicate_rater_cells=int(h.duplicated(keys+['judge']).sum()),gpt_duplicate_cells=int(g.duplicated(keys).sum()),matching='question + unordered model pair + turn + SHA256 of both full released conversations',feedback_status='release has only winner, no original/revised vote field; independence before GPT feedback cannot be verified')
    j.to_csv(out/'matched_cells.csv',index=False)
    n=pd.read_csv(ROOT/'data'/'nba.csv')
    for yr in [2013,2014,2015]:
        nn=n[(n._iscopy==0)&(n.year_id==yr)&(n.is_playoffs==0)].copy()
        assert not nn.game_id.duplicated().any()
        assert ((nn.pts>nn.opp_pts)==(nn.game_result=='W')).all()
        sets[f'nba{yr}']=canonical(pd.DataFrame(dict(a=nn.team_id,b=nn.opp_id,y=(nn.game_result=='W').astype(float),cluster=nn.game_id,home=nn.game_location.map({'H':1.,'A':-1.,'N':0.}))))
    audit['nba']=dict(raw_rows=len(n),unique_games=int(n.game_id.nunique()),copy0_rows=int((n._iscopy==0).sum()),seasons={str(y):len(sets[f'nba{y}']) for y in [2013,2014,2015]},unused_columns='published Elo, forecast, points (except validation); no feature leakage')
    for name,df in sets.items():
        df=df.reset_index(drop=True);df['unit_id']=np.arange(len(df));df.to_csv(out/f'{name}.csv',index=False)
    (ROOT/'results'/'data_audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps({k:len(v) for k,v in sets.items()},indent=2))
    return sets
if __name__=='__main__':prepare()
