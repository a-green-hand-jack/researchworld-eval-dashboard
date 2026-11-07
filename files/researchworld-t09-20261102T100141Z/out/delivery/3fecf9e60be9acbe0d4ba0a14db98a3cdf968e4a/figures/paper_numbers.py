"""Print the paper's figure/table numbers against the file each one includes (checks the map in README.md after paper-repo renumbers).
Usage: python3 paper_numbers.py <paper-repo>/paper     (needs a built main.aux next to main.tex)"""
import re, sys, glob, os

root = sys.argv[1] if len(sys.argv) > 1 else "../../paper/paper"
aux = open(os.path.join(root, "main.aux")).read()
num = {m[0]: m[1] for m in re.findall(r"\\newlabel\{((?:fig|tab):[^}]*)\}\{\{([^}]*)\}", aux)}
rows = []
for f in sorted(glob.glob(os.path.join(root, "sections", "*.tex"))):
    t = open(f).read()
    for env in re.finditer(r"\\begin\{(figure\*?|table\*?)\}(.*?)\\end\{\1\}", t, re.S):
        body = env.group(2)
        labels = re.findall(r"\\label\{([^}]*)\}", body)
        files = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", body) + re.findall(r"\\input\{([^}]*)\}", body)
        w = re.findall(r"\\includegraphics\[width=([^\]]*)\]", body)
        for l in labels:
            if l in num:
                kind = "Fig." if l.startswith("fig") else "Table"
                rows.append((kind, num[l], l, ", ".join(os.path.basename(x) for x in files) or "(typeset in the paper)", ",".join(w)))
for r in sorted(set(rows), key=lambda r: (r[0] != "Fig.", int(re.sub(r"\D", "", r[1]) or 0))):
    print(f"{r[0]} {r[1]:>3}  {r[2]:<18} {r[3]:<42} {r[4]}")
