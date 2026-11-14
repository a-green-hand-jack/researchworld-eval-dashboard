"""Load the three public leaderboards as score matrices (score points, higher=better)."""
import json, os
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
P = os.path.join(ROOT, "data", "processed")
T6 = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


class Board:
    def __init__(self, name, S, models, tasks, noise_sd=None, meta=None):
        self.name, self.S, self.models, self.tasks = name, np.asarray(S, float), list(models), list(tasks)
        self.noise_sd = noise_sd          # (n,m) std-dev of evaluation noise, score points
        self.meta = meta
        self.n, self.m = self.S.shape

    def subset_tasks(self, idx):
        return Board(self.name, self.S[:, idx], self.models, [self.tasks[i] for i in idx],
                     None if self.noise_sd is None else self.noise_sd[:, idx], self.meta)


def _binom_sd(p01, n):
    p01 = np.clip(p01, 0.0, 1.0)
    return 100.0 * np.sqrt(p01 * (1 - p01) / n)


def load(name):
    if name == "helm57":
        df = pd.read_csv(os.path.join(P, "helm57.csv"), index_col=0)
        nev = json.load(open(os.path.join(P, "helm57_n.json")))
        S = df.values * 100.0
        n_vec = np.array([nev[c] for c in df.columns], float)
        return Board(name, S, df.index, df.columns, _binom_sd(df.values, n_vec[None, :]))
    if name in ("bbh24", "bbh24x"):
        df = pd.read_csv(os.path.join(P, "bbh24.csv"))
        df = df[~df["Flagged"].astype(bool)].reset_index(drop=True)
        if name == "bbh24x":   # sensitivity variant: drop the single extreme outlier at the top of the board
            df = df[df["fullname"] != OUTLIER].reset_index(drop=True)
        tasks = [c for c in df.columns if not c.endswith("_se") and c not in
                 ("fullname", "run_ts", "Type", "#Params (B)", "Flagged", "Merged", "Base Model", "Official Providers")]
        S = df[tasks].values * 100.0
        sd = df[[t + "_se" for t in tasks]].values * 100.0
        return Board(name, S, df["fullname"], tasks, sd, meta=df[["fullname", "Type", "#Params (B)", "Merged", "Base Model"]])
    if name == "oll6":
        df = pd.read_csv(os.path.join(P, "oll6.csv"))
        df = df[~df["Flagged"].astype(bool)].reset_index(drop=True)
        S = df[T6].values
        raw = df[[t + " Raw" for t in T6]].values
        nn = json.load(open(os.path.join(P, "oll6_n.json")))
        n_vec = np.array([nn[t] for t in T6], float)
        # normalised score = 100*(raw-chance)/(1-chance); sd scales with the same factor
        chance = np.where(raw.max(0) > 0, (raw - S / 100.0 * 1.0), 0)  # placeholder, replaced below
        scale = np.array([_scale(df, t) for t in T6])
        sd = _binom_sd(raw, n_vec[None, :]) * scale[None, :]
        return Board(name, S, df["fullname"], T6, sd, meta=df[["fullname", "Type", "#Params (B)", "Merged", "Base Model"]])
    raise ValueError(name)


def _scale(df, t):
    """slope d(normalised pts)/d(raw pts). Exactly affine (100, 133.3, 100, 111.1 per unit raw) for IFEval, GPQA, MATH, MMLU-Pro;
    approximate (least-squares slope) for BBH and MuSR whose normalisation is per-subtask."""
    raw = df[t + " Raw"].values; sc = df[t].values
    ok = sc > 0
    return float(np.polyfit(raw[ok], sc[ok], 1)[0]) * 0.01   # d(normalised pts)/d(raw pts)


OUTLIER = "qingy2024/Benchmaxx-Llama-3.2-1B-Instruct"
BOARDS = ["helm57", "bbh24", "bbh24x", "oll6"]
