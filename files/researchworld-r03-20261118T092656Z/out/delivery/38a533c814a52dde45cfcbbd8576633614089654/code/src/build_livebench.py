"""LiveBench model_judgment (commit 9704e5d) -> model x task / model x category matrices.
usage: python3 -I build_livebench.py IN.parquet OUT_TASK.parquet OUT_CAT.parquet"""
import sys
import pandas as pd
src, out_t, out_c = sys.argv[1:4]
l = pd.read_parquet(src)
print("raw rows", len(l), "dup (question,model) rows", l.duplicated(["question_id", "model"]).sum())
# re-judgements of same (question, model): average first, so each question counts once
q = l.groupby(["model", "category", "task", "question_id"], as_index=False).agg(score=("score", "mean"), n_judgments=("score", "size"))
t = q.groupby(["model", "category", "task"]).agg(score=("score", "mean"), n_q=("score", "size")).reset_index()
wide_s = t.pivot(index="model", columns="task", values="score")
wide_n = t.pivot(index="model", columns="task", values="n_q").add_prefix("nq_")
df_t = wide_s.join(wide_n)
df_t["n_tasks"] = wide_s.notna().sum(axis=1)
df_t["n_questions_total"] = wide_n.sum(axis=1).astype(int)
df_t["first_tstamp"] = pd.to_datetime(l.groupby("model").tstamp.min(), unit="s")
df_t["last_tstamp"] = pd.to_datetime(l.groupby("model").tstamp.max(), unit="s")
df_t.reset_index().to_parquet(out_t, index=False)
# category: mean over questions in category (question-weighted) and mean of task means (macro)
c = q.groupby(["model", "category"]).agg(score=("score", "mean"), n_q=("score", "size")).reset_index()
m = t.groupby(["model", "category"]).score.mean().rename("macro").reset_index()
c = c.merge(m, on=["model", "category"])
cw = c.pivot(index="model", columns="category", values="score").add_suffix("_qmean")
cm = c.pivot(index="model", columns="category", values="macro").add_suffix("_taskmacro")
cn = c.pivot(index="model", columns="category", values="n_q").add_prefix("nq_")
df_c = cw.join(cm).join(cn).reset_index()
df_c.to_parquet(out_c, index=False)
print("task matrix", df_t.shape, "models", len(df_t), "tasks", wide_s.shape[1], "missing frac (scores)", wide_s.isna().mean().mean())
print("full 7 tasks:", (df_t.n_tasks == 7).sum(), " >=6:", (df_t.n_tasks >= 6).sum())
print("cat matrix", df_c.shape, "missing", df_c.filter(like="_qmean").isna().mean().mean())
print(wide_s.notna().sum())
