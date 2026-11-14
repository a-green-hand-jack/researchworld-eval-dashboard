"""Independently reconstruct stored edit witnesses and check result invariants."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,time
import numpy as np
import pandas as pd
from bt import BT
from data import load_panels,ROOT
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def main():
    start=time.time();paths=json.loads((ROOT/'results/paths.json').read_text())
    winner=json.loads((ROOT/'results/winner_paths.json').read_text())
    summary=pd.read_csv(ROOT/'results/summary.csv').set_index('panel')
    w=pd.read_csv(ROOT/'results/winner.csv').set_index('panel')
    checked=0;smallest_endpoint_gap=np.inf;diagnostics=[]
    for p in load_panels():
        graph=coo_matrix((np.ones(p.n),(p.a,p.b)),shape=(p.m,p.m))
        support=np.bincount(np.r_[p.a,p.b],minlength=p.m)
        diagnostics.append(dict(panel=p.name,
            comparison_components=int(connected_components(graph,directed=False,return_labels=False)),
            observed_pairs=len(p.X),min_item_support=int(support.min()),
            max_item_support=int(support.max()),unique_clusters=len(np.unique(p.cluster)),n=p.n,m=p.m))
        b=BT(p);t=b.fit();order=np.argsort(-t[:p.m]);c=b.contrast(*order[:2]);row=summary.loc[p.name]
        np.testing.assert_allclose(t,paths[p.name]['scores'],atol=1e-8)
        assert row.lower_k<=row.k
        assert row.safe_k<row.k
        assert bool(row.exact)==(row.lower_k==row.k)
        for mode,a in paths[p.name]['attacks'].items():
            ids=np.array(a['ids'],int);assert len(set(ids))==len(ids)
            assert a['k']==len(ids)
            count,wins=p.count.copy(),p.wins.copy()
            if mode=='delete':
                count-=np.bincount(p.group[ids],minlength=len(p.X))
                wins-=np.bincount(p.group[ids],weights=p.y[ids],minlength=len(p.X))
            else:
                assert np.all(p.y[ids]!=.5)
                wins+=np.bincount(p.group[ids],weights=1-2*p.y[ids],minlength=len(p.X))
            assert np.all(wins>=-1e-9) and np.all(wins<=count+1e-9)
            tt=b.fit(count,wins)
            target=2*row.bootstrap_sd if mode=='resolution' else 0.
            actual=float(c@tt)
            assert actual+target < -1e-8
            np.testing.assert_allclose(actual,a['gap'],atol=1e-7)
            if len(a['trace'])>1:assert a['trace'][-2]+target>=-1e-8
            smallest_endpoint_gap=min(smallest_endpoint_gap,abs(actual+target))
            checked+=1
        ids=np.array(winner[p.name]['ids'],int)
        wins=p.wins+np.bincount(p.group[ids],weights=1-2*p.y[ids],minlength=len(p.X))
        tt=b.fit(wins=wins)
        assert np.max(tt[:p.m])-tt[order[0]]>1e-8
        assert w.loc[p.name,'lower_k']<=len(ids)==w.loc[p.name,'upper_k']
        checked+=1
    adjacent=pd.read_csv(ROOT/'results/adjacent.csv')
    assert np.all(adjacent.lower_k<=adjacent.k)
    assert np.all(adjacent.safe_k<adjacent.k)
    random=pd.read_csv(ROOT/'results/random.csv')
    assert random.kendall.between(0,1).all()
    assert (random.pair_reversed<=random.leader_lost).all()
    result=dict(witnesses_checked=checked,all_passed=True,
        smallest_endpoint_margin=float(smallest_endpoint_gap),seconds=time.time()-start)
    (ROOT/'results/audit.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'results/data_diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
