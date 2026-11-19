import numpy as np, glob, os
for f in sorted(glob.glob("data/*.npz")):
    d = np.load(f); n = os.path.basename(f)[:-4]; print("==", n)
    for k in d.files:
        a = d[k]
        if a.ndim==1:
            u = np.unique(a)
            print(f"  {k}: shape={a.shape} mean={a.mean():.4f} sd={a.std():.4f} min={a.min():.3f} max={a.max():.3f} nunique={len(u)}")
        else: print(f"  {k}: shape={a.shape} nunique/col={[len(np.unique(a[:,j])) for j in range(a.shape[1])]}")
    if "Y" in d.files and "Yhat" in d.files:
        y, yh = d["Y"], d["Yhat"]
        print(f"  corr(Y,Yhat)={np.corrcoef(y,yh)[0,1]:.3f}  mean(Y)-mean(Yhat)={y.mean()-yh.mean():.4f}")
