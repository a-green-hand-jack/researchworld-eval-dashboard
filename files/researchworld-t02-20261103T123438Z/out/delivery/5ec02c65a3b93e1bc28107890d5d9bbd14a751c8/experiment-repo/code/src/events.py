"""Event definitions and seed-level uncertainty; no imputation beyond horizon."""
import numpy as np


def sustained_event(rows, metric, threshold, sustain=3, horizon=None):
    """First start of `sustain` consecutive observed evaluations above threshold.

    The event is timestamped at the first evaluation in the sequence, after
    confirmation by later evaluations. Non-events are right-censored at the
    last evaluation. Bounds describe the sampled crossing, not unseen dynamics.
    """
    if not rows:
        raise ValueError('Empty curve')
    if sustain < 1:
        raise ValueError('Sustain must be positive')
    horizon = rows[-1]['step'] if horizon is None else horizon
    above = np.array([r[metric] >= threshold for r in rows])
    for i in range(len(rows)-sustain+1):
        if rows[i]['step']<=horizon and above[i:i+sustain].all():
            return dict(observed=True, step=rows[i]['step'],
                        sampled_lower_step=rows[i-1]['step'] if i else 0,
                        confirmed_step=rows[i+sustain-1]['step'],
                        censor_step=horizon,
                        terminal_above=bool(above[-sustain:].all()))
    return dict(observed=False, step=None,sampled_lower_step=None,confirmed_step=None,
                censor_step=horizon,terminal_above=bool(above[-sustain:].all()))


def summarize_curve(rows, train_threshold=.99, valid_threshold=.95, sustain=3, horizon=None):
    horizon = rows[-1]['step'] if horizon is None else horizon
    if rows[-1]['step']<horizon:
        raise ValueError('Incomplete curve cannot be treated as an administrative non-event')
    train = sustained_event(rows,'train_acc',train_threshold,sustain,horizon)
    valid = sustained_event(rows,'valid_acc',valid_threshold,sustain,horizon)
    t_train = train['step'] if train['observed'] else horizon
    t_valid = valid['step'] if valid['observed'] else horizon
    # Common-horizon restricted time, explicitly distinguish it from event time.
    waiting = max(0,t_valid-t_train)
    return dict(train_event=train,valid_event=valid,horizon=horizon,
                restricted_train_time=t_train,restricted_valid_time=t_valid,
                restricted_waiting_time=waiting,
                event_delay=valid['step']-train['step'] if train['observed'] and valid['observed'] else None,
                log2_event_time_ratio=float(np.log2(valid['step']/train['step']))
                    if train['observed'] and valid['observed'] and train['step']>0 and valid['step']>0 else None,
                zero_clock_boundary=bool((train['observed'] and train['step']==0) or (valid['observed'] and valid['step']==0)),
                delayed_event=bool(train['observed'] and valid['observed'] and train['step']>0
                    and valid['step']-train['step']>=1000 and valid['step']/train['step']>=10),
                censored_lag_lower_bound=max(0,horizon-train['step']) if train['observed'] and not valid['observed'] else None,
                censored_ratio_lower_bound=horizon/train['step'] if train['observed'] and train['step']>0 and not valid['observed'] else None)


def bootstrap_mean(values, seed=1701, repeats=10000):
    values = np.asarray(values,dtype=float)
    if len(values) == 0:
        raise ValueError('Empty bootstrap')
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite bootstrap input')
    if len(values) == 1:
        return dict(mean=float(values[0]),ci_low=None,ci_high=None,n=1,
                    bootstrap_seed=seed,bootstrap_repeats=0,uncertainty_estimable=False)
    draws = np.random.default_rng(seed).choice(values,size=(repeats,len(values)),replace=True).mean(1)
    return dict(mean=float(values.mean()),ci_low=float(np.quantile(draws,.025)),
                ci_high=float(np.quantile(draws,.975)),n=len(values),bootstrap_seed=seed,
                bootstrap_repeats=repeats)


def wilson_interval(successes, n):
    """95% score interval for an independent-seed binary event probability."""
    if not 0 <= successes <= n or n < 1:
        raise ValueError('Invalid event count')
    z = 1.959963984540054
    rate = successes/n
    denominator = 1+z*z/n
    center = (rate+z*z/(2*n))/denominator
    radius = z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/denominator
    return dict(rate=rate,ci_low=float(max(0,center-radius)),
                ci_high=float(min(1,center+radius)),successes=successes,n=n,method='Wilson 95%')


def paired_binary_interval(low, high, alpha=.05):
    """Conservative exact paired difference CI from discordant-count bounds.

    Each marginal discordance rate receives a two-sided (1-alpha/2)
    Clopper-Pearson interval. Bonferroni gives joint coverage >=1-alpha
    without assuming independence of the mutually exclusive discordances.
    Difference high-low is p_plus-p_minus; bounds propagate jointly.
    """
    from scipy.stats import beta
    low,high = np.asarray(low,dtype=int),np.asarray(high,dtype=int)
    if low.shape!=high.shape or len(low)==0 or not np.isin(low,[0,1]).all() or not np.isin(high,[0,1]).all():
        raise ValueError('Need equally sized nonempty paired binary observations')
    n = len(low)
    plus = int(((low==0)&(high==1)).sum())
    minus = int(((low==1)&(high==0)).sum())
    tail = alpha/4
    def cp(k):
        return (float(beta.ppf(tail,k,n-k+1)) if k else 0.,
                float(beta.ppf(1-tail,k+1,n-k)) if k<n else 1.)
    lp,up = cp(plus)
    lm,um = cp(minus)
    return dict(difference=(plus-minus)/n,ci_low=lp-um,ci_high=up-lm,n=n,
        table_low0_high0=int(((low==0)&(high==0)).sum()),table_low0_high1=plus,
        table_low1_high0=minus,table_low1_high1=int(((low==1)&(high==1)).sum()),
        method='Bonferroni Clopper-Pearson exact discordance bounds',confidence=1-alpha)
