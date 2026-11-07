"""Cell lists (population, n, N, R, flags) for each study.  R defaults follow PLAN.md (primary >= 2000)."""
PRIMARY = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "ballots"]
POOL = {"galaxies": 16743, "forest": 1596, "alphafold": 10802, "gene_expression": 61150, "census_income": 380091,
        "census_healthcare": 318215, "census_education": 318215, "ballots": 1027, "plankton": 421238}
NS = [50, 100, 200, 400, 1000]


def ns_for(d):
    return [n for n in NS if n <= POOL[d] / 5]


def pilot(R):          # galaxies + forest, n in {50, 200}
    R = R or 2000
    return [(d, n, 20 * n, R, {"tag": "pilot"}) for d in ["galaxies", "forest"] for n in [50, 200]]


def real_primary(R):
    R = R or 2000
    return [(d, n, 20 * n, R, {"tag": "primary"}) for d in PRIMARY for n in ns_for(d)]


def real_appendix(R):  # census_healthcare / census_education
    R = R or 2000
    return [(d, n, 20 * n, R, {"tag": "appendix"}) for d in ["census_healthcare", "census_education"] for n in ns_for(d)]


def real_nsweep(R):    # n/N sweep: N in {n, 5n, 20n, large}
    R = R or 2000
    return [(d, n, N, R, {"tag": "nsweep"}) for d in ["galaxies", "forest", "gene_expression", "census_income"]
            for n in [100, 400] for N in [n, 5 * n, 20 * n, 20000]]


def shift(R):          # plankton: real shift vs within-2013 control
    R = R or 2000
    cells = [("plankton", n, 20 * n, R, {"tag": "shift", "shift": True}) for n in NS]
    cells += [("plankton", n, 20 * n, R, {"tag": "control"}) for n in NS]
    return cells


def forest_wor(R):     # duplicates sensitivity: labeled draws without replacement
    R = R or 2000
    return [("forest", n, 20 * n, R, {"tag": "wor", "wor": True}) for n in ns_for("forest")]


def synth(R):          # one-factor-at-a-time around base: tanh, kappa=.5, snr=1, n=100, N=20n
    R = R or 2000
    base = dict(kind="tanh", kappa=0.5, snr=1.0, tail=0, n=100, Nm=20)
    cells, seen = [], set()

    def add(tag, **kw):
        b = {**base, **kw}
        N = 20000 if b["Nm"] == 0 else b["Nm"] * b["n"]
        key = (b["kind"], b["kappa"], b["snr"], b["tail"], b["n"], N)
        if key in seen:
            return
        seen.add(key)
        cells.append((f"syn:{b['kind']}:{b['kappa']}:{b['snr']}:{b['tail']}", b["n"], N, R, {"tag": tag}))
    for kind in ["tanh", "quad", "bin"]:
        for kappa in [0.0, 0.25, 0.5, 0.75, 1.0]:
            add("kappa", kind=kind, kappa=kappa)
    for kind in ["tanh", "quad"]:
        for n in [50, 100, 200, 400, 1000]:
            add("n", kind=kind, n=n)
        for Nm in [1, 5, 20, 0]:
            add("Nratio", kind=kind, Nm=Nm)
        for snr in [0.25, 0.5, 1.0, 2.0, 4.0]:
            add("snr", kind=kind, snr=snr)
        for tail in [0, 1]:
            for kappa in [0.0, 0.5]:
                add("tail", kind=kind, tail=tail, kappa=kappa)
    for n in [50, 100, 400]:
        for kappa in [0.0, 1.0]:
            add("bin_n", kind="bin", kappa=kappa, n=n)
    return cells


GRIDS = dict(pilot=pilot, real_primary=real_primary, real_appendix=real_appendix, real_nsweep=real_nsweep,
             shift=shift, forest_wor=forest_wor, synth=synth)
