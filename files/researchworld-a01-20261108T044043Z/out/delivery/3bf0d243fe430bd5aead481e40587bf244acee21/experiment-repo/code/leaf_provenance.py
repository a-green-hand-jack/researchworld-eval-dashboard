"""Source provenance of the OLLB leaf-task retrieval (issue #9).
Usage: python3 code/leaf_provenance.py RAW_DIR   (RAW_DIR written by code/fetch_ollb_leaves.py)
Writes results/leaf/source_manifest.csv (every retrieved result file: path in the pinned `open-llm-leaderboard/results` commit, git object id from the
tree listing, SHA-256 of the downloaded bytes and of the reduced record), results/leaf/selected_files.csv (the file the file rule chose for each of the 500 models,
joined to the manifest; the one model without a validated file is listed with status no_matching_file) and results/leaf/source_digests.json
(SHA-256 of leaves.jsonl and files.csv, the pinned commit, counts). Gate and normalisation checks stay in results/ollb_leaves_gate.json."""
import sys, json, hashlib, pathlib
import pandas as pd
raw = pathlib.Path(sys.argv[1]); root = pathlib.Path(__file__).resolve().parents[1]; out = root / "results" / "leaf"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man = pd.read_csv(raw / "source_manifest.csv"); files = pd.read_csv(raw / "files.csv")
lv = pd.read_csv(root / "data" / "processed" / "ollb_leaves.csv", usecols=["model", "rank_mean6", "file", "n_files"])
man.to_csv(out / "source_manifest.csv", index=False)
sel = files[["model", "n_files"]].merge(lv[["model", "rank_mean6", "file"]], on="model", how="left").rename(columns={"file": "selected_file"})
sel["status"] = sel.selected_file.notna().map({True: "ok", False: "no_matching_file"})
sel = sel.merge(man[["model", "file", "path", "git_oid", "sha256_raw_file", "sha256_reduced_record"]].rename(columns={"file": "selected_file"}), on=["model", "selected_file"], how="left")
assert (sel.status == "ok").sum() == len(lv) and sel[sel.status == "ok"].sha256_raw_file.notna().all()
sel.to_csv(out / "selected_files.csv", index=False)
g = json.load(open(root / "results" / "ollb_leaves_gate.json"))
dig = dict(source="https://huggingface.co/datasets/open-llm-leaderboard/results", commit="aa81ecc38fdc5708254b833923368970efdf5ef5",
           leaves_jsonl_sha256=sha(raw / "leaves.jsonl"), files_csv_sha256=sha(raw / "files.csv"), n_files_retrieved=len(man), n_models=len(files),
           n_models_selected=int((sel.status == "ok").sum()), source_manifest_sha256=sha(out / "source_manifest.csv"),
           processed_leaves_csv_sha256=sha(root / "data" / "processed" / "ollb_leaves.csv"), gate_status_counts=g["status_counts"],
           note="leaves.jsonl is the reduced retrieval (stderr and alias fields dropped); it is not delivered, the manifest identifies every source file and "
                "code/fetch_ollb_leaves.py regenerates it (network).")
json.dump(dig, open(out / "source_digests.json", "w"), indent=1)
g["source"] = {k: dig[k] for k in ("source", "commit", "leaves_jsonl_sha256", "files_csv_sha256", "n_files_retrieved", "source_manifest_sha256")}
g["source"]["details"] = "results/leaf/source_digests.json, results/leaf/source_manifest.csv, results/leaf/selected_files.csv"
json.dump(g, open(root / "results" / "ollb_leaves_gate.json", "w"), indent=1)
print(json.dumps(dig, indent=1))
