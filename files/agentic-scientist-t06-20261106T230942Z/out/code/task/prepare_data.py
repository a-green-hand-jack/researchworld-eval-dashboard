"""Pinned, offline-capable preparation: python prepare_data.py --arena data/train.csv --nba data/nbaallelo.csv.
Raw downloads stay outside the submission; this deterministic script records all derived provenance.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import unicodedata
from collections import defaultdict

SOURCES = {
    "arena": ("18c298340948c0e7f7727399fd459cca6ce0ca6f", "0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2"),
    "nba": ("4c1ff5e3aef1816ae04af63218015066e186c147", "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc"),
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def normalize(value, strict=False):
    if isinstance(value, str):
        value = unicodedata.normalize("NFKC" if strict else "NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
        return " ".join(value.split()) if strict else value
    if isinstance(value, list):
        return [normalize(item, strict) for item in value]
    return value


def prepare(arena_path, nba_path, root):
    for name, path in (("arena", arena_path), ("nba", nba_path)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCES[name][1]:
            raise ValueError("source checksum mismatch: " + name)
    csv.field_size_limit(16 * 1024 * 1024)
    arena, parent, owners = [], [], {}

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    with arena_path.open(newline="", encoding="utf-8") as stream:
        for source_row, row in enumerate(csv.DictReader(stream), 2):
            model_a, model_b = row["model_a"], row["model_b"]
            flags = [int(row[key]) for key in ("winner_model_a", "winner_model_b", "winner_tie")]
            if sum(flags) != 1 or model_a == model_b:
                continue
            outcome = 1.0 if flags[0] else 0.0 if flags[1] else 0.5
            prompt, answer_a, answer_b = [json.loads(row[key]) for key in ("prompt", "response_a", "response_b")]
            hashes = set()
            for strict in (False, True):
                documents = [normalize(doc, strict) for doc in (prompt, answer_a, answer_b)]
                hashes.update(digest(doc) for doc in documents if any(str(item).strip() for item in doc))
                left = [model_a, documents[1]]
                right = [model_b, documents[2]]
                if canonical(left) > canonical(right):
                    left, right, mapped = right, left, 1 - outcome
                else:
                    mapped = outcome
                hashes.add(digest([documents[0], left, right, mapped]))
            index = len(arena)
            parent.append(index)
            for content_hash in sorted(hashes):
                if content_hash in owners:
                    parent[find(index)] = find(owners[content_hash])
                else:
                    owners[content_hash] = index
            arena.append({"source_id": row["id"], "source_row": source_row, "a": model_a, "b": model_b,
                          "y": outcome, "z": 0.0, "hashes": sorted(hashes)})
    members = defaultdict(list)
    for index in range(len(arena)):
        members[find(index)].append(index)
    panels = {"search": {"arena": []}, "final": {"arena": []}}
    for indices in members.values():
        group = min(content_hash for index in indices for content_hash in arena[index]["hashes"])
        plane = "search" if int(hashlib.sha256(("split-v1:" + group).encode()).hexdigest(), 16) % 4 == 0 else "final"
        for index in indices:
            arena[index]["group"] = group
            panels[plane]["arena"].append(arena[index])
    games = defaultdict(list)
    with nba_path.open(newline="", encoding="utf-8") as stream:
        for source_row, row in enumerate(csv.DictReader(stream), 2):
            if int(row["year_id"]) in (2006, 2007, 2008, 2011, 2012, 2013, 2014, 2015):
                games[row["game_id"]].append((source_row, row))
    exclusions = []
    for identity, rows in sorted(games.items()):
        primary = [item for item in rows if item[1]["_iscopy"] == "0"]
        if len(primary) != 1 or len(rows) != 2:
            exclusions.append([identity, "incomplete_reciprocal", int(rows[0][1]["year_id"])])
            continue
        source_row, row = primary[0]
        other = next(item[1] for item in rows if item[1]["_iscopy"] == "1")
        if not (row["team_id"] == other["opp_id"] and row["opp_id"] == other["team_id"]
                and row["pts"] == other["opp_pts"] and row["opp_pts"] == other["pts"]):
            raise ValueError("inconsistent reciprocal game")
        year = int(row["year_id"])
        plane = "search" if year < 2010 else "final"
        teams = sorted([row["team_id"], row["opp_id"]])
        scores = {row["team_id"]: int(row["pts"]), row["opp_id"]: int(row["opp_pts"])}
        location = {"H": 1.0, "A": -1.0, "N": 0.0}[row["game_location"]]
        home = row["team_id"] if location == 1 else row["opp_id"] if location == -1 else None
        raw = [row["date_game"], year, teams, [scores[team] for team in teams], home, row["is_playoffs"]]
        content_hash = digest(raw)
        example_hash = digest([teams, [scores[team] for team in teams], row["date_game"], home])
        record = {"source_id": identity, "source_row": source_row, "reciprocal_rows": [item[0] for item in rows],
                  "a": row["team_id"], "b": row["opp_id"], "y": float(int(row["pts"]) > int(row["opp_pts"])),
                  "z": location, "hashes": [content_hash, example_hash], "group": content_hash}
        panels[plane].setdefault("nba-" + str(year), []).append(record)
    sets = {plane: {content_hash for records in cases.values() for row in records for content_hash in row["hashes"]}
            for plane, cases in panels.items()}
    if sets["search"] & sets["final"]:
        raise ValueError("normalized raw document/example overlap")
    ids = {plane: {row["source_id"] for cases in panels[plane].values() for row in cases} for plane in panels}
    if ids["search"] & ids["final"]:
        raise ValueError("source ID overlap")
    for plane, cases in panels.items():
        destination = root / "resources" / plane
        destination.mkdir(parents=True, exist_ok=True)
        manifest = {"normalization": "v1 NFC line endings preserve case/whitespace; additional NFKC whitespace-collapsed audit; JSON parsed before hashing; swapped example canonicalization; transitive document groups",
                    "sources": SOURCES, "content_disjoint": True, "source_disjoint": True,
                    "hash_count": len(sets[plane]), "group_rule": "sha256(split-v1:minimum-content-hash) modulo 4 equals 0 for search",
                    "nba_exclusions": [item for item in exclusions if (item[2] < 2010) == (plane == "search")], "cases": {}}
        for case, records in cases.items():
            records.sort(key=lambda row: row["source_row"])
            if len(records) < 1000:
                raise ValueError("insufficient panel: " + case)
            names = sorted({row[side] for row in records for side in ("a", "b")})
            index = {name: ordinal for ordinal, name in enumerate(names)}
            data = {"case": case, "participants": names, "rows": [[index[row["a"]], index[row["b"]], row["y"], row["z"]] for row in records],
                    "provenance": [{key: value for key, value in row.items() if key not in ("a", "b", "y", "z")} for row in records]}
            (destination / (case + ".json")).write_text(canonical(data) + "\n")
            manifest["cases"][case] = {"rows": len(records), "participants": len(names), "groups": len({row["group"] for row in records})}
        (destination / "manifest.json").write_text(canonical(manifest) + "\n")
    print(canonical({plane: {case: len(rows) for case, rows in cases.items()} for plane, cases in panels.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arena", type=pathlib.Path, required=True)
    parser.add_argument("--nba", type=pathlib.Path, required=True)
    options = parser.parse_args()
    prepare(options.arena, options.nba, pathlib.Path(__file__).resolve().parent)
