"""Safely convert the .jbl pickles to .npz (restricted unpickler: numpy/builtins only). Usage: python -I prep_data.py RAW OUT"""
import sys, pickle, glob, os, numpy as np, joblib
import joblib.numpy_pickle as npk
orig = npk.NumpyUnpickler.find_class
def fc(self, mod, name):
    if not (mod.startswith('numpy') or mod in ('builtins','collections','joblib.numpy_pickle','_codecs')):
        raise pickle.UnpicklingError(f'blocked {mod}.{name}')
    return orig(self, mod, name)
npk.NumpyUnpickler.find_class = fc
raw, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
helm = [l.strip() for l in open(f'{raw}/helm_model_list.txt') if l.strip()]
for f in sorted(glob.glob(f'{raw}/*.jbl')):
    n = os.path.basename(f)[:-4]
    if n.endswith('_models'): continue
    X = joblib.load(f)
    mp = f'{raw}/{n}_models.jbl'
    models = joblib.load(mp) if os.path.exists(mp) else None
    nan = int(np.isnan(X.astype(float)).sum())
    vals = np.unique(X[~np.isnan(X.astype(float))])
    print(n, X.shape, 'nan', nan, 'values', vals[:6], 'mean', np.nanmean(X.astype(float)).round(3),
          'nmodels', None if models is None else (len(models), len(set(models))))
    np.savez_compressed(f'{out}/{n}.npz', X=X.astype(float), models=np.array(models if models is not None else []))
