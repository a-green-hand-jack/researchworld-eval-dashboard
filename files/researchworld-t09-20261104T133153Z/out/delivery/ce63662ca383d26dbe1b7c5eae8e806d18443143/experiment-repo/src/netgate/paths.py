"""Location of the results/ directory: NETGATE_RESULTS, else the nearest ancestor of this file that holds a results/ directory
(the repository root, also when the code is delivered under code/), else ./results."""
import os


def results_dir():
    if os.environ.get("NETGATE_RESULTS"):
        return os.environ["NETGATE_RESULTS"]
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "results")):
            return os.path.join(d, "results")
        d = os.path.dirname(d)
    return os.path.join(os.getcwd(), "results")
