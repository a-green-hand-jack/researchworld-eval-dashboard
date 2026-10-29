# Review of paper-repo PR #14 (Version 1 -> release), head 774f3eb29837; re-checked at 0ab29827ae80 (only change: Table 2 title "per black hole" in report.md)

Inspected at that commit: report/report.md (all sections), all 7 figures (fig01-fig07 opened and checked: labelled axes, legends, readable, consistent with captions/text),
outputs/ (README, summary_leaver.json, summary.json, pex_vs_mu*.csv, rate_validation.csv, figure_manifest), code/sr.py, code/validate_rates.py. Delivery status `hutian/delivery`: success.

Independent checks
- Re-ran sr.excluded with the calibrated rate on the supplied data: P_ex(M33 X-7, 2e-12 eV)=1.0, P_ex(M33 X-7, 1e-11 eV)=0.331, P_ex(IRAS, 3.5e-19 eV)=0.683 (grid 0.688 at the nearest grid mu) - match outputs/pex_vs_mu_leaver.csv.
- Witek et al. Table II benchmark (alpha=0.42, a*=0.99: M*omega_I = 1.504e-7) is in paper_003; outputs/rate_validation.csv holds a computed value 1.5039e-7 (not a hard-coded number).
- Stott (2018) windows (7e-14-2e-11, 7e-20-1e-16 eV) match paper_001; the report's "inside Stott's windows" statement holds.
- Bosenova N_max = 16 pi alpha f_a^2 r_c^2 with r_c = l^2 r_g/alpha^2 matches paper_000 Sec. 3.2.1 and code.
- Data provenance (digitised M33 X-7 samples; IRAS mass from GRAVITY, spin from Walton) is stated and matches the file headers.

Against my commitment (#2): full-posterior framework, P_ex combination, windows at 50/68/95/99.7 %, bootstrap edge errors, (mu, f_a) limit with an honest reading (lower bound on f_a / upper bound on lambda for excluded bosons), point-vs-posterior comparison, sensitivity (age, levels, rate model, kappa), validation against literature - all present with traceable numbers. Limitations (upper edge from l=4,5 at alpha~0.9, assumed age, digitised samples, order-one bosenova coefficient, scalar only) are disclosed in abstract and Sec. 6.

Non-blocking remarks (for a later version)
- Fig. 6 / manifest label the benchmark "Witek+12", the report cites Witek et al. (2013).
- The headline upper edge 8.2e-12 eV rests on rates the report itself calls unreliable; the abstract already gives the conservative l<=1-2 edge, which is the appropriate framing.
- Age is a fixed assumption rather than a nuisance parameter (listed in Outlook).

Conclusion: version supported; approved.
