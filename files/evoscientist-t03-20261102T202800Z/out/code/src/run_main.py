"""Run experiments. Usage: python src/run_main.py E1|E2|E3|E4|E5 [n_jobs]
Raw attributions are stored as npz under results/<stage>/ ; analysis is in build_tables.py . analyze.py."""
import os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
os.environ["PYTHONPATH"] = here + os.pathsep + os.environ.get("PYTHONPATH", "")
import tasks
if __name__ == "__main__":
    tasks.main()
