"""Download raw public data (German credit from UCI, Pima / GMSC from OpenML, ACS PUMS via folktables)."""
import sys, os
root = sys.argv[1] if len(sys.argv) > 1 else "/work/data/raw"
import urllib.request, zipfile, io
# German credit (UCI id 144)
gdir = os.path.join(root, "german"); os.makedirs(gdir, exist_ok=True)
if not os.path.exists(os.path.join(gdir, "german.data")):
    b = urllib.request.urlopen("https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip").read()
    zipfile.ZipFile(io.BytesIO(b)).extractall(gdir)
# OpenML
import openml
openml.config.set_root_cache_directory(os.path.join(root, "openml"))
import pandas as pd
for name, did in [("pima", 37), ("gmsc", 46929)]:
    out = os.path.join(root, f"{name}.parquet")
    if os.path.exists(out): continue
    ds = openml.datasets.get_dataset(did, download_data=True, download_qualities=False, download_features_meta_data=False)
    X, y, cat, names = ds.get_data(target=ds.default_target_attribute)
    df = X.copy(); df["__target__"] = y
    df.to_parquet(out)
    print(name, did, ds.name, ds.version, ds.upload_date, df.shape, flush=True)
# ACS via folktables
from folktables import ACSDataSource
src = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir=os.path.join(root, "acs"))
df = src.get_data(states=["CA"], download=True)
print("ACS CA 2018", df.shape)
# Arrhythmia (UCI id 5), used only in the high-dimensional stress test
adir = os.path.join(root, "arrhythmia"); os.makedirs(adir, exist_ok=True)
if not os.path.exists(os.path.join(adir, "arrhythmia.data")):
    b = urllib.request.urlopen("https://archive.ics.uci.edu/static/public/5/arrhythmia.zip").read()
    zipfile.ZipFile(io.BytesIO(b)).extractall(adir)
