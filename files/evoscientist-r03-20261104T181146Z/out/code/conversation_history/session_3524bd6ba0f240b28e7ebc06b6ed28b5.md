## Summarized at 2026-11-04T18:14:50.936945+00:00

<message type="human">Research-only safe literature/template acquisition. Work root /work empty. User prohibits accessing or trying to identify an unspecified prior paper on benchmark selection/prediction OR any pages citing/discussing it. Therefore NO topical search, citation graph, related-paper pages. Access ONLY exact starter arXiv papers IDs 2210.07316 (MTEB), 2402.14992 (tinyBenchmarks), 2407.12844 (metabench), 2405.10938 (Observational scaling), 2412.06540 (Sloth), and official conference template/rules pages. Avoid downstream pages and do not search unknown forbidden paper. Fetch permitted paper fulltexts via export.arxiv.org/pdf or arxiv.org/pdf and save under /work/literature with reading notes explicitly what you actually read (methods, limitations), verified metadata and BibTeX /work/literature/references.bib. Choose latest conference whose official template can be retrieved, prefer NeurIPS 2026 if available as current date Nov4 2026; else latest available verified (2025 not silent). Download official style files/checklist/rules to /work/paper and document URLs and page limit. Write /work/literature/sources.md + /work/literature/access_log.md (any accidental prohibited material must immediately stop and record). This is artifact production via research, not code implementation; do not delegate code. Return concrete template path, rules, paper insights and limitations. Can use requests/downloads, inspect PDF pdftotext. Read relevant paper-navigator skill if useful but DO NOT do its searches because forbidden content.</message>
<message type="ai">
  <tool_call id="call_e8aa7ba10e6844238e6a28d415e570c5" name="search_observations">{"limit": 3, "memory_type": null, "mode": "ranked", "query": "safe exact arxiv paper acquisition conference templates access restrictions", "scope": null}</tool_call>
</message>
<message type="tool">{"results": []}</message>
<message type="ai">
  <tool_call id="call_ce358975a7594964b7c871fa15f01ec4" name="think_tool">{"reflection": "No relevant observation found. This task has a strict URL/content allowlist: only five specified arXiv fulltexts and official conference rules/templates. I must avoid discovery searches, citation graphs, downstream pages, and identifying the unspecified forbidden work. Read the paper-navigation skill only for PDF acquisition/reading guidance, not its search workflow. Fetch exact PDFs and official NeurIPS 2026 endpoints directly, log every attempted URL and redirects, and stop if prohibited material is encountered. Need robust metadata/BibTeX from the permitted fulltexts and explicit reading-scope notes."}</tool_call>
</message>
<message type="tool">Reflection recorded: No relevant observation found. This task has a strict URL/content allowlist: only five specified arXiv fulltexts and official conference rules/templates. I must avoid discovery searches, citation graphs, downstream pages, and identifying the unspecified forbidden work. Read the paper-navigation skill only for PDF acquisition/reading guidance, not its search workflow. Fetch exact PDFs and official NeurIPS 2026 endpoints directly, log every attempted URL and redirects, and stop if prohibited material is encountered. Need robust metadata/BibTeX from the permitted fulltexts and explicit reading-scope notes.</message>
<message type="ai">
  <content>No relevant prior memory was found. I’ll use only the five specified arXiv fulltexts and official conference template/rules pages—no topical or citation searches—and record access attempts and exactly which sections I read.</content>
  <tool_call id="call_0cf39bde2d3b414aa39931c4a2f892d2" name="ls">{"path": "/skills/paper-navigator"}</tool_call>
</message>
<message type="tool">['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']</message>
<message type="ai">
  <tool_call id="call_ba181c3444c44bc4be51db93a06b1cac" name="read_file">{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-379 of 379 @@
---
name: paper-navigator
description: "Find and read academic papers (S2 + arXiv). Disambiguate ambiguous queries, search by keyword + citation graph + recommendations + snippets, judge relevance against an authored rubric, and read with L1/L2/L3 strategy. Trigger phrases: find papers, search papers, related work, citation analysis, recent advances, read this paper, baseline with code. Do NOT use for: survey reports (research-survey), idea generation (research-ideation), Related Work sections (paper-writing)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '3.4.1'
  tags: [core, research, literature, papers, search, rubric]
---

# Paper Navigator

Find and read academic papers. Route by **intent**, judge by **relevance**.

```
        User
         │
         ▼
   ┌── Router ──┐
   │            │
   ▼            ▼
 POINT      LIST/ITERATIVE
(1 paper)   (Probe + up to 3 paper rounds:
             R2 breadth / R3 deepen / R4 close)
```

The agent does relevance judgment — no LLM-as-judge is called, no numeric scoring. You author the rubric, you triage each paper, you rank by relevance.

## Setup

Script paths in this document are relative to this skill's directory. Run via `python scripts/&lt;name&gt;.py`.

**Dependencies**: `pip install deepxiv-sdk httpx` (also listed in `requirements.txt` at the skill root). Install into the environment the user is working in.

arXiv access (`arxiv_monitor`, `scholar_search` fallback) uses the DeepXiv SDK: `pip install deepxiv-sdk`, then `deepxiv token` once to provision a **free** API token (saved to `~/.env`). The skill reads the token from `DEEPXIV_API_TOKEN`/`DEEPXIV_TOKEN` in the environment, or from `./.env` / `~/.env`.

| Env var | Used by | Notes |
|---|---|---|
| `S2_API_KEY` | All S2 scripts | Without it: `scholar_search` falls back to arXiv (via DeepXiv); `citation_traverse` / `recommend` / `snippet_search` are disabled |
| `DEEPXIV_API_TOKEN` | `arxiv_monitor`, `scholar_search` fallback | Get a free token: `deepxiv token` (writes `~/.env`). Also read from `DEEPXIV_TOKEN` and `./.env`/`~/.env`. ~10,000 req/day |
| `JINA_API_KEY` | `fetch_paper` | Free tier works without key |
| `GITHUB_TOKEN` | `github_search`, `find_code` | Higher rate limits |
| `PAPER_NAV_PAPERS_DIR` | `fetch_paper` full text | No default — set or pass `--metadata-only` |

Full env-var list: `references/env-vars.md`.

---

## Five Red Lines (always)

1. **Track history.** Don't re-run a query you already ran. Empty result → change angle, not synonyms.
2. **Search a gap, not a vibe.** Every query maps to one missing piece of information. No stacked-keyword bags.
3. **One query = one concept.** Split comparisons (`A vs B`), multi-property asks, and multi-year spans into separate calls.
4. **Never hallucinate.** Every fact (title, author, year, citation count, content) comes from a tool result.
5. **Quote-or-zero.** When you claim a paper meets a criterion, quote a ≤80-char span from its abstract / tldr / snippet. No quote → do not claim the paper meets that criterion. (This guards against hallucination; it does not drive a numeric score.)

---

## Router

| Branch | User signal | Cadence | Output |
|---|---|---|---|
| **POINT** | Title quoted, URL, arXiv/DOI/PMID/S2 ID, "read this paper" | 1 call | Paper Card |
| **LIST** (default) | "find papers about X", "is there a paper that …?", "papers satisfying A and B" | Probe + up to 3 rounds (R2/R3/R4) | Shortlist with per-criterion evidence |
| **ITERATIVE** | "survey of X", "30+ papers on Y", called from `research-survey` / `research-ideation` | Probe + up to 3 rounds (R2/R3/R4) | Ranked table (hand off to research-survey for the report) |

**Default to LIST when unsure.** Don't add `survey` / `review` to LIST queries — it down-ranks the canonical research papers the user wants.

**Output format follows the caller:** the Output column above is the structured form (skill callers). Direct user calls default to **Narrative** — see Step 6 "Output mode".

Ambiguous query (project nickname, codename, single capitalized word with zero hits) → run `scholar_search` exact + web/GitHub search first to resolve identifiers, then re-route.

---

## POINT branch (known paper)

| Input | Command | Output |
|---|---|---|
| URL | `python scripts/fetch_paper.py --url &lt;URL&gt;` | Paper Card + reading notes (see `references/reading-strategy.md` for L1/L2/L3) |
| Title quoted | `python scripts/match_paper_by_title.py --title "&lt;title&gt;"` (add `--fallback-search` for typos) | Paper Card |
| Bare ID (arXiv / DOI / S2 / CorpusId) | `python scripts/fetch_paper.py --paper-id &lt;ID&gt; --metadata-only` | Paper Card |

**Paper Card:**

```
📄 **&lt;Title&gt;**
Authors: &lt;First Author&gt; et al. | Year: &lt;Y&gt; | Venue: &lt;V&gt;
Citations: &lt;N&gt; | ID: &lt;ArXiv:xxxx.xxxxx&gt; | DOI: &lt;...&gt;
TLDR: &lt;one sentence&gt;
```

Stop here. Do not chain to citation expansion unless asked.

---

## LIST / ITERATIVE branch — 6 steps

### Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch. When the user gives only a bare noun (concept / model / algorithm / benchmark name) with no direction, default intent is "trace the lineage" — foundations, evolution, current state — not applications or a generic `survey`.

### Step 2: Author the RUBRIC (via `think_tool`)

Emit a structured block before any search. It persists across rounds and every later step references it.

```
RUBRIC for "&lt;user query verbatim&gt;"
Branch: LIST | ITERATIVE
Criteria (2–4, atomic; mark each [core] or [secondary]):
  C1 [core]     &lt;what the paper MUST do/be — one sentence&gt;
  C2 [core]     &lt;...&gt;
  C3 [secondary] &lt;...&gt;
Named entities to preserve verbatim: [&lt;ent1&gt;, &lt;ent2&gt;, ...]
Angle tags (3–5 sub-topic axes): [&lt;tag1&gt;, &lt;tag2&gt;, &lt;tag3&gt;]
Recency signal: [none | recency cue — defined in Step 3]
Disqualifiers: [&lt;auto-reject if abstract shows this&gt;]
```

Rules:
- **Criteria** atomic (one condition each), non-redundant. Mark each `[core]` (must-have) or `[secondary]` (nice-to-have) — this guides relevance ranking, no weights, no math.
- **Named entities** = proper-noun / technical-term anchors from the user's query. Every entity appears verbatim in ≥1 query across Probe + R2.
- **Angle tags** = sub-topic axes (`method`, `task`, `dataset`, `evaluation`, `domain`, …). No two queries in the same round share a tag.
- **Recency signal** = whether the user query carries a recency cue (see Step 3 recency trigger). Drives `--year-min` and the Step 6 recency tie-break.
- **Disqualifiers** = "specifically X, **not** Y" exclusions. Tripping a disqualifier → Irrelevant.

For ITERATIVE, criteria can be lighter (e.g. `covers topic` + `is canonical`); disqualifiers may be empty.

### Step 3: Search — Probe then Multi-round (Breadth → Deepen → Close)

Probe first to grasp the user's need comprehensively, then run up to **3 paper rounds** (R2 breadth / R3 deepen / R4 close). Decide round-by-round whether more rounds are needed (Step 5 gate) — **do NOT fix a round count**. There is no R5; the cap is 3 paper rounds.

**Probe (prerequisite — NOT counted in the 3 rounds, 2 parallel queries):** establish a comprehensive understanding of the need and lift named entities / angle gaps.
- `Q-broad` — canonical phrasing of the topic (angle: `general`)
- `Q-narrow` — a specific mechanism / sub-question / method (angle: tagged)

```bash
python scripts/scholar_search.py --query "&lt;Q-broad&gt;"  --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "&lt;Q-narrow&gt;" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
```

`--output --append` auto-dedupes by `paperId` across rounds (built into the script), so a paper found by two queries is written once. Read `/tmp/pool.jsonl` to inspect (Step 4 triage). From Probe titles + tldrs, lift:
- recurring **named entities** (algorithm / benchmark / dataset / model names),
- **angle gaps** (Step-2 tags not seen),
- vocabulary from **adjacent communities**.

**R2 — Breadth (default — skipped only via the Step 5 early exit; 2–3 parallel queries).** Broad academic queries on the core object + canonical terms lifted from Probe. The main axis is the user's core object + canonical mapping; Probe only supplies high-confidence supplements.

**R3 — Targeted deepening (optional, when Step 5 gate says CONTINUE, 2–3 parallel queries).** Driven by the gap→strategy map below — fill the specific gap Step 4 triage exposed.

**R4 — Closing (optional, 2–3 parallel queries).** Fill whatever key gap remains after R3: a missing representative work, a strong baseline, a counter-example, or an uncovered sub-direction.

**Gap→strategy map** (R3/R4 are driven by the Step-4 triage gap, not vibes):

| Gap surfaced by Step 4 triage | R3/R4 strategy |
|---|---|
| Foundational work drowned by recent papers | `--year-max`, search the original mechanism / early terminology |
| User wants SOTA / frontier, or R2 skewed old | `--year-min` last 2 years |
| Thin single-source evidence | swap terminology / team / benchmark for multi-source corroboration |
| Incomplete A-vs-B comparison | separately fill A, B, and an upper-topic query (no `survey`/`review` terms) |
| Contradictory findings | verification query, prefer authoritative venue / high-cite / direct experiment |

**Per-query rules:**
- 3–6 words preferred (English academic terms); &lt;3 over-recalls, &gt;6 dilutes ranking.
- Use academic terms (`mechanism`, `benchmark`); no `how it works` phrasing.
- **Do NOT add `survey` / `review` / `tutorial` terms** — they bias results toward review papers and crowd out the research papers the user wants. Only use them when the user explicitly asks for a survey/review.
- Bare entity names; no `paper` / `pdf` / `arxiv` / `original`.
- Split comparisons / multi-property; if short of 2–3 queries, fill with upper-topic or representative method.
- Time intent goes into `--year-min/max` params, never year words in the query.
- Forbidden: `"…"`, `(..)`, `OR`, `AND`, `|`, `site:`, `filetype:`.
- No two queries in one round may share &gt;60% of content tokens (after stop-words).

**Recency trigger (query layer).** When the user query contains a recency signal (最新 / 近年 / 近期 / 近两年 / 前沿 / SOTA / latest / recent / state-of-the-art), set `--year-min` to **last 2 years** from R2 onward — Jan 1 of the year before the current system year (e.g. system date 2026-08 → `--year-min 2025`). Do not extend to 3–4 years.

**Without `S2_API_KEY`:** swap `scholar_search` for `arxiv_monitor --keywords "&lt;variant&gt;" --match-mode flexible --days 3650`.

**Citation expansion** (ITERATIVE, or LIST after ≥3 All-core/Partial seeds):
```bash
python scripts/citation_traverse.py --paper-id &lt;SEED&gt; --direction co-citation --limit 15 --output /tmp/pool.jsonl --append
python scripts/citation_traverse.py --paper-id &lt;SEED&gt; --direction forward --limit 20 --min-citations 20 --year-min 2022 --output /tmp/pool.jsonl --append
python scripts/recommend.py --positive &lt;SEED1&gt;,&lt;SEED2&gt; --limit 15 --output /tmp/pool.jsonl --append
```

### Step 4: Triage — All-core / Partial / Irrelevant

After every round, classify each new paper and stamp a **per-criterion mask** (✓ / ~ / ✗) over the RUBRIC — **no numeric scoring**. The mask is what makes conjunctive queries ("papers satisfying A and B") terminate correctly: only a paper with `✓` on **every [core] criterion** is `All-core`. Emit a `think_tool` block:

```
TRIAGE round=&lt;n&gt;  query="&lt;q&gt;"
  All-core   (k): &lt;paperId&gt; "&lt;title-≤60&gt;" Y=&lt;year&gt; · [C1✓ C2✓ (C3~)]   every [core] ✓
                 C1: "&lt;≤80-char quote&gt;"
                 C2: "&lt;≤80-char quote&gt;"
  Partial    (k): &lt;paperId&gt; "&lt;title&gt;" Y=&lt;year&gt; · [C1✓ C2✗]              some [core] ✓
                 C1: "&lt;≤80-char quote&gt;"
  Irrelevant (k): &lt;paperId&gt; "&lt;title&gt;"                                   no [core] ✓, or trips disqualifier — drop
```

| Tier | Mask | Quotes |
|---|---|---|
| `All-core` | every [core] criterion `✓` (no `✗` on any [core]) | one ≤80-char quote per [core] criterion |
| `Partial` | at least one [core] `✓`, but some [core] `✗`/`~`; or only [secondary] support | one quote per `✓` [core] criterion |
| `Irrelevant` | no [core] `✓`, or trips a disqualifier | none — drop from later rounds |

`✓` = abstract/tldr clearly supports. `~` = partial / inferable. `✗` = no support or contradicts. [secondary] criteria don't set the tier but still get a mask symbol.

Rules:
1. **Dedup across rounds** by `paperId` first, then normalised title. Keep the stronger mask.
2. **Disqualifier check** beats all other matches → Irrelevant.
3. **Re-diagnose gaps:** note any [core] criterion with 0 `✓` across All-core+Partial, and any angle tag with 0 All-core/Partial → that's the next refine target (feeds the Step 3 gap→strategy map).
4. **No fabrication:** missing abstract → stamp `~`, do not infer from training data.

The per-criterion quotes collected here are exactly what the Step 6 Rank-1 bar and the structured LIST template cite — do not skip them.

**Snippet upgrade** for borderline papers (abstract silent on a [core] criterion): batch-fetch real body text:
```bash
python scripts/snippet_search.py --query "&lt;criterion phrase&gt;" \
  --paper-ids "CorpusId:1,CorpusId:2,..." --limit 50
```

### Step 5: Saturation Gate

After **Probe and each round**, decide CONTINUE vs STOP by **whether key gaps remain** — not by counting papers.

**Early exit after Probe (single-recommendation / conjunctive queries only, K=1–2):** for "is there a paper that …?", "recommend a paper", "what's the canonical X", or conjunctive "papers satisfying A **and** B" queries, if an `All-core` paper already covers every [core] criterion, **STOP** without running further rounds. This preserves the fast path where one probe hit settles a POINT-like query (≈2 queries), which matters under keyless S2 rate limits. For broader question shapes ("find papers about …" K=3–5, or 30+-paper ITERATIVE), do **not** use this early exit — apply the full STOP conditions below.

**STOP when ALL hold:**
- ≥1 `All-core` paper exists — a *single* paper with `✓` on every [core] criterion. This is required so conjunctive queries like "papers satisfying A **and** B" can't pass on two different papers that each cover only one side, AND
- every angle tag has ≥1 All-core/Partial paper, AND
- no key claim rests on a single source,
- OR further rounds stop surfacing anything new (empty recall / all duplicates).

**CONTINUE to the next round (R3 / R4) otherwise**, driven by the gap→strategy map:
- 0 `All-core` papers → fill the [core] criterion still `✗`.
- An angle tag has 0 All-core/Partial → open that angle.
- A key claim rests on a single source → multi-source corroboration.

**Re-decompose** (rubric is wrong) if R2 returns 0 All-core AND 0 Partial across the board: report the strongest Partial candidate(s) + ask the user to relax a criterion.

**Round caps:** LIST and ITERATIVE up to 3 paper rounds (R2/R3/R4). POINT is a single fetch (no multi-round). If still not saturated at the cap, go to Step 6 and report which criteria / angle tags were not covered.

**The gate is mechanical about gaps** — do not skip rounds because "the results look right"; do not run extra rounds once the STOP conditions hold. The single-All-core-suffices shortcut applies only to the K=1–2 early exit above, not to broader queries.

### Step 6: Rank and Output

**Gather:** every All-core and Partial paper from across all rounds (dedup by `paperId`). Drop Irrelevant.

**Rank by relevance — the model judges, no numeric score.** Order the gathered papers by how directly each answers the user's question: All-core before Partial; a paper satisfying every [core] criterion ranks above one satisfying only some. This is a judgment call, not a formula — **do not compute a weighted_total**.

**Recency-aware tie-break.** When the RUBRIC flagged a recency signal (cues defined in Step 3), break ties / near-ties in favor of the more recent paper (`year` DESC), applied **after** relevance. Recency rides behind relevance, never ahead of it.

**K (soft ceiling — prevents pool-dumping):**

| Question shape | K |
|---|---|
| "Exactly N papers" | N |
| "Is there a paper that …?" / "Recommend a paper" | 1–2 (bold top-1) |
| "Find papers about …" | 3–5 |
| "Survey of …" / ITERATIVE | ≤ 10 (soft cap) + 1–2 surveys if the user explicitly asked for them |

K is a soft guide, not a formula. For broad "survey / categorize the field" queries the dominant failure mode is dumping the whole accumulated pool (often 30–50 papers, most off-criterion) into the output, burying the few on-criterion papers. Rank by relevance, keep the top K, and move the rest to an **"Also relevant (not ranked)"** list — never pad the ranked list with weak papers to reach a count.

**Rank-1 quality bar.** For single-recommendation queries ("is there a paper that …?", "recommend a paper", "what's the canonical X") the bolded top-1 must be an **All-core** paper — clearly satisfying every [core] criterion with a quote. Rank 1 carries disproportionate weight in user perception; fronting a Partial paper at top-1 reads as a confident wrong answer. If no paper clears the bar, lead with "No fully-matching paper found" and present the strongest near-miss honestly with its gaps.

If no All-core paper survives after the round cap, report "no fully-matching paper found", list strongest Partial candidates + their gaps, stop.

**Output mode (caller inference).** Pick the format by what the request demands, not by an explicit flag:
- **Structured** (formats below) — when the request demands machine-consumable output: a ranked list/table, per-criterion evidence, or hand-off to a downstream skill. Default for skill callers (`research-survey`, `research-ideation`, `paper-writing`, `experiment-pipeline`).
- **Narrative** (see "Narrative output" below) — the default for direct user calls: natural-language questions with no structured-output demand.

**Structured output formats (skill callers):**

LIST (shortlist with evidence):
```
**Top matches:**
- **&lt;paperId&gt;** "&lt;Title&gt;" — &lt;Authors&gt; et al., &lt;Year&gt;, &lt;Venue&gt;, cited by &lt;N&gt;. &lt;URL&gt;
  - C1 [core]: "&lt;quote&gt;"
  - C2 [core]: "&lt;quote&gt;"
  - C3 [secondary]: "&lt;quote&gt;"

**May also be relevant:**
- &lt;paperId&gt; "&lt;Title&gt;" — &lt;Authors&gt; et al., &lt;Year&gt;, cited by &lt;N&gt;. &lt;URL&gt; (Partial: only C3)
```

ITERATIVE (ranked table):
```
| # | Title | Authors | Year | Venue | Cited by | Link |
|---|-------|---------|------|-------|----------|------|
| 1 | …    | … et al. | 2024 | NeurIPS | 1234 | &lt;URL&gt; |
```

POINT: Paper Card (above).

**Narrative output (direct user callers).**

Deliver structured knowledge, not a search trace. Strip process words before output (`Probe`, `R2/R3/R4`, `All-core/Partial`, "rounds done") unless the user explicitly asks for a trace.

- **Information-first, not list-first.** Unless the user only wants a paper list, do not collapse the answer into "title + one-line contribution". Build the cognitive structure the user needs (timeline / topic grouping / comparison / mechanism breakdown / evidence verification / reading path), then place papers into it as evidence nodes.
- **One main form + 2–3 auxiliary forms.** The main form carries the answer's logic (timeline, topic grouping, comparison, mechanism breakdown, evidence grading, reading path, mini-survey); 2–3 auxiliary forms (paper card, table, evidence grading, annotated bibliography, reader payoff) aid readability. Do not stack every form.
- **Intent → form (condensed):** latest/SOTA → status-judgment + table; origin/foundation → timeline + source-paper analysis; A-vs-B → conclusion + dimension comparison; mechanism → mechanism breakdown + evidence interleaving; benchmark/data → verification + evidence table; landscape → topic grouping + reading path.
- **Citation rules:** a core paper shows **Title (Venue Year)** on first mention (never author-only like `Zhang et al.`); every cited paper carries its returned `[N]`. **Tables MAY contain `[N]` markers.** At the end of the answer, list every cited paper by number in **IEEE style** (with citation count appended): `[N] A. Author et al., "Title," Venue, Year, cited by N. [Online]. Available: URL`. IEEE rules: author names as `Initial. Surname` (e.g. `A. Vaswani`); join multiple authors with commas and `and`; ≥3 authors → `A. Firstauthor et al.`; title in double quotes; then `Venue, Year`; append `cited by N` (the tool's citationCount); end with `[Online]. Available: URL` for the link. Omit a field only if the tool genuinely did not return it (never fabricate); authors and citation count must appear whenever returned.
- **Length:** single-point 600–1200 words; comparison/retrieval 1200–2500; landscape/timeline 2000–3500. Do not sacrifice evidence structure for brevity.
- **Quote-or-zero still applies** — every claim a paper is used to support is still backed by a ≤80-char quote (Red Line 5, anti-hallucination); the narrative just renders it as `[N]` instead of showing the raw quote.

**Pre-output checklist (mandatory).** Before emitting the answer, verify each box.

- [ ] **Pool gathered** from every round's triage, deduped by `paperId`, Irrelevant excluded.
- [ ] **Ranked by relevance** (judgment, not a numeric score) — All-core before Partial.
- [ ] **Recency tie-break applied** when a recency signal is present (`year` DESC after relevance).
- [ ] **Rank-1 clears the bar** for single-recommendation queries (clearly satisfies every [core] criterion with a quote) — or you've reported "No fully-matching paper found".
- [ ] **Every cited paper has ≥1 supporting quote** for the claim it's used for (quote-or-zero, Red Line 5 — anti-hallucination).
- [ ] **Output ≤ K** (soft cap); surplus relevant papers sit in "Also relevant (not ranked)", not the ranked list.
- [ ] **Narrative mode only** — every cited paper appears in the end-of-answer numbered reference list in **IEEE style with authors + citation count** (`[N] A. Author et al., "Title," Venue, Year, cited by N. [Online]. Available: URL`), and the body strips process words (`Probe` / `R2` / `All-core/Partial`).

If any box is unchecked, return to Step 6 — do not output.

---

## Tool Cheat Sheet

| Need | Script | Notes |
|---|---|---|
| Keyword search | `scholar_search.py` | S2 → arXiv fallback on missing key / 429 |
| Title → record | `match_paper_by_title.py` | S2 exact-match; `--fallback-search` for typos |
| Citation graph | `citation_traverse.py` | `--direction forward/backward/co-citation`; `--min-citations`; `--year-min/max`; `--smart-sort`; `--enrich` |
| Similar papers | `recommend.py` | seed-based; `--per-seed` for diverse seeds |
| Author papers | `author_search.py` | `--sort-by year/citations` |
| New arXiv | `arxiv_monitor.py` | `--categories cs.CL` or `--keywords "x,y" --match-mode flexible` |
| Trending | `trending.py` | citation velocity |
| Body-text snippets | `snippet_search.py` | `--paper-ids c1,c2,c3 --limit 50` (1 call, not N) |
| Fetch full text | `fetch_paper.py` | Saves to `$PAPER_NAV_PAPERS_DIR/&lt;id&gt;.md`; stdout truncated to 2000 chars |
| Code repo (known paper) | `find_code.py --arxiv-id &lt;ID&gt;` | Official repo lookup |
| Code repo (unpublished) | `github_search.py` | When no arXiv ID exists |
| HF leaderboard / SOTA | `sota.py` | sorted by downloads |
| HF datasets | `dataset_search.py` | Query short-name (`imdb`, `sst2`), not task description |
| Saturation gate (optional) | `saturation.py` | JSONL log of per-round yields; `estimate` returns STOP/CONTINUE |

All discovery scripts: `--limit N`, `--json`, `--output FILE`, `--append`; accept S2 / arXiv / DOI / CorpusId IDs. `--output --append` auto-dedupes by `paperId` across rounds (within-batch + cross-file), so the pool stays clean.

---

## Rate limits

| API | Without key | With key |
|---|---|---|
| Semantic Scholar | ~1 req / 3s, no parallel | 100 req/min, parallel OK |
| arXiv | 1 req / 3s (courtesy) | N/A |
| GitHub | 10 req/min | 5,000 req/hr |
| HuggingFace | 500 req / 300s | Higher with `HF_TOKEN` |

Global S2 pacer + circuit breaker (5 failures → 60s cooldown). Retries: 3s / 6s / 12s / 24s / 48s.

Without `S2_API_KEY`: use `scholar_search` (arXiv fallback) + `arxiv_monitor`. Skip `citation_traverse` / `recommend` / `snippet_search` — they're S2-only; do not retry.

---

## References

| File | Read when |
|---|---|
| `references/env-vars.md` | Setting environment variables |
| `references/search-principles.md` | Per-query rules, gap diagnosis, rate-limit recovery |
| `references/iterative-collection.md` | ITERATIVE corpus collection (30+ papers): phase mapping, citation expansion, escape hatches |
| `references/disambiguation.md` | Query is a project nickname / codename |
| `references/reading-strategy.md` | L1 / L2 / L3 reading framework |
| `references/api-reference.md` | S2 / arXiv / Jina / HF / GitHub endpoint details |
| `references/arxiv-categories.md` | arXiv category codes |
| `references/output-formats.md` | Baseline / Disambiguation / Reading-Notes / Citation-Graph templates |

References are self-contained. Don't chain between them — return here to re-route.

---

## Hand off to

| Goal | Skill |
|---|---|
| Survey report | `research-survey` |
| Idea generation | `research-ideation` |
| Related Work section | `paper-writing` |
| Baseline + experiment | `experiment-pipeline` |</message>
<message type="ai">
  <tool_call id="call_d5284f4564a44b6890eb44b296d28847" name="write_todos">{"todos": [{"content": "Acquire only the five allowed PDFs with audited URL access and verified metadata.", "status": "in_progress"}, {"content": "Read permitted methods/evaluations/limitations and write source-grounded notes and BibTeX.", "status": "pending"}, {"content": "Retrieve latest verified official conference template, checklist and rules; document page limit.", "status": "pending"}, {"content": "Audit artifacts and provide concise insights, limitations and concrete paths.", "status": "pending"}]}</tool_call>
</message>
<message type="tool">Updated todo list to [{'content': 'Acquire only the five allowed PDFs with audited URL access and verified metadata.', 'status': 'in_progress'}, {'content': 'Read permitted methods/evaluations/limitations and write source-grounded notes and BibTeX.', 'status': 'pending'}, {'content': 'Retrieve latest verified official conference template, checklist and rules; document page limit.', 'status': 'pending'}, {'content': 'Audit artifacts and provide concise insights, limitations and concrete paths.', 'status': 'pending'}]</message>
<message type="ai">
  <tool_call id="call_5373e8d9922b47ccac7515e25cc2bff9" name="ls">{"path": "/work"}</tool_call>
</message>
<message type="tool">['/.langgraph_api/']</message>
<message type="ai">
  <tool_call id="call_012b2f7444b44839b5aa3291015d044c" name="execute">{"command": "pwd; python -c \"import requests,shutil; print('requests ready'); print('pdftotext:',shutil.which('pdftotext')); from pathlib import Path; p=Path('/work'); print('host work exists',p.exists()); p.mkdir(exist_ok=True); (p/'literature').mkdir(exist_ok=True); (p/'paper').mkdir(exist_ok=True)\"", "timeout": 20}</tool_call>
</message>
<message type="tool">/work

[stderr] Traceback (most recent call last):
[stderr]   File "&lt;string&gt;", line 1, in &lt;module&gt;
[stderr] ModuleNotFoundError: No module named 'requests'

Exit code: 1
[Command failed with exit code 1]</message>
<message type="ai">
  <content><reasoning>**Preparing network access.**</reasoning></content>
  <tool_call id="call_0339b9a1c7b14940a86337a233e796ff" name="execute">{"command": "python - &lt;&lt;'PY'\nimport urllib.request, pathlib, shutil, datetime, json, hashlib, time\nroot=pathlib.Path('/work'); (root/'literature').mkdir(exist_ok=True); (root/'paper').mkdir(exist_ok=True)\nlog=root/'literature/access_log.md'\nlog.write_text('# Access log\\n\\nPolicy: only arXiv PDFs for 2210.07316, 2402.14992, 2407.12844, 2405.10938, 2412.06540 and official conference template/rules resources. No topical search, citation graph, related-paper pages, metadata APIs, repository visits, or external PDF hyperlinks. PDF bibliographies will not be read. No attempt to identify the unspecified prohibited paper.\\n\\nMemory preflight: no relevant observations. Read local paper-navigator skill; discovery workflow disabled. Local /work listing showed no task artifacts. Initial environment probe failed importing requests; using standard-library urllib instead (no network in probe).\\n\\n## Network requests\\n')\nclass Guard(urllib.request.HTTPRedirectHandler):\n def redirect_request(self,req,fp,code,msg,headers,newurl):\n  with log.open('a') as f:f.write(f'- REDIRECT {req.full_url} -&gt; {newurl}; not followed automatically.\\n')\n  return None\nopener=urllib.request.build_opener(Guard)\nfor id in ['2210.07316','2402.14992','2407.12844','2405.10938','2412.06540']:\n for host in ['export.arxiv.org','arxiv.org']:\n  url=f'https://{host}/pdf/{id}'\n  try:\n   req=urllib.request.Request(url,headers={'User-Agent':'ResearchAcquisition/1.0 (exact allowlisted PDF only)'})\n   with opener.open(req,timeout=45) as r:\n    data=r.read(); status=r.status; typ=r.headers.get('Content-Type','')\n   with log.open('a') as f:f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()} GET {url} — HTTP {status}; {typ}; {len(data)} bytes.\\n')\n   if not data.startswith(b'%PDF'): raise ValueError('Non-PDF response; not inspected')\n   p=root/'literature'/f'{id}.pdf';p.write_bytes(data)\n   with log.open('a') as f:f.write(f'  Saved `{p}`; SHA256 `{hashlib.sha256(data).hexdigest()}`.\\n')\n   print(id,'saved',len(data));break\n  except Exception as e:\n   with log.open('a') as f:f.write(f'- GET {url} failed: {type(e).__name__}: {e}. Response body not read.\\n')\n   print(id,host,type(e).__name__,str(e))\n  time.sleep(3)\n time.sleep(3)\nprint('pdftotext',shutil.which('pdftotext'))\nPY", "timeout": 300}</tool_call>
</message>
<message type="tool">2210.07316 saved 769075
2402.14992 saved 5430592
2407.12844 saved 7494081
2405.10938 saved 4369337
2412.06540 saved 4231266
pdftotext None

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking pypdf availability**</reasoning></content>
  <tool_call id="call_e3e3be1c2f8f43e5a353075e52feb722" name="execute">{"command": "python - &lt;&lt;'PY'\nimport importlib.util\nfor x in ['pypdf','PyPDF2','fitz','pdfplumber','bs4']:\n print(x,bool(importlib.util.find_spec(x)))\nPY", "timeout": 20}</tool_call>
</message>
<message type="tool">pypdf False
PyPDF2 False
fitz False
pdfplumber False
bs4 False

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking for PDF tools**</reasoning></content>
  <tool_call id="call_469e79727fb4486e8dc7e63a9088b31b" name="execute">{"command": "python - &lt;&lt;'PY'\nimport os,sys,shutil\nprint('python',sys.executable)\nfor x in ['pdftotext','mutool','gs','pdfinfo','node','pip','uv','pdflatex','latex','tesseract']:\n print(x,shutil.which(x))\nfor p in ['/opt','/usr/local/lib','/usr/local/bin','/root/.cache','/home/evosci/.cache']:\n try: print(p,os.listdir(p)[:60])\n except OSError as e: print(e)\nPY", "timeout": 20}</tool_call>
</message>
<message type="tool">Command blocked: contains absolute system path '/opt'. All file operations must use relative paths within the workspace. Use relative paths (e.g., './file.py') instead.
[Command failed with exit code 1]</message>
<message type="ai">
  <content><reasoning>**Checking PDF access**</reasoning></content>
  <tool_call id="call_ac62ed12a60a4bb4807eac16c86dcf24" name="ls">{"path": "/work/literature"}</tool_call>
</message>
<message type="tool">['/literature/2210.07316.pdf', '/literature/2402.14992.pdf', '/literature/2405.10938.pdf', '/literature/2407.12844.pdf', '/literature/2412.06540.pdf', '/literature/access_log.md']</message>

