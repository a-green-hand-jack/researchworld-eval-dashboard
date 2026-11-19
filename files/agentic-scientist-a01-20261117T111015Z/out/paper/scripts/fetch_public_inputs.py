import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    # @evidence[[source_evidence/data/manifest.json#sources]]
    sources = json.loads(Path("source_evidence/data/manifest.json").read_text())["sources"]
    for index, source in enumerate(sources):
        path = args.output / (str(index).zfill(3) + "_" + source["sha256"])
        if path.exists():
            encoded = path.read_bytes()
        else:
            with urlopen(source["source"], timeout=120) as response:
                encoded = response.read()
        actual = hashlib.sha256(encoded).hexdigest()
        if actual != source["sha256"]:
            raise RuntimeError("Source checksum mismatch: " + source["source"])
        if not path.exists():
            path.write_bytes(encoded)
        print(index, source["family"], actual)


if __name__ == "__main__":
    main()
