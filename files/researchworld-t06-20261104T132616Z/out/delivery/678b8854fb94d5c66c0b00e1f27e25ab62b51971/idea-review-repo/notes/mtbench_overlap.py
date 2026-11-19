# Working check (not a delivery): MT-Bench human vs GPT-4 pair judgments, pinned files, columns only.
# usage: python3 -I mtbench_overlap.py <human.parquet> <gpt4_pair.parquet>
import sys, pandas as pd
c = ['question_id', 'model_a', 'model_b', 'winner', 'judge', 'turn']
h = pd.read_parquet(sys.argv[1], columns=c); g = pd.read_parquet(sys.argv[2], columns=c)
k = ['question_id', 'model_a', 'model_b', 'turn']
print(len(h), len(g), h.winner.value_counts().to_dict(), g.winner.value_counts().to_dict())
print('unique keys human/gpt4', len(h.drop_duplicates(k)), len(g.drop_duplicates(k)),
      'overlap', len(h.drop_duplicates(k).merge(g.drop_duplicates(k), on=k)))
