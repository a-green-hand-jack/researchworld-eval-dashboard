"""Download raw data (UCI German Credit, OpenML 37 / 46929, ACS PUMS CA 2018 via folktables) into data/."""
import os, urllib.request, zipfile, io, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
raw = os.path.join(common.DATA, "raw"); os.makedirs(raw, exist_ok=True)
if not os.path.exists(os.path.join(raw, "german.data")):
    b = urllib.request.urlopen("https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip").read()
    zipfile.ZipFile(io.BytesIO(b)).extract("german.data", raw)
for ds in ["german", "pima", "gmsc", "acs_income", "acs_coverage"]:
    X, y, cat = common.load_dataset(ds)
    print(ds, X.shape, "pos rate %.3f" % y.mean(), "cat:", cat)
