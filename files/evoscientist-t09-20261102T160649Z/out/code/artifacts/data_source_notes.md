# Dataset-provenance source notes

Date: 2026-11-02 (UTC). Scope: dataset attribution and topology/extraction provenance only. No topic research, search engines, abstract pages, recommendations, citation-chain traversal, or regression/GATE papers were accessed. No code, manuscript, existing data, or existing source files were changed. Newly saved source responses, extraction products, and audit logs are under `/work/artifacts/sources/`.

## 1. Read-source references (eligible under the only-cite-read rule)

[1] Amanda L. Traud, Peter J. Mucha, and Mason A. Porter. **Social Structure of Facebook Networks.** arXiv:1102.2166v1 [cs.SI], 10 February 2011. https://arxiv.org/pdf/1102.2166

- Downloaded and extracted using installed **pypdf 5.9.0**; 82 PDF pages.
- Read title/version metadata (PDF p. 1), snapshot context (p. 4), Section 2, “Data” (pp. 5–7), and the Stanford row in Table A.1 (p. 39). This is a provenance-section reading, not a claim to have read the whole paper.
- Exact original read: the PDF itself labels the version `arXiv:1102.2166v1 ... 10 Feb 2011`. Its title-page footer also says `Preprint submitted to Social Networks October 22, 2018`; that footer is reported as an internal discrepancy, not used to infer a different publication year.
- The read NetworkRepository dataset page separately supplies a 2012 *Phys. A* citation, volume 391(16), pp. 4165–4180. Those are page-reported published-version metadata, not verification that the journal version was read. The reference above deliberately identifies the actual preprint read.

[2] SNAP. **Social circles: Facebook.** https://snap.stanford.edu/data/ego-Facebook.html

- Read existing local snapshot `/work/data/snap_page.html`, including dataset information, anonymization, statistics, combined-network construction note, source citation, and files table.
- Snapshot URL is established by `/work/data/manifest.json`; no new network access to the page was made in this task. Snapshot hash matches that manifest. Original snapshot download time is not supplied there.

[3] Network Repository. **Stanford3 (Facebook Networks).** https://networkrepository.com/socfb-Stanford3.php

- Read existing `/work/data/stanford_page.html` through locally extracted text, including metadata, acknowledgements/citation policy, and network statistics.
- Snapshot URL and matching hash verified against the existing manifest; no new network access to this page. Original download time is not supplied in the manifest.

[4] Network Repository. **Policy / Data Policy and License.** https://networkrepository.com/policy.php

- Read existing `/work/data/nr_policy.html` through locally extracted text, including attribution, ShareAlike, additional dataset citation requests, notices, and repository acknowledgement instructions.
- Snapshot URL and matching hash verified against the existing manifest; no new network access to this page. Original download time is not supplied in the manifest.

## 2. Verified dataset provenance and topology

### Facebook100 / Stanford3

- Section 2 of [1] says Adam D’Angelo of Facebook supplied the data directly in anonymized form: complete users and within-institution friendship links for 100 American institutions in September 2005. The preceding context specifies a single-day snapshot. The authors ignore cross-institution links and analyze institutions as separate networks [1, PDF pp. 4–6].
- The paper describes a single unweighted, undirected edge type and symmetric binary adjacency. Optional user attributes include gender, class year, high school, major, and residence; some are missing [1, pp. 6–7]. This does not establish that those attributes are present in the repository's topology-only `.mtx` download.
- The paper's **“Full” network is the largest connected component**, not necessarily every record in the institution's initial raw data. Student, Female, and Male variants are also largest-component constructions; the gender-specific networks are subsets of Full, not Student [1, p. 6].
- Table A.1 identifies **Stanford, institution number 3**. Its Full graph has **11,586 nodes and 568,309 edges**. The Student, Female, and Male node counts are 7,183, 4,562, and 5,501; their edge counts are 345,561, 132,904, and 135,932 [1, p. 39]. Do not conflate these subnetworks.
- Repository metadata independently labels Stanford3 as people linked by friendship/social relations, **undirected and unweighted**, and displays rounded counts 11.6K nodes / 568.3K edges [3].
- Read-only inspection of the existing ZIP found `socfb-Stanford3.mtx` and `readme.html`. The matrix member's **literal** first two lines are:

  ```text
  %MatrixMarket matrix coordinate pattern symmetric
  11586 11586 568309
  ```

  The first header has a **single `%`**, as actually present in this archive; do not silently report it as `%%MatrixMarket`. Entries start `23 1`, `63 1`, `193 1`. This is an integer-index coordinate-pattern representation with symmetric storage. Treat undirected edge count separately from the number of nonzeros after symmetrizing; avoid doubling edges or using these positive indices as zero-based array positions. Header dimensions/counts match the paper's Full Stanford row, but this check alone is not an edge-by-edge identity verification or an audit of all connectivity, duplicates, or self-loops.
- The ZIP member listing is evidence of a topology download, not evidence that original Facebook100 demographic fields were imported. No external dataset links mentioned in the paper were followed.

### SNAP combined Facebook ego network

- [2] says the Facebook data were collected from survey participants using a Facebook application, with profiles/features, circles, and ego networks. IDs are replaced, and feature meanings are obscured; matching feature values can remain observable without revealing their original interpretation.
- [2] reports **4,039 nodes and 88,234 edges**. It explicitly says those statistics combine ego networks **including ego nodes and their edges to friends**. The files table labels `facebook_combined.txt.gz` as edges from all ego networks combined, and the separate Facebook archive as ten anonymized networks.
- Therefore describe the local combined file as a **combined ego-network friendship topology**, not a representative full Facebook graph, not ten disconnected components, and not the Stanford3/Facebook100 September 2005 graph. Do not infer a collection date for the SNAP graph from [1].
- Existing `facebook_combined.txt.gz` has **88,234 nonempty lines**, with initial rows `0 1`, `0 2`, `0 3`, `0 4`, `0 5`. The combined file is an edge list; the richer profiles/circles advertised for the dataset are not thereby present in this file. Line count matches the page's edge count, but this check is not an exhaustive validation of uniqueness, symmetry, self-loops, or node coverage.
- The SNAP page directly names J. McAuley and J. Leskovec, *Learning to Discover Social Circles in Ego Networks*, NIPS 2012, and directly links `http://i.stanford.edu/~julian/pdfs/nips2012.pdf`. The user-permitted HTTPS form was attempted twice and failed before receiving a source response. **The paper was not read and is not in the read-source references.** All claims in this subsection are grounded in the read dataset page or local archive, not that unread paper.

## 3. Attribution policy and unresolved only-cite-read limits

- [4] states Creative Commons Attribution-ShareAlike, requires attribution, retaining notices and making the license clear, indicating changes, honouring additional dataset citation requests, and acknowledging the repository. It also requests sharing transformed data; the Stanford3 page asks users to consider uploading transformed/preprocessed data with transformation details [3–4]. This is a summary of the read policy, not an independent legal conclusion. **A license version was not established from the read policy text; do not invent one.**
- The read Stanford3 page requests a Rossi/Ahmed AAAI 2015 repository citation and lists both the 2012 Traud/Mucha/Porter article and the 2011 Traud/Kelsic/Mucha/Porter article, *Comparing Community Structure to Characteristics in Online Collegiate Social Networks* [3]. These are **citation requests observed in a read page**, not claims that either additional original was read. No links or references were followed to obtain the 2011 article.
- **Rossi/Ahmed original:** the only permitted URL returned HTTP 404. Use read pages [3–4] for repository attribution rather than pretending the paper was read. Page-reported metadata: Ryan A. Rossi and Nesreen K. Ahmed, *The Network Data Repository with Interactive Graph Analytics and Visualization*, AAAI, 2015. This metadata is not promoted to a read-paper bibliography entry.
- **McAuley/Leskovec original:** both identical permitted HTTPS attempts failed with a tunnel 502 error. Use read page [2] to attribute the SNAP data, explicitly describing its named original as page-reported if needed, rather than citing it as a read original.
- **Constraint status:** the four read references support truthful dataset and repository attribution. They do **not** establish that every paper-level citation request on the dataset/policy pages has been fully discharged. Under a strict requirement to include every requested original *and* cite only originals read, full compliance remains blocked by unavailable permitted originals and the additional unread 2011 article. This task does not waive those requests or claim compliance beyond the read-source fallback the user permitted.

Suggested bounded attribution text (for reference only; no manuscript was edited):

> We use the Stanford3 undirected, unweighted friendship topology distributed by Network Repository [3], with repository attribution and policy [4]; its corresponding Stanford Full graph is documented by Traud, Mucha, and Porter [1]. We separately use SNAP's combined Facebook ego-network edge list [2], whose dataset page credits McAuley and Leskovec (NIPS 2012). The latter original and the Rossi–Ahmed repository original could not be read at the permitted URLs; provenance claims here rely only on the read sources.

## 4. Exact new original-source accesses, hashes, and errors

All timestamps UTC. Automatic redirects were disabled; no alternate URL, search, abstract, or citation-chain fallback was attempted. HTTP response headers, exact machine-readable errors, and full start/end times are retained in `sources/dataset_provenance_accesses.json`.

| Requested URL | Start UTC | Finish UTC | Result | Saved bytes / SHA-256 |
|---|---|---|---|---|
| `https://arxiv.org/pdf/1102.2166` | 2026-11-02T17:10:30.099263+00:00 | 2026-11-02T17:10:35.952780+00:00 | HTTP 200; same returned URL; PDF read in relevant sections | 933918; `ddac5bf24872cc9706d42b320162d060c0012236f08fd6a3e1285e6254ebe847` |
| `https://i.stanford.edu/~julian/pdfs/nips2012.pdf` | 2026-11-02T17:10:35.952910+00:00 | 2026-11-02T17:10:36.685025+00:00 | `URLError(OSError('Tunnel connection failed: 502 Bad Gateway'))` | No source response/body received; no PDF saved; no hash available |
| `https://networkrepository.com/pubs/aaai15-network-data-repo.pdf` | 2026-11-02T17:10:36.685115+00:00 | 2026-11-02T17:10:38.061920+00:00 | HTTP 404; same returned URL; non-PDF response; paper NOT read | 179693; `c382bab6db2469a3b9f73145a4bd6dcc609bd17bdfb312b9ac7c0e78452527c4` (error body, NOT a paper hash) |
| `https://i.stanford.edu/~julian/pdfs/nips2012.pdf` (identical-URL retry) | 2026-11-02T17:11:51.382301+00:00 | 2026-11-02T17:11:51.642121+00:00 | `URLError(OSError('Tunnel connection failed: 502 Bad Gateway'))` | No source response/body received; no PDF saved; no hash available |

Saved original: `sources/traud_mucha_porter_1102.2166.pdf`.

Full pypdf extraction: `sources/traud_mucha_porter_1102.2166.txt`, SHA-256 `62ba9156156108687ab88d94109555fbeef049d981d6baf466c08c5cc81e4b8c`. PDF page delimiters are included to preserve location. `sources/traud_stanford_table_excerpt.txt` is a local locator/excerpt artifact, not another source; the Full Stanford row was verified against p. 39.

Rossi HTTP error response: `sources/rossi_ahmed_aaai15_network_data_repo.http_response`; retained as failure evidence only, not treated as a PDF or read reference.

## 5. Existing local snapshots and archives checked (no new downloads)

Read/snapshot timestamps and text hashes: `sources/dataset_provenance_local_snapshots.json`. Archive checks: `sources/dataset_provenance_archive_checks.json`. The following SHA-256 values were recalculated from local bytes and match `/work/data/manifest.json`:

| Local file | Bytes | SHA-256 | Local check time UTC |
|---|---:|---|---|
| `/work/data/snap_page.html` | 13634 | `5274558a65bb9881ee282a6ecebea8b1bae14e71462eaf8afd6ca6483913844b` | 2026-11-02T17:11:18.133428+00:00 |
| `/work/data/stanford_page.html` | 171309 | `490680de85fd8ca0290432320263520f9f5e36e2e7a17b0d8d785c70adddfcef` | 2026-11-02T17:11:18.155934+00:00 |
| `/work/data/nr_policy.html` | 161684 | `02fadef0b66b1d8c4b1be021ff8141c9477a037ce8eea7eb1d42443def5fe5d6` | 2026-11-02T17:11:18.178643+00:00 |
| `/work/data/facebook_combined.txt.gz` | 218576 | `125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7` | 2026-11-02T17:12:18.278713+00:00 |
| `/work/data/socfb-Stanford3.zip` | 1649740 | `b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d` | 2026-11-02T17:12:18.278713+00:00 |

The pre-existing manifest records archive acquisition URLs as `https://snap.stanford.edu/data/facebook_combined.txt.gz` and `https://nrvis.com/download/data/socfb/socfb-Stanford3.zip`; these URLs were not requested in this task. No collection time is inferred from archive HTTP Last-Modified fields.

Locally stripped page text for inspection is saved as `sources/snap_facebook_page.txt`, `sources/nr_stanford3_page.txt`, and `sources/nr_policy_page.txt`. HTML parsing did not execute scripts or request linked resources. No new empirical analyses, dataset transformations, or experimental protocol claims were made.
