"""Leaderboard units used in the study (one fit + claim set each)."""
from __future__ import annotations

import numpy as np

from . import data
from .analysis import Unit

ELIG_TOP = 20  # Arena / NBA-all: C2/C3/C4 are about the top-20 ranks of the base fit; C1/C3 challengers are all participants


def arena_unit(lam=1.0, top=ELIG_TOP, ds=None, drop_ties=False, name=None, by_count=False):
    """Primary claim set: top-`top` ranks of the fit, challengers = all participants (`top=None`: adjacent pairs of all ranks).
    `by_count=True`: secondary claim set of the `top` participants with the most comparisons (challengers only among them)."""
    ds = ds or data.load_arena55k()
    c = ds.counts(drop_ties=drop_ties)
    meta = dict(has_ties=not drop_ties)
    if by_count:
        elig = np.argsort(-c.participant_counts(), kind="stable")[:top]
        return Unit(name or "arena55k_top20count", "crowd", c, elig, lam=lam, meta=meta), ds
    return Unit(name or "arena55k", "crowd", c, None, lam=lam, meta=meta, window=top), ds


def mt_unit(kind="human", lam=1.0, ds=None, drop_ties=False, name=None):
    ds = ds or data.load_mt(kind)
    c = ds.counts(drop_ties=drop_ties)
    return Unit(name or f"mt_{kind}", "expert" if kind == "human" else "llm_judge", c, None, lam=lam,
                meta=dict(has_ties=not drop_ties)), ds


def nba_all_unit(lam=1.0, home=False, top=ELIG_TOP, nba=None, by_count=False):
    nba = nba or data.load_nba()
    c = nba.counts(home=home)
    sfx = "_home" if home else ""
    if by_count:
        elig = np.argsort(-c.participant_counts(), kind="stable")[:top]
        return Unit("nba_all_top20count" + sfx, "sports", c, elig, lam=lam, lam_h=1.0, meta=dict(has_ties=False)), nba
    return Unit("nba_all" + sfx, "sports", c, None, lam=lam, lam_h=1.0, meta=dict(has_ties=False), window=top), nba


def nba_season_unit(nba, year, lam=1.0, home=False):
    d = data.nba_season(nba, year)
    c = d.counts(home=home)
    return Unit(f"nba{year}" + ("_home" if home else ""), "sports", c, None, lam=lam, lam_h=1.0,
                meta=dict(has_ties=False, season=int(year))), d
