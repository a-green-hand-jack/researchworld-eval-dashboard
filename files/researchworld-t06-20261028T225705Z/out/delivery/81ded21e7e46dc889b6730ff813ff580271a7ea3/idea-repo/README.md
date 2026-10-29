# idea-repo

ResearchWorld role: idea-repo

## notes/
Working material of the context position (not a delivery): `bt_checks.py` (tie rules, BT existence/connectivity per dataset) and `amip_check.py` (first-order influence formula vs exact refit on Arena 55k), with their logs. Raw data is read from a directory outside the repository (`/hutian/data`, see wiki `Data-notes` for sources and checksums). Run: `python3 -I notes/bt_checks.py <datadir>` (~40 s), `python3 -I notes/amip_check.py <datadir>` (~40-100 s). Python 3 with numpy, scipy, pandas.
