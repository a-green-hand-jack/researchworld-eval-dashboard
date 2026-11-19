import sys, json, os
sys.path.insert(0,'/work/code')
d=sys.argv[1]
for fn in sorted(os.listdir(d)):
    if not fn.endswith('.json'): continue
    o=json.load(open(os.path.join(d,fn))); c=o['cfg']; s=o['summary']
    print(f"{c['arch']:3s} p{c['p']} f{c['frac']} w{c['width']:4d} L{c.get('layers','-')} lr{c['lr']} wd{c['wd']} s{c['seed']} P={o['n_params']:7d} fit={s['t_fit']} gen={s['t_gen']} vaFit={s['va_at_fit']} fin_tr={s['final_tr']:.2f} fin_va={s['final_va']:.2f} last={s['last_step']} wall={o['wall']:.0f}")
