# Reproduction
Env: `uv venv .venv && uv pip install numpy scipy scikit-learn matplotlib pandas gdown ppi-python==0.2.3` (see code/requirements.txt). Python 3.11.
Data: in /work/data run `python -c "from ppi_py.datasets import load_dataset; [load_dataset('./',n) for n in ['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare']]"` (Google Drive via gdown).
Run (cwd /work/code, OMP_NUM_THREADS=1, 36 procs): `python run.py 1000` (~25 min) -> results.json; `python analyze.py` -> paper/table.tex (Table 1); `python synth.py` -> synth.json, paper/synth.tex (Table 2, ~10 min; needs PYTHONPATH=/work/code).
Paper: cd paper; pdflatex main.tex (twice). NeurIPS 2026 template.
Off-limits content: none encountered.
