"""Export the final 2000-2023 calendar-year regional and global series as one tidy table."""
import sys; sys.path.insert(0, '/work/code')
import pandas as pd
from glambie_lib import REGIONS, SHORT
rows = []
for r in REGIONS:
    c = pd.read_csv(f'/work/outputs/main/calendar_{r}.csv', index_col=0).loc[2000:2023]
    for y, x in c.iterrows():
        rows.append(dict(region=r, code=SHORT[r], year=y, glacier_area_km2=x.area, mass_change_gt=x['gt'], sigma_gt=x.sig_gt,
                         sigma_random_gt=x.sig_rand_gt, sigma_systematic_gt=x.sig_sys_gt, specific_mass_change_mwe=x.mwe, sigma_mwe=x.sig))
g = pd.read_csv('/work/outputs/global_annual.csv', index_col=0)
for y, x in g.iterrows():
    rows.append(dict(region='0_global', code='GLOBAL', year=y, glacier_area_km2=x.area, mass_change_gt=x['gt'], sigma_gt=x.sig_gt,
                     sigma_random_gt=x.sig_rand_gt, sigma_systematic_gt=x.sig_sys_gt, specific_mass_change_mwe=x.mwe, sigma_mwe=x.sig))
pd.DataFrame(rows).to_csv('/work/outputs/final_calendar_year_series_2000_2023.csv', index=False)
print(len(rows))
