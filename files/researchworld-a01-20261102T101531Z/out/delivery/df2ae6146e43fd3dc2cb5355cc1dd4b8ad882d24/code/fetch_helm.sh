#!/bin/bash
# download HELM MMLU v1.13.0 release summary files listed in names.txt
while read n; do
  out="data/raw/helm/${n#mmlu/benchmark_output/releases/v1.13.0/}"
  mkdir -p "$(dirname "$out")"
  [ -s "$out" ] || curl -fsS --get -o "$out" "https://storage.googleapis.com/crfm-helm-public/$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$n")"
done < "$1"
