import importlib.metadata
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ["numpy", "scipy", "matplotlib", "pypdf", "pymupdf", "jsonschema", "requests"]


def main():
    path = ROOT / "reproduction_environment.json"
    path.write_text(json.dumps({"python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in MODULES},
        "scope": "Paper extraction environment only; sealed evaluation environment not recoverable."}, indent=2) + "\n")
    path.with_suffix(".json.prov.json").write_text(json.dumps({
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": path.name, "kind": "log"},
        "derived_from": ["@evidence[[scripts/capture_environment.py]]"],
        "generated_by": {"script_path": "scripts/capture_environment.py"},
        "notes": "Actual importlib.metadata and platform outputs from the manuscript extraction interpreter; not experimental performance."}, indent=2) + "\n")


if __name__ == "__main__":
    main()
