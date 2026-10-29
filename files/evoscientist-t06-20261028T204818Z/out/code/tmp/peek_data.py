import pandas as pd, pyarrow.parquet as pq, json
for f in ["data/mtbench/human.parquet","data/mtbench/gpt4_pair.parquet"]:
    d=pd.read_parquet(f, columns=["question_id","model_a","model_b","winner","judge","turn"])
    print(f, d.shape); print(d.head(3)); print(d.winner.value_counts()); print(d.judge.nunique(), d.judge.value_counts().head(5)); print(sorted(set(d.model_a)|set(d.model_b)))
s=pq.read_schema("data/arena140k/train-00000-of-00007.parquet"); print(s.names)
d=pd.read_csv("data/arena55k/train.csv", usecols=["id","model_a","model_b","winner_model_a","winner_model_b","winner_tie"])
print(d.shape, d[["winner_model_a","winner_model_b","winner_tie"]].sum().to_dict(), d.model_a.nunique())
n=pd.read_csv("data/nba/nbaallelo.csv"); print(n.columns.tolist()); print(n.head(2).T)
with open("data/arena_judges/llm-judges-prob-avg/Qwen2-72B-Instruct.jsonl") as f:
    print(f.readline()[:500])
