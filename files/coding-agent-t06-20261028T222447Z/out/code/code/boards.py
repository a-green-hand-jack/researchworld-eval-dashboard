"""Registry of all leaderboards used in the paper: name -> (design, loader)."""
import numpy as np
import loaders as D

JUDGES = ["Meta-Llama-3-70B-Instruct", "Qwen2-72B-Instruct", "Mistral-7B-Instruct-v0.2"]
MT_SHARED = {"gpt-4": ["gpt-4-0314", "gpt-4-0613"], "gpt-3.5-turbo": ["gpt-3.5-turbo-0613", "gpt-3.5-turbo-0314"],
             "claude-v1": ["claude-1"], "alpaca-13b": ["alpaca-13b"], "vicuna-13b-v1.2": ["vicuna-13b"], "llama-13b": ["llama-13b"]}


def _sub(d, keep_items, rename=None):
    """restrict a comparison table to a set of items (names)"""
    items = d["items"]
    keep = [k for k, n in enumerate(items) if n in keep_items]
    m = np.isin(d["a"], keep) & np.isin(d["b"], keep)
    newidx = {k: t for t, k in enumerate(keep)}
    a = np.array([newidx[x] for x in d["a"][m]]); b = np.array([newidx[x] for x in d["b"][m]])
    y = d["y"][m].copy()
    sw = a > b
    a2 = np.where(sw, b, a); b2 = np.where(sw, a, b); y2 = np.where(sw, 1 - y, y)
    return dict(items=[items[k] for k in keep], a=a2, b=b2, h=d["h"][m], y=y2)


def arena_matched6():
    d = D.arena55k()
    # one Arena checkpoint per MT-Bench model (the one with most comparisons) so that the six-item
    # leaderboard is comparable with MT-Bench
    from collections import Counter
    cnt = Counter(list(d["a"]) + list(d["b"]))
    pick = []
    for mt, cands in MT_SHARED.items():
        c = [x for x in cands if x in d["items"]]
        pick.append(max(c, key=lambda n: cnt[d["items"].index(n)]))
    return _sub(d, set(pick))


def _drop_ties(d):
    m = d["y"] != 0.5
    return dict(items=d["items"], a=d["a"][m], b=d["b"][m], h=d["h"][m], y=d["y"][m])


def get_all(include_nba=True):
    """returns dict name -> dict(design=..., load=callable)"""
    B = {}
    B["arena55k"] = dict(design="crowd", load=D.arena55k)
    B["arena140k"] = dict(design="crowd", load=D.arena140k)
    B["arena6"] = dict(design="crowd", load=arena_matched6)
    B["mt_human"] = dict(design="expert", load=lambda: D.mtbench("human"))
    B["mt_gpt4"] = dict(design="judge", load=lambda: D.mtbench("gpt4"))
    if include_nba:
        # lazy: load once
        for yr in range(1947, 2016):
            B[f"nba{yr}"] = dict(design="sport", load=(lambda yr=yr: D.nba_seasons()[yr]))
    for nm in ("arena55k", "mt_human", "mt_gpt4"):
        B[nm + "_noties"] = dict(design=B[nm]["design"], load=(lambda nm=nm: _drop_ties(B[nm]["load"]())))
    B["arenaST_human"] = dict(design="crowd", load=lambda: _judge_board(None))
    for j in JUDGES:
        B[f"arenaST_{j}"] = dict(design="judge", load=lambda j=j: _judge_board(j))
    return B


def _judge_board(judge):
    ma, mb, yh, yj = D.arena_judge(JUDGES[0])
    from loaders import _encode
    if judge is None:
        return _encode(ma, mb, yh)
    if judge != JUDGES[0]:
        _, _, _, yj = D.arena_judge(judge)  # same battle order in every judge file (checked in tests.py)
    return _encode(ma, mb, yj)
