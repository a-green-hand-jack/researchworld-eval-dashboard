import glob, pickle, pandas as pd
def load_all(tag, root="/work/results/raw"):
    rows = []
    for f in glob.glob(f"{root}/{tag}/*.pkl"):
        rows += pickle.load(open(f, "rb"))
    df = pd.DataFrame(rows)
    df["method"] = df["design"] + "/" + df["est"]
    return df
