## Summarized at 2026-11-02T18:06:18.267702+00:00

<message type="human">Research only, do not implement experiment code. Workspace /work. User mandates independent research on conformal uncertainty for compositions, and forbids an unidentified existing paper AND ALL pages citing/discussing it. To avoid accidental access, NO topical search, no citation graph, no recommendation pages. Only fetch exact starter PDFs https://arxiv.org/pdf/2107.07511 (Angelopoulos Bates tutorial), https://arxiv.org/pdf/1904.06019 (Tibshirani et al covariate shift), https://arxiv.org/pdf/2009.14193 (Romano et al classifier uncertainty), https://arxiv.org/pdf/2402.10723 (Conformalized Credal Set Predictors) if desired. These are explicitly allowed. Read papers directly, summarize target distinction discrete label vs observed composition vs latent conditional probability, split quantile, Mondrian/group calibration, weighted shift, and scope limits. Save PDFs under /work/literature and read notes /work/literature_notes.md; include exact pages/equations consulted and correct BibTeX. Additionally obtain latest official ICLR template via exact official repo https://github.com/ICLR/Master-Template (raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027_conference.sty or inspect repo API), or NeurIPS 2026 official template if ICLR latest unavailable; do NOT use broad search. Download official style and template, document latest year, official URL and page limit from official instructions only to /work/template_provenance.md. Other agents handle code. Return concise findings + files + compliance log. If any forbidden content accidentally encountered STOP reading that page and record URL and amount read. Need actual readable PDFs not fabricated summaries.</message>
<message type="ai">
  <tool_call id="call_793a9683b6b64fb99bd4ee2a0bb017c8" name="search_observations">{"limit": 3, "memory_type": null, "mode": "ranked", "query": "restricted exact URL paper PDF research conformal compositions official ICLR template", "scope": null}</tool_call>
</message>
<message type="tool">{"results": []}</message>
<message type="ai">
  <tool_call id="call_491c9f6c5fce494b92a3df7e49c962b0" name="think_tool">{"reflection": "No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit."}</tool_call>
</message>
<message type="tool">Reflection recorded: No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit.</message>
<message type="ai">
  <content>No relevant prior memory was found. I’ll fetch only the four allowed PDFs and official ICLR template resources—no topical searches, citation graphs, or recommendation pages—and record page-level evidence and access provenance.</content>
  <tool_call id="call_09c5911ac475422797357163853a2b68" name="write_todos">{"todos": [{"content": "Download allowed PDFs and inspect direct-reading guidance and workspace.", "status": "in_progress"}, {"content": "Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.", "status": "pending"}, {"content": "Verify and download latest available official template; document provenance and official page-limit evidence.", "status": "pending"}, {"content": "Audit artifacts and report concise findings plus access-compliance log.", "status": "pending"}]}</tool_call>
</message>
<message type="tool">Updated todo list to [{'content': 'Download allowed PDFs and inspect direct-reading guidance and workspace.', 'status': 'in_progress'}, {'content': 'Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.', 'status': 'pending'}, {'content': 'Verify and download latest available official template; document provenance and official page-limit evidence.', 'status': 'pending'}, {'content': 'Audit artifacts and report concise findings plus access-compliance log.', 'status': 'pending'}]</message>
<message type="ai">
  <tool_call id="call_e9fffcf55c164eeeab43a9d61afb341a" name="ls">{}</tool_call>
  <tool_call id="call_1c20d3175c2a49efb50cd10338db4930" name="ls">{}</tool_call>
</message>
<message type="tool">Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.</message>
<message type="ai">
  <tool_call id="call_ae6c2487b3c34554a682b877fe90b431" name="ls">{}</tool_call>
  <tool_call id="call_9cbe720f26bd4284aa0c6ecb6deb152a" name="ls">{}</tool_call>
</message>
<message type="tool">Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.</message>
<message type="ai">
  <tool_call id="call_1cbb6d81379a430da39099250d0dd123" name="ls">{"path": "/work"}</tool_call>
</message>
<message type="tool">['/.langgraph_api/']</message>
<message type="ai">
  <tool_call id="call_4a2d2382f91540aa96b5ccc0645daa62" name="ls">{"path": "/skills/paper-navigator"}</tool_call>
</message>
<message type="tool">['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']</message>
<message type="ai">
  <tool_call id="call_96b4712d994842d0b5ac184f4f890eef" name="read_file">{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}</tool_call>
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
  <content><reasoning>**Checking paper identity**</reasoning></content>
  <tool_call id="call_61b44f6105154fcf829f4efcfbdf0bed" name="execute">{"command": "python -c 'import os,sys,importlib.util; print(\"work_exists\",os.path.isdir(\"/work\")); print(\"pymupdf\",bool(importlib.util.find_spec(\"fitz\"))); print(\"requests\",bool(importlib.util.find_spec(\"requests\"))); print(\"cwd\",os.getcwd())'", "timeout": 30}</tool_call>
</message>
<message type="tool">work_exists True
pymupdf False
requests False
cwd /work

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_2e7809663285427587fed2f868c981d9" name="execute">{"command": "python -c 'import os,urllib.request,json,hashlib,datetime,shutil; os.makedirs(\"/work/literature\",exist_ok=True); os.makedirs(\"/work/template\",exist_ok=True); log=[]; ids=[\"2107.07511\",\"1904.06019\",\"2009.14193\",\"2402.10723\"]; urls=[(\"https://arxiv.org/pdf/\"+i,\"/work/literature/\"+i+\".pdf\") for i in ids]+[(\"https://api.github.com/repos/ICLR/Master-Template/contents/\",\"/work/template/repo_contents.json\")]; print(\"pdftotext\",shutil.which(\"pdftotext\")); print(\"pdfinfo\",shutil.which(\"pdfinfo\")); [(None) for _ in []];\nfor url,path in urls:\n try:\n  req=urllib.request.Request(url,headers={\"User-Agent\":\"ResearchAssistant-primary-source-download/1.0\"}); response=urllib.request.urlopen(req,timeout=90); data=response.read(); open(path,\"wb\").write(data); entry={\"requested_url\":url,\"final_url\":response.url,\"status\":response.status,\"bytes\":len(data),\"sha256\":hashlib.sha256(data).hexdigest(),\"path\":path,\"utc\":datetime.datetime.now(datetime.timezone.utc).isoformat()}; log.append(entry); print(json.dumps(entry))\n except Exception as e:\n  entry={\"requested_url\":url,\"error\":str(e)}; log.append(entry); print(json.dumps(entry))\nopen(\"/work/access_log.json\",\"w\").write(json.dumps(log,indent=2))'", "timeout": 300}</tool_call>
</message>
<message type="tool">pdftotext None
pdfinfo None
{"requested_url": "https://arxiv.org/pdf/2107.07511", "final_url": "https://arxiv.org/pdf/2107.07511", "status": 200, "bytes": 5360733, "sha256": "c69aa191d8363c25b36685db4adb7e6980e55ee39892fd3626206c16e1e0efa1", "path": "./literature/2107.07511.pdf", "utc": "2026-11-02T18:05:39.099243+00:00"}
{"requested_url": "https://arxiv.org/pdf/1904.06019", "final_url": "https://arxiv.org/pdf/1904.06019", "status": 200, "bytes": 423685, "sha256": "d80dba944a136e075bbfe281009152ce42041e0a455f68f73684ace83cfc3fed", "path": "./literature/1904.06019.pdf", "utc": "2026-11-02T18:05:39.590307+00:00"}
{"requested_url": "https://arxiv.org/pdf/2009.14193", "final_url": "https://arxiv.org/pdf/2009.14193", "status": 200, "bytes": 1339455, "sha256": "ca78c0ab20b95151db93e75f0fed5ef88faf180023b80d36c9e671034bc43f85", "path": "./literature/2009.14193.pdf", "utc": "2026-11-02T18:05:40.183158+00:00"}
{"requested_url": "https://arxiv.org/pdf/2402.10723", "final_url": "https://arxiv.org/pdf/2402.10723", "status": 200, "bytes": 1756530, "sha256": "ac4a42679abdeaff5cfbe6bb316ac60373dfd9eefc97afc9ce94eb4899c68d09", "path": "./literature/2402.10723.pdf", "utc": "2026-11-02T18:05:40.831276+00:00"}
{"requested_url": "https://api.github.com/repos/ICLR/Master-Template/contents/", "final_url": "https://api.github.com/repos/ICLR/Master-Template/contents/", "status": 200, "bytes": 16961, "sha256": "dc54ed42f6d93f1f1debb1d044bf45a48b2e65cbc310f914f683f3b443061f07", "path": "./template/repo_contents.json", "utc": "2026-11-02T18:05:41.442059+00:00"}

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Listing files**</reasoning></content>
  <tool_call id="call_ead7000ee4654b1c8c72f8e48846f97d" name="ls">{"path": "/work/literature"}</tool_call>
</message>
<message type="tool">['/literature/1904.06019.pdf', '/literature/2009.14193.pdf', '/literature/2107.07511.pdf', '/literature/2402.10723.pdf']</message>
<message type="ai">
  <tool_call id="call_a10c0b96b40842b88e0075f048f154e5" name="read_file">{"file_path": "/work/literature/2009.14193.pdf", "limit": 100, "offset": 0}</tool_call>
</message>
<message type="tool">&lt;file url="/conversation_history/media/ca78c0ab20b95151.pdf" /&gt;</message>
<message type="ai">
  <content><reasoning>**Checking PDF support**</reasoning></content>
  <tool_call id="call_LydFdMvJkec3axfsitLzKOyI" name="execute">{"command": "python -c 'import importlib.util,json; print({x:bool(importlib.util.find_spec(x)) for x in [\"pypdf\",\"PyPDF2\",\"pdfplumber\",\"pymupdf\"]}); d=json.load(open(\"/work/template/repo_contents.json\")); print(json.dumps([{k:e.get(k) for k in [\"name\",\"type\",\"download_url\",\"sha\"]} for e in d],indent=2))'", "timeout": 30}</tool_call>
</message>
<message type="tool">{'pypdf': False, 'PyPDF2': False, 'pdfplumber': False, 'pymupdf': False}
[
  {
    "name": ".gitignore",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/.gitignore",
    "sha": "e6598ba17279ba13dd91095e2699c30ebf2a570d"
  },
  {
    "name": "README.md",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md",
    "sha": "ab02c8cea890668baaa2b0cc171d06667b53d7a3"
  },
  {
    "name": "archive",
    "type": "dir",
    "download_url": null,
    "sha": "2eb0d9ff6824fd5e10e25a2e5537c1405472538d"
  },
  {
    "name": "fancyhdr.sty",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/fancyhdr.sty",
    "sha": "5a4d89785c30c5975836ec62902212e41d105339"
  },
  {
    "name": "iclr2019_conference.bib",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2019_conference.bib",
    "sha": "dbc773bf20f6a5e04306a5f7c8c4c759abf44baf"
  },
  {
    "name": "iclr2019_conference.bst",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2019_conference.bst",
    "sha": "149a48c5be151e84bc9f0f4ecb1381875e71573e"
  },
  {
    "name": "iclr2019_conference.pdf",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2019_conference.pdf",
    "sha": "cde15d34d763810c5554af67e47aa8349455259f"
  },
  {
    "name": "iclr2019_conference.sty",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2019_conference.sty",
    "sha": "9f6cc1656e629328ab26db9604551de24e193a08"
  },
  {
    "name": "iclr2019_conference.tex",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2019_conference.tex",
    "sha": "4dba00c47a60348acd094062682c7e92e2de273f"
  },
  {
    "name": "iclr2020",
    "type": "dir",
    "download_url": null,
    "sha": "6e59de0f7510a7681e703412111fc730db203142"
  },
  {
    "name": "iclr2021",
    "type": "dir",
    "download_url": null,
    "sha": "96668e145d072394b8cc496c4121b4f81fdc5e0d"
  },
  {
    "name": "iclr2022.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2022.zip",
    "sha": "921bdd8e2159aad35384d4638109b1830217d68d"
  },
  {
    "name": "iclr2023.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2023.zip",
    "sha": "f83f190b0e4a6b198b05f322a2a8253936b623f6"
  },
  {
    "name": "iclr2024.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2024.zip",
    "sha": "a3878e1295f476229908cbb6a4ae883528d20850"
  },
  {
    "name": "iclr2025.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2025.zip",
    "sha": "c7b2fc046127c72b4372cea6cd7c425d16f7124c"
  },
  {
    "name": "iclr2025",
    "type": "dir",
    "download_url": null,
    "sha": "a711ddaefd51b108fe6209eccb5f9c4ec8808b26"
  },
  {
    "name": "iclr2026.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026.zip",
    "sha": "868f74ea316b901f30ed8bfaaba59ad82c3ada12"
  },
  {
    "name": "iclr2026",
    "type": "dir",
    "download_url": null,
    "sha": "fd03065ec4e8df2ffcc63a0d1b820b420a23e26d"
  },
  {
    "name": "iclr2027.zip",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip",
    "sha": "a079db54799d53378169a6e2c4f2105371522181"
  },
  {
    "name": "iclr2027",
    "type": "dir",
    "download_url": null,
    "sha": "413badc001888f7d3277699d80e64f6c8fb38781"
  },
  {
    "name": "math_commands.tex",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/math_commands.tex",
    "sha": "0668f931945175ca8535db25cc27fa603920cc3c"
  },
  {
    "name": "natbib.sty",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/natbib.sty",
    "sha": "ff0d0b91b6ef41468c593a0ca40a81f9a183b055"
  }
]

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_IeDHEYntB49suqRBAWtsnqmO" name="read_file">{"file_path": "/work/literature/1904.06019.pdf", "limit": 100, "offset": 0}</tool_call>
</message>
<message type="tool">&lt;file url="/conversation_history/media/d80dba944a136e07.pdf" /&gt;</message>

## Summarized at 2026-11-02T18:25:54.980012+00:00

<message type="ai">
  <tool_call id="call_kKKW6xLj0UgjRPS5w9XXto9T" name="read_file">{"file_path": "/work/literature/2402.10723.pdf", "limit": 100, "offset": 0}</tool_call>
</message>
<message type="tool">&lt;file url="/conversation_history/media/ac4a42679abdeaff.pdf" /&gt;</message>
<message type="ai">
  <content><reasoning>**Recovering exact user history**</reasoning> The earlier memory preflight found no relevant observations. I’m continuing with only the explicitly allowed PDFs and official ICLR repository, without topical or citation searches. Direct PDF reading is now working.</content>
  <tool_call id="call_oBRSnYV47J3KlRvCInxNlNha" name="ls">{"path": "/conversation_history"}</tool_call>
  <tool_call id="call_VniSL8GBIhure3EH4U254Ato" name="ls">{"path": "/work"}</tool_call>
  <tool_call id="call_s214gVIMhK88NQQQIXFS0oOB" name="ls">{"path": "/skills/paper-navigator"}</tool_call>
</message>
<message type="tool">['/conversation_history/media/', '/conversation_history/session_a5f648ccde4d4e72a7ccbf5b28ccfcb8.md']</message>
<message type="tool">['/.langgraph_api/', '/access_log.json', '/conversation_history/', '/literature/', '/template/']</message>
<message type="tool">['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']</message>
<message type="ai">
  <tool_call id="call_CgFjTsgCtXx2zOdqHGPPTBFr" name="read_file">{"file_path": "/conversation_history/session_a5f648ccde4d4e72a7ccbf5b28ccfcb8.md", "limit": 220, "offset": 0}</tool_call>
  <tool_call id="call_g1hy0TlnOn2s4KtaJnPZRk88" name="read_file">{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}</tool_call>
  <tool_call id="call_RYgPmz5rai27yJKhiEnO0Qzi" name="read_file">{"file_path": "/work/access_log.json", "limit": 200, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-220 of 604 | next offset 220 @@
## Summarized at 2026-11-02T18:06:18.267702+00:00

&lt;message type="human"&gt;Research only, do not implement experiment code. Workspace /work. User mandates independent research on conformal uncertainty for compositions, and forbids an unidentified existing paper AND ALL pages citing/discussing it. To avoid accidental access, NO topical search, no citation graph, no recommendation pages. Only fetch exact starter PDFs https://arxiv.org/pdf/2107.07511 (Angelopoulos Bates tutorial), https://arxiv.org/pdf/1904.06019 (Tibshirani et al covariate shift), https://arxiv.org/pdf/2009.14193 (Romano et al classifier uncertainty), https://arxiv.org/pdf/2402.10723 (Conformalized Credal Set Predictors) if desired. These are explicitly allowed. Read papers directly, summarize target distinction discrete label vs observed composition vs latent conditional probability, split quantile, Mondrian/group calibration, weighted shift, and scope limits. Save PDFs under /work/literature and read notes /work/literature_notes.md; include exact pages/equations consulted and correct BibTeX. Additionally obtain latest official ICLR template via exact official repo https://github.com/ICLR/Master-Template (raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027_conference.sty or inspect repo API), or NeurIPS 2026 official template if ICLR latest unavailable; do NOT use broad search. Download official style and template, document latest year, official URL and page limit from official instructions only to /work/template_provenance.md. Other agents handle code. Return concise findings + files + compliance log. If any forbidden content accidentally encountered STOP reading that page and record URL and amount read. Need actual readable PDFs not fabricated summaries.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_793a9683b6b64fb99bd4ee2a0bb017c8" name="search_observations"&gt;{"limit": 3, "memory_type": null, "mode": "ranked", "query": "restricted exact URL paper PDF research conformal compositions official ICLR template", "scope": null}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;{"results": []}&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_491c9f6c5fce494b92a3df7e49c962b0" name="think_tool"&gt;{"reflection": "No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit."}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Reflection recorded: No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;content&gt;No relevant prior memory was found. I’ll fetch only the four allowed PDFs and official ICLR template resources—no topical searches, citation graphs, or recommendation pages—and record page-level evidence and access provenance.&lt;/content&gt;
  &lt;tool_call id="call_09c5911ac475422797357163853a2b68" name="write_todos"&gt;{"todos": [{"content": "Download allowed PDFs and inspect direct-reading guidance and workspace.", "status": "in_progress"}, {"content": "Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.", "status": "pending"}, {"content": "Verify and download latest available official template; document provenance and official page-limit evidence.", "status": "pending"}, {"content": "Audit artifacts and report concise findings plus access-compliance log.", "status": "pending"}]}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Updated todo list to [{'content': 'Download allowed PDFs and inspect direct-reading guidance and workspace.', 'status': 'in_progress'}, {'content': 'Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.', 'status': 'pending'}, {'content': 'Verify and download latest available official template; document provenance and official page-limit evidence.', 'status': 'pending'}, {'content': 'Audit artifacts and report concise findings plus access-compliance log.', 'status': 'pending'}]&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_e9fffcf55c164eeeab43a9d61afb341a" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_1c20d3175c2a49efb50cd10338db4930" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_ae6c2487b3c34554a682b877fe90b431" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_9cbe720f26bd4284aa0c6ecb6deb152a" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_1cbb6d81379a430da39099250d0dd123" name="ls"&gt;{"path": "/work"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/.langgraph_api/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_4a2d2382f91540aa96b5ccc0645daa62" name="ls"&gt;{"path": "/skills/paper-navigator"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_96b4712d994842d0b5ac184f4f890eef" name="read_file"&gt;{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;@@ lines 1-379 of 379 @@
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

Script paths in this document are relative to this skill's directory. Run via `python scripts/&amp;lt;name&amp;gt;.py`.

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
| URL | `python scripts/fetch_paper.py --url &amp;lt;URL&amp;gt;` | Paper Card + reading notes (see `references/reading-strategy.md` for L1/L2/L3) |
| Title quoted | `python scripts/match_paper_by_title.py --title "&amp;lt;title&amp;gt;"` (add `--fallback-search` for typos) | Paper Card |
| Bare ID (arXiv / DOI / S2 / CorpusId) | `python scripts/fetch_paper.py --paper-id &amp;lt;ID&amp;gt; --metadata-only` | Paper Card |

**Paper Card:**

```
📄 **&amp;lt;Title&amp;gt;**
Authors: &amp;lt;First Author&amp;gt; et al. | Year: &amp;lt;Y&amp;gt; | Venue: &amp;lt;V&amp;gt;
Citations: &amp;lt;N&amp;gt; | ID: &amp;lt;ArXiv:xxxx.xxxxx&amp;gt; | DOI: &amp;lt;...&amp;gt;
TLDR: &amp;lt;one sentence&amp;gt;
```

Stop here. Do not chain to citation expansion unless asked.

---

## LIST / ITERATIVE branch — 6 steps

### Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch. When the user gives only a bare noun (concept / model / algorithm / benchmark name) with no direction, default intent is "trace the lineage" — foundations, evolution, current state — not applications or a generic `survey`.

### Step 2: Author the RUBRIC (via `think_tool`)

Emit a structured block before any search. It persists across rounds and every later step references it.

```
RUBRIC for "&amp;lt;user query verbatim&amp;gt;"
Branch: LIST | ITERATIVE
Criteria (2–4, atomic; mark each [core] or [secondary]):
  C1 [core]     &amp;lt;what the paper MUST do/be — one sentence&amp;gt;
  C2 [core]     &amp;lt;...&amp;gt;
  C3 [secondary] &amp;lt;...&amp;gt;
Named entities to preserve verbatim: [&amp;lt;ent1&amp;gt;, &amp;lt;ent2&amp;gt;, ...]
Angle tags (3–5 sub-topic axes): [&amp;lt;tag1&amp;gt;, &amp;lt;tag2&amp;gt;, &amp;lt;tag3&amp;gt;]
Recency signal: [none | recency cue — defined in Step 3]
Disqualifiers: [&amp;lt;auto-reject if abstract shows this&amp;gt;]
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
python scripts/scholar_search.py --query "&amp;lt;Q-broad&amp;gt;"  --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
python scripts/scholar_search.py --query "&amp;lt;Q-narrow&amp;gt;" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
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
- 3–6 words preferred (English academic terms); &amp;lt;3 over-recalls, &amp;gt;6 dilutes ranking.
- Use academic terms (`mechanism`, `benchmark`); no `how it works` phrasing.
- **Do NOT add `survey` / `review` / `tutorial` terms** — they bias results toward review papers and crowd out the research papers the user wants. Only use them when the user explicitly asks for a survey/review.
- Bare entity names; no `paper` / `pdf` / `arxiv` / `original`.
- Split comparisons / multi-property; if short of 2–3 queries, fill with upper-topic or representative method.
- Time intent goes into `--year-min/max` params, never year words in the query.
- Forbidden: `"…"`, `(..)`, `OR`, `AND`, `|`, `site:`, `filetype:`.
- No two queries in one round may share &amp;gt;60% of content tokens (after stop-words).

**Recency trigger (query layer).** When the user query contains a recency signal (最新 / 近年 / 近期 / 近两年 / 前沿 / SOTA / latest / recent / state-of-the-art), set `--year-min` to **last 2 years** from R2 onward — Jan 1 of the year before the current system year (e.g. system date 2026-08 → `--year-min 2025`). Do not extend to 3–4 years.</message>
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
<message type="tool">@@ lines 1-47 of 47 @@
[
  {
    "requested_url": "https://arxiv.org/pdf/2107.07511",
    "final_url": "https://arxiv.org/pdf/2107.07511",
    "status": 200,
    "bytes": 5360733,
    "sha256": "c69aa191d8363c25b36685db4adb7e6980e55ee39892fd3626206c16e1e0efa1",
    "path": "./literature/2107.07511.pdf",
    "utc": "2026-11-02T18:05:39.099243+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/1904.06019",
    "final_url": "https://arxiv.org/pdf/1904.06019",
    "status": 200,
    "bytes": 423685,
    "sha256": "d80dba944a136e075bbfe281009152ce42041e0a455f68f73684ace83cfc3fed",
    "path": "./literature/1904.06019.pdf",
    "utc": "2026-11-02T18:05:39.590307+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2009.14193",
    "final_url": "https://arxiv.org/pdf/2009.14193",
    "status": 200,
    "bytes": 1339455,
    "sha256": "ca78c0ab20b95151db93e75f0fed5ef88faf180023b80d36c9e671034bc43f85",
    "path": "./literature/2009.14193.pdf",
    "utc": "2026-11-02T18:05:40.183158+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2402.10723",
    "final_url": "https://arxiv.org/pdf/2402.10723",
    "status": 200,
    "bytes": 1756530,
    "sha256": "ac4a42679abdeaff5cfbe6bb316ac60373dfd9eefc97afc9ce94eb4899c68d09",
    "path": "./literature/2402.10723.pdf",
    "utc": "2026-11-02T18:05:40.831276+00:00"
  },
  {
    "requested_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "final_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "status": 200,
    "bytes": 16961,
    "sha256": "dc54ed42f6d93f1f1debb1d044bf45a48b2e65cbc310f914f683f3b443061f07",
    "path": "./template/repo_contents.json",
    "utc": "2026-11-02T18:05:41.442059+00:00"
  }
]</message>
<message type="ai">
  <content><reasoning>**Checking PDF text extraction**</reasoning></content>
  <tool_call id="call_f06a2b9709cf49778851adee7b58249f" name="execute">{"command": "pwd; python -c 'import sys,importlib.util,shutil,os; print(sys.executable); print({x:bool(importlib.util.find_spec(x)) for x in [\"pip\",\"pypdf\",\"fitz\"]}); print({x:shutil.which(x) for x in [\"pdftotext\",\"mutool\",\"gs\"]}); print(os.path.exists(\"/work/literature/2107.07511.pdf\"))'", "timeout": 30}</tool_call>
</message>
<message type="tool">/work
/opt/research/bin/python
{'pip': True, 'pypdf': False, 'fitz': False}
{'pdftotext': None, 'mutool': None, 'gs': None}
True

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_6a8ad23e5cb74885a39b31d4f4e0d4fa" name="execute">{"command": "python -m pip install pypdf --disable-pip-version-check", "timeout": 120}</tool_call>
</message>
<message type="tool">Collecting pypdf
  Downloading pypdf-6.21.4-py3-none-any.whl.metadata (7.6 kB)
Downloading pypdf-6.21.4-py3-none-any.whl (410 kB)
Installing collected packages: pypdf
Successfully installed pypdf-6.21.4

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_a677492bb8454abea84c8e9a1685af74" name="write_todos">{"todos": [{"content": "Download allowed PDFs and inspect direct-reading guidance and workspace.", "status": "completed"}, {"content": "Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.", "status": "in_progress"}, {"content": "Verify and download latest available official template; document provenance and official page-limit evidence.", "status": "pending"}, {"content": "Audit artifacts and report concise findings plus access-compliance log.", "status": "pending"}]}</tool_call>
</message>
<message type="tool">Updated todo list to [{'content': 'Download allowed PDFs and inspect direct-reading guidance and workspace.', 'status': 'completed'}, {'content': 'Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.', 'status': 'in_progress'}, {'content': 'Verify and download latest available official template; document provenance and official page-limit evidence.', 'status': 'pending'}, {'content': 'Audit artifacts and report concise findings plus access-compliance log.', 'status': 'pending'}]</message>
<message type="ai">
  <tool_call id="call_d1bcf7a4a8d3408bbbbff0ea5ab71f66" name="execute">{"command": "python -c 'from pypdf import PdfReader; from pathlib import Path; ids=[\"2107.07511\",\"1904.06019\",\"2009.14193\",\"2402.10723\"]; [(print(i,\"pages\",len(r.pages),\"metadata\",r.metadata),Path(\"/work/literature/\"+i+\".txt\").write_text(\"\\n\\n\".join(\"=== PDF PAGE \"+str(n+1)+\" ===\\n\"+p.extract_text() for n,p in enumerate(r.pages)))) for i in ids for r in [PdfReader(\"/work/literature/\"+i+\".pdf\")]]'", "timeout": 120}</tool_call>
</message>
<message type="tool">2107.07511 pages 51 metadata {'/Author': '', '/CreationDate': 'D:20221208011258Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20221208011258Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) kpathsea version 6.3.2', '/Producer': 'pdfTeX-1.40.21', '/Subject': '', '/Title': '', '/Trapped': '/False'}
1904.06019 pages 17 metadata {'/Author': '', '/CreationDate': 'D:20200708002641Z', '/Creator': 'LaTeX with hyperref package', '/Keywords': '', '/ModDate': 'D:20200708002641Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.17 (TeX Live 2016) kpathsea version 6.2.2', '/Producer': 'pdfTeX-1.40.17', '/Subject': '', '/Title': '', '/Trapped': '/False'}
2009.14193 pages 18 metadata {'/Author': '', '/CreationDate': 'D:20220907011307Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20220907011307Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) kpathsea version 6.3.2', '/Producer': 'pdfTeX-1.40.21', '/Subject': '', '/Title': '', '/Trapped': '/False'}
2402.10723 pages 16 metadata {'/Author': '', '/CreationDate': 'D:20240219015235Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20240219015235Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.141592653-2.6-1.40.25 (TeX Live 2023) kpathsea version 6.3.5', '/Producer': 'pdfTeX-1.40.25', '/Subject': '', '/Title': '', '/Trapped': '/False'}

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_0405c608151a45e99720849dc92c97a1" name="read_file">{"file_path": "/conversation_history/session_a5f648ccde4d4e72a7ccbf5b28ccfcb8.md", "limit": 130, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-130 of 604 | next offset 130 @@
## Summarized at 2026-11-02T18:06:18.267702+00:00

&lt;message type="human"&gt;Research only, do not implement experiment code. Workspace /work. User mandates independent research on conformal uncertainty for compositions, and forbids an unidentified existing paper AND ALL pages citing/discussing it. To avoid accidental access, NO topical search, no citation graph, no recommendation pages. Only fetch exact starter PDFs https://arxiv.org/pdf/2107.07511 (Angelopoulos Bates tutorial), https://arxiv.org/pdf/1904.06019 (Tibshirani et al covariate shift), https://arxiv.org/pdf/2009.14193 (Romano et al classifier uncertainty), https://arxiv.org/pdf/2402.10723 (Conformalized Credal Set Predictors) if desired. These are explicitly allowed. Read papers directly, summarize target distinction discrete label vs observed composition vs latent conditional probability, split quantile, Mondrian/group calibration, weighted shift, and scope limits. Save PDFs under /work/literature and read notes /work/literature_notes.md; include exact pages/equations consulted and correct BibTeX. Additionally obtain latest official ICLR template via exact official repo https://github.com/ICLR/Master-Template (raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027_conference.sty or inspect repo API), or NeurIPS 2026 official template if ICLR latest unavailable; do NOT use broad search. Download official style and template, document latest year, official URL and page limit from official instructions only to /work/template_provenance.md. Other agents handle code. Return concise findings + files + compliance log. If any forbidden content accidentally encountered STOP reading that page and record URL and amount read. Need actual readable PDFs not fabricated summaries.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_793a9683b6b64fb99bd4ee2a0bb017c8" name="search_observations"&gt;{"limit": 3, "memory_type": null, "mode": "ranked", "query": "restricted exact URL paper PDF research conformal compositions official ICLR template", "scope": null}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;{"results": []}&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_491c9f6c5fce494b92a3df7e49c962b0" name="think_tool"&gt;{"reflection": "No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit."}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Reflection recorded: No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;content&gt;No relevant prior memory was found. I’ll fetch only the four allowed PDFs and official ICLR template resources—no topical searches, citation graphs, or recommendation pages—and record page-level evidence and access provenance.&lt;/content&gt;
  &lt;tool_call id="call_09c5911ac475422797357163853a2b68" name="write_todos"&gt;{"todos": [{"content": "Download allowed PDFs and inspect direct-reading guidance and workspace.", "status": "in_progress"}, {"content": "Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.", "status": "pending"}, {"content": "Verify and download latest available official template; document provenance and official page-limit evidence.", "status": "pending"}, {"content": "Audit artifacts and report concise findings plus access-compliance log.", "status": "pending"}]}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Updated todo list to [{'content': 'Download allowed PDFs and inspect direct-reading guidance and workspace.', 'status': 'in_progress'}, {'content': 'Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.', 'status': 'pending'}, {'content': 'Verify and download latest available official template; document provenance and official page-limit evidence.', 'status': 'pending'}, {'content': 'Audit artifacts and report concise findings plus access-compliance log.', 'status': 'pending'}]&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_e9fffcf55c164eeeab43a9d61afb341a" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_1c20d3175c2a49efb50cd10338db4930" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_ae6c2487b3c34554a682b877fe90b431" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_9cbe720f26bd4284aa0c6ecb6deb152a" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_1cbb6d81379a430da39099250d0dd123" name="ls"&gt;{"path": "/work"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/.langgraph_api/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_4a2d2382f91540aa96b5ccc0645daa62" name="ls"&gt;{"path": "/skills/paper-navigator"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_96b4712d994842d0b5ac184f4f890eef" name="read_file"&gt;{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;@@ lines 1-379 of 379 @@
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

Script paths in this document are relative to this skill's directory. Run via `python scripts/&amp;lt;name&amp;gt;.py`.

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
| URL | `python scripts/fetch_paper.py --url &amp;lt;URL&amp;gt;` | Paper Card + reading notes (see `references/reading-strategy.md` for L1/L2/L3) |
| Title quoted | `python scripts/match_paper_by_title.py --title "&amp;lt;title&amp;gt;"` (add `--fallback-search` for typos) | Paper Card |
| Bare ID (arXiv / DOI / S2 / CorpusId) | `python scripts/fetch_paper.py --paper-id &amp;lt;ID&amp;gt; --metadata-only` | Paper Card |
</message>
<message type="ai">
  <tool_call id="call_a757ad4133624f45b4a4a29718314c62" name="read_file">{}</tool_call>
  <tool_call id="call_4f2449ecb3b74244a7b30464b330cab6" name="read_file">{}</tool_call>
  <tool_call id="call_7b05ddf207774269ab7695b895345e50" name="read_file">{}</tool_call>
  <tool_call id="call_d0ebc10d90094664a00f1a73af56802b" name="read_file">{}</tool_call>
</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="ai">
  <tool_call id="call_c508032a40b54243a4bffafce3dd2914" name="read_file">{"file_path": "/work/literature/2107.07511.txt", "limit": 260, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-260 of 2462 | next offset 260 @@
=== PDF PAGE 1 ===
A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantiﬁcation
Anastasios N. Angelopoulos and Stephen Bates
December 8, 2022
Abstract
Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-
tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-
tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty
sets/intervals for the predictions of such models. Critically, the sets are valid in a distribution-free sense:
they possess explicit, non-asymptotic guarantees even without distributional assumptions or model as-
sumptions. One can use conformal prediction with any pre-trained model, such as a neural network, to
produce sets that are guaranteed to contain the ground truth with a user-speciﬁed probability, such as
90%. It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the
ﬁelds of computer vision, natural language processing, deep reinforcement learning, and so on.
This hands-on introduction is aimed to provide the reader a working understanding of conformal
prediction and related distribution-free uncertainty quantiﬁcation techniques with one self-contained
document. We lead the reader through practical theory for and examples of conformal prediction and
describe its extensions to complex machine learning tasks involving structured outputs, distribution
shift, time-series, outliers, models that abstain, and more. Throughout, there are many explanatory
illustrations, examples, and code samples in Python. With each code sample comes a Jupyter notebook
implementing the method on a real-data example; the notebooks can be accessed and easily run by
clicking on the following icons:
 .
1
arXiv:2107.07511v6  [cs.LG]  7 Dec 2022

=== PDF PAGE 2 ===
Contents
1 Conformal Prediction 4
1.1 Instructions for Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 Examples of Conformal Procedures 6
2.1 Classiﬁcation with Adaptive Prediction Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.2 Conformalized Quantile Regression . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.3 Conformalizing Scalar Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.1 The Estimated Standard Deviation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.2 Other 1-D Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.4 Conformalizing Bayes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Evaluating Conformal Prediction 11
3.1 Evaluating Adaptivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 The Eﬀect of the Size of the Calibration Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
3.3 Checking for Correct Coverage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
4 Extensions of Conformal Prediction 16
4.1 Group-Balanced Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Class-Conditional Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Conformal Risk Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Outlier Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
4.5 Conformal Prediction Under Covariate Shift . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
4.6 Conformal Prediction Under Distribution Drift . . . . . . . . . . . . . . . . . . . . . . . . . . 21
5 Worked Examples 23
5.1 Multilabel Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.2 Tumor Segmentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.3 Weather Prediction with Time-Series Distribution Shift . . . . . . . . . . . . . . . . . . . . . 24
5.4 Toxic Online Comment Identiﬁcation via Outlier Detection . . . . . . . . . . . . . . . . . . . 25
5.5 Selective Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
6 Full conformal prediction 27
6.1 Full Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.2 Cross-Conformal Prediction, CV+, and Jackknife+ . . . . . . . . . . . . . . . . . . . . . . . . 28
7 Historical Notes on Conformal Prediction 28
A Distribution-Free Control of General Risks 39
A.1 Instructions for Learn then Test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
2

=== PDF PAGE 3 ===
A.1.1 Crash Course on Generating p-values . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
A.1.2 Crash Course on Familywise-Error Rate Algorithms . . . . . . . . . . . . . . . . . . . 44
B Examples of Distribution-Free Risk Control 45
B.1 Multi-label Classiﬁcation with FDR Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
B.2 Simultaneous Guarantees on OOD Detection and Coverage . . . . . . . . . . . . . . . . . . . 46
C Concentration Properties of the Empirical Coverage 49
D Theorem and Proof: Coverage Property of Conformal Prediction 50
3

=== PDF PAGE 4 ===
Figure 1: Prediction set examples on Imagenet. We show three progressively more diﬃcult examples
of the class fox squirrel and the prediction sets (i.e., C(Xtest)) generated by conformal prediction.
1 Conformal Prediction
Conformal prediction [1–3] (a.k.a. conformal inference) is a straightforward way to generate prediction sets
for any model. We will introduce it with a short, pragmatic image classiﬁcation example, and follow up in
later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows.
First, we begin with a ﬁtted predicted model (such as a neural network classiﬁer) which we will call ˆf. Then,
we will create prediction sets (a set of possible labels) for this classiﬁer using a small amount of additional
calibration data—we will sometimes call this the calibration step.
Formally, suppose we have images as input and they each contain one of K classes. We begin with
a classiﬁer that outputs estimated probabilities (softmax scores) for each class: ˆf(x)∈ [0, 1]K. Then, we
reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training,
(X1,Y 1),..., (Xn,Yn), for use as calibration data. Using ˆf and the calibration data, we seek to construct a
prediction set of possible labels C(Xtest)⊂{ 1,...,K } that is valid in the following sense:
1−α≤ P(Ytest∈C (Xtest))≤ 1−α + 1n + 1, (1)
where (Xtest,Y test) is a fresh test point from the same distribution, and α∈ [0, 1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1 −α; we call
this property marginal coverage, since the probability is marginal (averaged) over the randomness in the
calibration and test points. See Figure 1 for examples of prediction sets on the Imagenet dataset.
To constructC from ˆf and the calibration data, we will perform a simple calibration step that requires
only a few lines of code; see the right panel of Figure 2. We now describe the calibration step in more detail,
introducing some terms that will be helpful later on. First, we set the conformal scoresi = 1− ˆf(Xi)Yi to be
one minus the softmax output of the true class. The score is high when the softmax output of the true class
is low, i.e., when the model is badly wrong. Next comes the critical step: deﬁne ˆq to be the⌈(n+1)(1−α)⌉/n
empirical quantile of s1,...,s n, where⌈·⌉ is the ceiling function (ˆq is essentially the 1−α quantile, but with
a small correction). Finally, for a new test data point (where Xtest is known but Ytest is not), create a
prediction setC(Xtest) ={y : ˆf(Xtest)y≥ 1− ˆq} that includes all classes with a high enough softmax output
(see Figure 2). Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy (1), no matter
what (possibly incorrect) model is used or what the (unknown) distribution of the data is.
true class
class
softmax output
#
scores,       class
softmax output
(1) compute scores
on holdout data
(2) get quantile (3) construct
prediction set
# 1: get conformal scores. n = calib_Y.shape[0]
cal_smx = model(calib_X).softmax(dim=1).numpy()
cal_scores = 1-cal_smx[np.arange(n),cal_labels]
# 2: get adjusted quantile
q_level = np.ceil((n+1)*(1-alpha))/n
qhat = np.quantile(cal_scores, q_level, method='higher')
val_smx = model(val_X).softmax(dim=1).numpy()
prediction_sets = val_smx &gt;= (1-qhat) # 3: form prediction sets
Figure 2: Illustration of conformal prediction with matching Python code.
4

=== PDF PAGE 5 ===
Remarks
Let us think about the interpretation of C. The function C is set-valued—it takes in an image, and it
outputs a set of classes as in Figure 1. The model’s softmax outputs help to generate the set. This method
constructs a diﬀerent output set adaptively to each particular input . The sets become larger when the model
is uncertain or the image is intrinsically hard. This is a property we want, because the size of the set gives you
an indicator of the model’s certainty. Furthermore, C(Xtest) can be interpreted as a set of plausible classes
that the image Xtest could be assigned to. Finally, C is valid, meaning it satisﬁes (1). 1 These properties of
C translate naturally to other machine learning problems, like regression, as we will see.
With an eye towards generalization, let us review in detail what happened in our classiﬁcation problem.
To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the
jth entry of the softmax vector estimated P(Y = j| X = x), the probability of class j conditionally on
an input image x. However, we had no guarantee that the softmax outputs were any good; they may have
been arbitrarily overﬁt or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face
value, we used the holdout set to adjust for their deﬁciencies.
The holdout set contained n≈ 500 fresh data points that the model never saw during training, which
allowed us to get an honest appraisal of its performance. The adjustment involved computing conformal
scores, which grow when the model is uncertain, but are not valid prediction intervals on their own. In our
case, the conformal score was one minus the softmax output of the true class, but in general, the score can
be any function of x and y. We then took ˆq to be roughly the 1−α quantile of the scores. In this case, the
quantile had a simple interpretation—when setting α = 0.1, at least 90% of ground truth softmax outputs
are guaranteed to be above the level 1 − ˆq (we prove this rigorously in Appendix D). Taking advantage of
this fact, at test-time, we got the softmax outputs of a new image Xtest and collected all classes with outputs
above 1− ˆq into a prediction setC(Xtest). Since the softmax output of the new true class Ytest is guaranteed
to be above 1− ˆq with probability at least 90%, we ﬁnally got the guarantee in Eq. (1).
1.1 Instructions for Conformal Prediction
As we said during the summary, conformal prediction is not speciﬁc to softmax outputs or classiﬁcation
problems. In fact, conformal prediction can be seen as a method for taking any heuristic notion of
uncertainty from any model and converting it to a rigorous one (see the diagram below). Conformal pre-
diction does not care if the underlying prediction problem is discrete/continuous or classiﬁcation/regression.
Heuristic
uncertainty
(per input)
Rigorous
uncertainty
(per input)
conformal
prediction
We next outline conformal prediction for a general input x and output y (not necessarily discrete).
1. Identify a heuristic notion of uncertainty using the pre-trained model.
2. Deﬁne the score function s(x,y )∈ R. (Larger scores encode worse agreement between x and y.)
3. Compute ˆq as the ⌈(n+1)(1−α)⌉n quantile of the calibration scores s1 =s(X1,Y 1),...,s n =s(Xn,Yn).
4. Use this quantile to form the prediction sets for new examples:
C(Xtest) ={y :s(Xtest,y )≤ ˆq}. (2)
As before, these sets satisfy the validity property in (1), for any (possibly uninformative) score function and
(possibly unknown) distribution of the data. We formally state the coverage guarantee next.
1Due to the discreteness of Y , a small modiﬁcation involving tie-breaking is needed to additionally satisfy the upper bound
(see [4] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
5

=== PDF PAGE 6 ===
Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [5]). Suppose (Xi,Yi)i=1,...,n
and (Xtest,Y test) are i.i.d. and deﬁne ˆq as in step 3 above andC(Xtest) as in step 4 above. Then the following
holds:
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
See Appendix D for a proof and a statement that includes the upper bound in (1). We note that the
above is only a special case of conformal prediction, called split conformal prediction . This is the most
widely-used version of conformal prediction, and it will be our primary focus. To complete the picture, we
describe conformal prediction in full generality later in Section 6 and give an overview of the literature in
Section 7.
Choice of score function
Upon ﬁrst glance, this seems too good to be true, and a skeptical reader might ask the following question:
How is it possible to construct a statistically valid prediction set even if the heuristic notion of uncertainty
of the underlying model is arbitrarily bad?
Let’s give some intuition to supplement the mathematical understanding from the proof in Appendix D.
Roughly, if the scoressi correctly rank the inputs from lowest to highest magnitude of model error, then the
resulting sets will be smaller for easy inputs and bigger for hard ones. If the scores are bad, in the sense that
they do not approximate this ranking, then the sets will be useless. For example, if the scores are random
noise, then the sets will contain a random sample of the label space, where that random sample is large
enough to provide valid marginal coverage. This illustrates an important underlying fact about conformal
prediction: although the guarantee always holds, the usefulness of the prediction sets is primarily
determined by the score function. This should be no surprise—the score function incorporates almost all
the information we know about our problem and data, including the underlying model itself. For example, the
main diﬀerence between applying conformal prediction on classiﬁcation problems versus regression problems
is the choice of score. There are also many possible score functions for a single underlying model, which have
diﬀerent properties. Therefore, constructing the right score function is an important engineering choice. We
will next show a few examples of good score functions.
2 Examples of Conformal Procedures
In this section we give examples of conformal prediction applied in many settings, with the goal of providing
the reader a bank of techniques to practically deploy. Note that we will focus only on one-dimensional Y in
this section, and smaller conformal scores will correspond to more model conﬁdence (such scores are called
nonconformity scores). Richer settings, such as high-dimensional Y , complicated (or multiple) notions of
error, or where diﬀerent mistakes cost diﬀerent amounts, often require the language of risk control, outlined
in Section A.
2.1 Classiﬁcation with Adaptive Prediction Sets
Let’s begin our sequence of examples with an improvement to the classiﬁcation example in Section 1.
The previous method produces prediction sets with the smallest average size [6], but it tends to undercover
hard subgroups and overcover easy ones. Here we develop a diﬀerent method called adaptive prediction sets
(APS) that avoids this problem. We will follow [7] and [4].
As motivation for this new procedure, note that if the softmax outputs ˆf(Xtest) were a perfect model
of Ytest|Xtest, we would greedily include the top-scoring classes until their total mass just exceeded 1 −α.
6

=== PDF PAGE 7 ===
# Get scores. calib_X.shape[0] == calib_Y.shape[0] == n
cal_pi = cal_smx.argsort(1)[:,::-1]; cal_srt = np.take_along_axis(cal_smx,cal_pi,axis=1).cumsum(axis=1)
cal_scores = np.take_along_axis(cal_srt,cal_pi.argsort(axis=1),axis=1)[range(n),cal_labels]
# Get the score quantile
qhat = np.quantile(cal_scores, np.ceil((n+1)*(1-alpha))/n, interpolation='higher')
# Deploy (output=list of length n, each element is tensor of classes)
val_pi = val_smx.argsort(1)[:,::-1]; val_srt = np.take_along_axis(val_smx,val_pi,axis=1).cumsum(axis=1)
prediction_sets = np.take_along_axis(val_srt &lt;= qhat,val_pi.argsort(axis=1),axis=1)
Figure 3: Python code for adaptive prediction sets.
Formally, we can describe this oracle algorithm as
{π1(x),...,π k(x)} , where k = sup


k′ :
k′∑
j=1
ˆf(Xtest)πj(x) &lt; 1−α


 + 1,
and π(x) is the permutation of {1,...,K} that sorts ˆf(Xtest) from most likely to least likely. In practice,
however, this procedure fails to provide coverage, since ˆf(Xtest) is not perfect; it only provides us a heuristic
notion of uncertainty. Therefore, we will use conformal prediction to turn this into a rigorous notion of
uncertainty.
To proceed, we deﬁne a score function inspired by the oracle algorithm:
s(x,y ) =
k∑
j=1
ˆf(x)πj(x), where y =πk(x).
In other words, we greedily include classes in our set until we reach the true label, then we stop. Unlike the
score from Section 1, this one utilizes the softmax outputs of all classes, not just the true class.
The next step, as in all conformal procedures, is to set ˆ q = Quantile(s1,...,s n ; ⌈(n+1)(1−α)⌉n ). Having
done so, we will form the prediction set {y :s(x,y )≤ ˆq}, modiﬁed slightly to avoid zero-size sets:
C(x) ={π1(x),...,π k(x)} , where k = sup


k′ :</message>
<message type="ai">
  <tool_call id="call_910afb8df58441f5bb8f6e2c827e5b9c" name="read_file">{}</tool_call>
  <tool_call id="call_15afa1b5377941d3841cb9b18aac4d89" name="read_file">{}</tool_call>
  <tool_call id="call_eedfc12c27df44ecb6837b5f11bae694" name="read_file">{}</tool_call>
</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="tool">Error invoking tool 'read_file' with kwargs {} with error:
 file_path: Field required
 Please fix the error and try again.</message>
<message type="ai">
  <content><reasoning>**Clearing arguments directly**</reasoning></content>
  <tool_call id="call_397874860be04a5f82d5fa93f5bdc2f2" name="read_file">{"file_path": "/work/literature/1904.06019.txt", "limit": 320, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-320 of 2190 | next offset 320 @@
=== PDF PAGE 1 ===
Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the training and test data are not drawn from the same distribution.
We begin by reviewing the basics of conformal prediction, in this section. In Section 2, we describe an extension of
conformal prediction to the setting of covariate shift, and give supporting empirical results. In Section 3, we cover the
mathematical details behind our conformal extension. We conclude in Section 4, and discuss several other possible
applications of our new conformal methodology.
1.1 Quantile lemma
Before explaining the basic ideas behind conformal inference (i.e., conformal prediction, we will use these two terms
interchangeably), we introduce some notation. We denote by Quantile(β;F ) the levelβ quantile of a distributionF ,
i.e., forZ∼F ,
Quantile(β;F ) = inf
{
z : P{Z≤z}≥ β
}
.
In our use of quantiles, we will allow for distributionsF on the augmented real line, R∪{∞} . For valuesv1,...,v n,
we writev1:n ={v1,...,v n} to denote their multiset. Note that this is unordered, and allows for multiple instances the
same element; thus in the present case, ifvi =vj fori⁄=j, then this value appears twice inv1:n. To denote quantiles
of the empirical distribution of the valuesv1,...,v n, we abbreviate
Quantile(β;v1:n) = Quantile
(
β; 1n
n∑
i=1
δvi
)
,
1
arXiv:1904.06019v3  [stat.ME]  6 Jul 2020

=== PDF PAGE 2 ===
whereδa denotes a point mass ata (i.e., the distribution that places all mass at the valuea). The next result is a simple
but key component underlying conformal prediction.
Lemma 1. IfV1,...,V n+1 are exchangeable random variables, then for anyβ∈ (0, 1), we have
P
{
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)}
≥β.
Furthermore, if ties betweenV1,...,V n+1 occur with probability zero, then the above probability is upper bound by
β + 1/(n + 1).
Proof. Consider the following useful fact about quantiles of a discrete distributionF , with support pointsa1,...,a k∈
R: denotingq = Quantile(β;F ), if we reassign the pointsai &gt;q to arbitrary values strictly larger thanq, yielding a
new distribution ~F , then the levelβ quantile remains unchanged, Quantile(β;F ) = Quantile(β;~F ). Using this fact,
Vn+1 &gt; Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1 &gt; Quantile
(
β;V1:(n+1)
)
,
or equivalently,
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1≤ Quantile
(
β;V1:(n+1)
)
. (2)
Moreover, it is straightforward to check that
Vn+1≤ Quantile
(
β;V1:(n+1)
)
⇐⇒ Vn+1 is among the⌈β(n + 1)⌉ smallest ofV1,...,V n+1.
By exchangeability, the latter event occurs with probability at least⌈β(n + 1)⌉/(n + 1)≥β, which proves the lower
bound; when there are almost surely no ties, it holds with probability exactly⌈β(n + 1)⌉/(n + 1)≤β + 1/(n + 1),
which proves the upper bound.
1.2 Conformal prediction
We now return to the regression setting. DenoteZi = (Xi,Yi),i = 1,...,n , andZ1:n ={Z1,...,Z n}. We will use
the abbreviationZ−i =Z1:n\{Zi}. In what follows, we describe the construction of a prediction band satisfying (1),
using conformal inference, due to V ovk et al. (2005). We ﬁrst choose a score functionS, whose arguments consist of a
point (x,y ), and a multisetZ.1 Informally, a low value ofS((x,y ),Z ) indicates that the point (x,y ) “conforms” toZ,
whereas a high value indicates that (x,y ) is atypical relative to the points inZ. For example, we might choose to deﬁne
S by
S
(
(x,y ),Z
)
=|y−ˆµ(x)|, (3)
whereˆµ : Rd→ R is a regression function that was ﬁtted by running an algorithmA on (x,y ) andZ.
Next, at eachx∈ Rd, we deﬁne the conformal prediction interval2 ˆCn(x) by repeating the following procedure for
eachy∈ R. We calculate the nonconformity scores
V (x,y)i =S(Zi,Z−i∪{ (x,y )}), i= 1,...,n, and V (x,y)n+1 =S((x,y ),Z 1:n), (4)
and includey in our prediction interval ˆCn(x) if
V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞}),
whereV (x,y)1:n ={V (x,y)1 ,...,V (x,y)n }. Importantly, the symmetry in the construction of the nonconformity scores (4)
guarantees exact coverage in ﬁnite samples. The next theorem summarizes this coverage result. The lower bound is a
standard result in conformal inference, due to V ovk et al. (2005); the upper bound, as far as we know, was ﬁrst pointed
out by Lei et al. (2018).
1We emphasize that by deﬁningZ to be a multiset, we are treating its points as unordered. Hence, to be perfectly explicit, the score function S
cannot accept the points inZ in any particular order, and it must take them in as unordered. The same is true of the base algorithm A used to deﬁne
the ﬁtted regression function ˆµ, in the choice of absolute residual score function (3).
2For convenience, throughout, we will refer to ˆCn(x) as an “interval”, even though this may actually be a union of multiple nonoverlapping
intervals. Similarly, for simplicity, we will refer to ˆCn as a “band”.
2

=== PDF PAGE 3 ===
Theorem 1 (V ovk et al. 2005; Lei et al. 2018). Assume that (Xi,Yi)∈ Rd× R,i = 1,...,n + 1 are exchangeable.
For any score functionS, and anyα∈ (0, 1), deﬁne the conformal band (based on the ﬁrstn samples) atx∈ Rd by
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞})}, (5)
whereV (x,y)i ,i = 1,...,n + 1 are as deﬁned in (4). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Furthermore, if ties betweenV (Xn+1,Yn+1)1 ,...,V (Xn+1,Yn+1)n+1 occur with probability zero, then this probability is upper
bounded by 1−α + 1/(n + 1).
Proof. To lighten notation, abbreviateVi =V (Xn+1,Yn+1)i ,i = 1,...,n + 1. Observe
Yn+1∈ ˆCn(Xn+1) ⇐⇒ Vn+1≤ Quantile(1−α;V1:n∪{∞}).
By the symmetric construction of the nonconformity scores in (4),
(Z1,...,Z n+1)
d
= (Zσ(1),...,Z σ(n+1)) ⇐⇒ (V1,...,V n+1)
d
= (Vσ(1),...,V σ(n+1)),
for any permutationσ of the numbers 1,...,n + 1. Therefore, asZ1,...,Z n+1 are exchangeable, so areV1,...,V n+1,
and applying Lemma 1 gives the result.
Remark 1. Theorem 1 is stated for exchangeable samples (Xi,Yi),i = 1,...,n + 1, which is (signiﬁcantly) weaker
than assuming i.i.d. samples. As we will see in what follows, it is furthermore possible to relax the exchangeability
assumption, under an appropriate modiﬁcation to the conformal procedure.
Remark 2. If we use an appropriate random tie-breaking rule (to determine the rank ofVn+1 amongV1,...,V n+1),
then the upper bounds in Lemma 1 and Theorem 1 hold in general (without assuming there are no ties almost surely).
The result in Theorem 1, albeit very simple to prove, is quite remarkable. It gives us a recipe for distribution-free
prediction intervals, with nearly exact coverage, starting from an arbitrary score functionS; e.g., absolute residuals
with respect to a ﬁtted regression function from any base algorithmA, as in (3). For more discussion of conformal
prediction, its properties, and its variants, we refer to V ovk et al. (2005); Lei et al. (2018) and references therein.
2 Covariate shift
In this paper, we are concerned with settings in which the data (Xi,Yi),i = 1,...,n + 1 are no longer exchangeable.
Our primary focus will be a setting in which we observe data according to
(Xi,Yi)
i.i.d.
∼ P =PX×PY|X, i= 1,...,n,
(Xn+1,Yn+1)∼ ~P = ~PX×PY|X, independently. (6)
Notice that the conditional distribution ofY|X is assumed to be the same for both the training and test data. Such a
setting is often called covariate shift (e.g., see Shimodaira 2000; Quinonero-Candela et al. 2009; see also Remark 4
below for more discussion of this literature). The key realization is the following: if we know the ratio of test to training
covariate likelihoods, d~PX/dPX, then we can still perform a modiﬁed of version conformal inference, using a quantile
of a suitably weighted empirical distribution of nonconformity scores. The next subsection gives the details; following
this, we describe a more computationally efﬁcient conformal procedure, and give an empirical demonstration.
2.1 Weighted conformal prediction
In conformal prediction, we compare the value of a nonconformity score at a test point to the empirical distribution of
nonconformity scores at the training points. In the covariate shift case, where the covariate distributions PX,~PX in
our training and test sets differ, we will now weight each nonconformity scoreV (x,y)i (which measures how wellZi =
3

=== PDF PAGE 4 ===
(Xi,Yi) conforms to the other points) by a probability proportional to the likelihood ratiow(Xi) = d~PX (Xi)/dPX (Xi).
Therefore, we will no longer be interested in the empirical distribution
1
n + 1
n∑
i=1
δV (x,y)i + 1n + 1δ∞,
as in Theorem 1, but rather, a weighted version
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞,
where the weights are deﬁned by
pwi (x) = w(Xi)∑n
j=1w(Xj) +w(x), i= 1,...,n, and pwn+1(x) = w(x)∑nj=1w(Xj) +w(x). (7)
Due this careful weighting, draws from the discrete distribution in the second to last display resemble nonconformity
scores computed on the test population, and thus, they “look exchangeable” with the nonconformity score at our test
point. Our main result below formalizes these claims.
Corollary 1. Assume data from the model(6). Assume that ~PX is absolutely continuous with respect toPX, and denote
w = d~PX/dPX. For any score functionS, and anyα∈ (0, 1), deﬁne forx∈ Rd,
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile
(
1−α;
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞
)}
, (8)
whereV (x,y)i ,i = 1,...,n + 1 are as in (4), andpwi (x),i = 1,...,n + 1 are as in (7). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Corollary 1 is a special case of a more general result that we present later in Theorem 2, which extends conformal
inference to a setting in which the data are what we call weighted exchangeable. The proof is given in Section 3.5.
Remark 3. The same result as in Corollary 1 holds ifw∝ d~PX/dPX, i.e., with an unknown normalization constant,
because this normalization constant cancels out in the calculation of probabilities in (7).
Remark 4. Though the basic premise of covariate shift—and certainly the techniques employed in addressing it—are
related to much older ideas in statistics, the speciﬁc setup (6) has recently generated great interest in machine learning:
e.g., see Sugiyama and Muller (2005); Sugiyama et al. (2007); Quinonero-Candela et al. (2009); Agarwal et al. (2011);
Wen et al. (2014); Reddi et al. (2015); Chen et al. (2016) and references therein). The focus is usually on correcting
estimators, model evaluation, or model selection approaches to account for covariate shift. Correcting distribution-free
prediction intervals, as we examine in this work, is (as far as we know) a new contribution. As one might expect, the
likelihood ratio d~PX/dPX, a key component of our conformal construction in Corollary 1, also plays a critical role in
much of the literature on covariate shift.
2.2 Weighted split conformal
In general, constructing a conformal prediction band can be computationally intensive, though this of course depends
on the choice of score function. Consider the use of absolute residuals as in (3). To compute the nonconformity scores
in (4), we must ﬁrst run our base algorithmA on the data setZ1:n∪{ (x,y )} to produce a ﬁtted regression functionˆµ,
and then calculate
V (x,y)i =|Yi−ˆµ(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−ˆµ(x)|.
As the formation of the conformal set in (5) (ordinary case) or (8) (covariate shift case) requires us to do this for each
x∈ Rd andy∈ R (which requires reﬁttingˆµ each time), this can clearly become computationally burdernsome.
A fast alternative, known as split conformal prediction (Papadopoulos et al., 2002; Lei et al., 2015), resolves this
issue by taking the score functionS to be deﬁned using absolute residuals with respect to a ﬁxed regression function,
4

=== PDF PAGE 5 ===
typically, one that has been trained on an preliminary data set. Denote by (X 01,Y 01 ),..., (X 0n0,Y 0n0 ) this preliminary
data set, used for ﬁtting the regression functionµ0, and consider the score function
S
(
(x,y ),Z
)
=|y−µ0(x)|.
Given data (X1,Y 1),..., (Xn,Yn), independent of (X 01,Y 01 ),..., (X 0n0,Y 0n0 ), we calculate
V (x,y)i =|Yi−µ0(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−µ0(x)|.
The conformal prediction interval (5), deﬁned at a pointx∈ Rd, reduces to
ˆCn(x) = µ0(x)± Quantile
(
1−α;
{
|Yi−µ0(Xi)|
}n
i=1∪{∞}
)
, (9)
and by Theorem 1 it has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ). This coverage result holds
because, when we treatµ0 as ﬁxed (meaning, condition on (X 01,Y 01 ),..., (X 0n0,Y 0n0 )), the scoresV (x,y)1 ,...,V (x,y)n+1
scores are exchangeable for (x,y ) = (Xn+1,Yn+1), as (X1,Y 1),..., (Xn+1,Yn+1) are.
As split conformal prediction can be seen as a special case of conformal prediction, in which the regression function
µ0 is treated as ﬁxed, Corollary 1 also applies to the split scenario, and guarantees that the band deﬁned forx∈ Rd by
ˆCn(x) = µ0(x)± Quantile
(
1−α;
n∑
i=1
pwi (x)δ|Yi−µ0(Xi)| +pwn+1(x)δ∞
)
, (10)
where the probabilities are as in (7), has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ).
2.3 Airfoil data example
We demonstrate the use of conformal prediction in the covariate shift setting in an empirical example. We consider the
airfoil data set from the UCI Machine Learning Repository (Dua and Graff, 2019), which hasN = 1503 observations of
a responseY (scaled sound pressure level of NASA airfoils), and a covariateX withd = 5 dimensions (log frequency,
angle of attack, chord length, free-stream velocity, and suction side log displacement thickness). For efﬁciency, we use
the split conformal prediction methods in (9) and (10) for the unweighted and weighted case, respectively. R code to
reproduce these simulation results can be found at http://www.github.com/ryantibs/conformal/.
Creating training data, test data, and covariate shift. We repeated an experiment for 5000 trials, where for each
trial we randomly partitioned the data{(Xi,Yi)}Ni=1 into three setsDpre,D train,D test, and also constructed a covariate
shift test setDshift, which have the following roles.
• Dpre, containing 25% of the data, is used to preﬁt a regression functionµ0 via linear regression, to be used in
constructing split conformal intervals.
• Dtrain, containing 25% of the data, is our training set, i.e., (Xi,Yi),i = 1,...,n , used to compute the residual
quantiles in the construction of the split conformal prediction intervals (9) and (10).
• Dtest, containing 50% of the data, is our test set (as these data points are exchangeable with those inDtrain, there
is no covariate shift in this test set).
• Dshift is a second test set, constructed to simulate covariate shift, by sampling 25% of the points fromDtest with
replacement, with probabilities proportional to
w(x) = exp(xTβ), where β = (−1, 0, 0, 0, 1). (11)
As the original data pointsDtrain∪Dtest can be seen as draws from the same underlying distribution, we can view
w(x) as the likelihood ratio of covariate distributions between the test setDshift and training setDtrain. Note that the test
covariate distribution~PX, which satisﬁes d~PX∝ exp(xTβ)dPX as we have deﬁned it here, is called an exponential
tilting of the training covariate distributionPX. Figure 1 visualizes the effect of this exponential tilting, in the airfoil
data set, with our choiceβ = (−1, 0, 0, 0, 1). Only the 1st and 5th dimensions of the covariate distribution are tilted;
the bottom row of Figure 1 plots the marginal densities of the 1st and 5th covariates (estimated via kernel smoothing)
before and after the tilt. The top row plots the response versus the 1st and 5th covariates, simply to highlight the fact
that there is heteroskedasticity, and thus we might expect the shift in the covariate distribution to have some effect on
the validity of the ordinary conformal prediction intervals.
5

=== PDF PAGE 6 ===
●
●
●●
●
●
●
●
●●● ●
●
●
●
●
●</message>
<message type="ai">
  <tool_call id="call_39df775b8dc2458ab7599ca13e313af2" name="read_file">{"file_path": "/work/literature/2009.14193.txt", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-300 of 898 | next offset 300 @@
=== PDF PAGE 1 ===
UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in computer vision.
Formally, for a discrete responseY ∈Y ={1,...,K } and a feature vectorX∈ Rd, we desire an
uncertainty set function,C(X), mapping a feature vector to a subset of{1,...,K } such that
P (Y ∈C (X))≥ 1−α, (1)
for a pre-speciﬁed conﬁdence levelα such as 10%. Conformal predictors like our method can mod-
ify any black-box classiﬁer to output predictive sets that are rigorously guaranteed to satisfy the
∗equal contribution
†Project website here.
1
arXiv:2009.14193v5  [cs.CV]  3 Sep 2022

=== PDF PAGE 2 ===
Figure 1: Prediction set examples on Imagenet. We show three examples of the class fox squirrel and
the 95% prediction sets generated by RAPS to illustrate how the size of the set changes as a function of the
difﬁculty of a test-time image.
desired coverage property shown in Eq. (1). For evaluations, we focus on Imagenet classiﬁcation
using convolutional neural networks (CNNs) as the base classiﬁers, since this is a particularly chal-
lenging testbed. In this setting,X would be the image andY would be the class label. Note that the
guarantee in Eq. (1) is marginal overX andY —it holds on average, not for a particular imageX.
A ﬁrst approach toward this goal might be to assemble the set by including classes from highest to
lowest probability (e.g., after Platt scaling and a softmax function; see Platt et al., 1999; Guo et al.,
2017) until their sum just exceeds the threshold 1−α. We call this strategy naive and formulate
it precisely in Algorithm 1. There are two problems with naive: ﬁrst, the probabilities output by
CNNs are known to be incorrect (Nixon et al., 2019), so the sets from naive do not achieve cov-
erage. Second, image classiﬁcation models’ tail probabilities are often badly miscalibrated, leading
to large sets that do not faithfully articulate the uncertainty of the model; see Section 2.3. Moreover,
smaller sets that achieve the same coverage level can be generated with other methods.
The coverage problem can be solved by picking a new threshold using holdout samples. For exam-
ple, withα =10%, if choosing sets that contain 93% estimated probability achieves 90% coverage
on the holdout set, we use the 93% cutoff instead. We refer to this algorithm, introduced in Ro-
mano et al. (2020), as Adaptive Prediction Sets (APS). The APS procedure provides coverage but
still produces large sets. To ﬁx this, we introduce a regularization technique that tempers the in-
ﬂuence of these noisy estimates, leading to smaller, more stable sets. We describe our proposed
algorithm, Regularized Adaptive Prediction Sets (RAPS), in Algorithms 2 and 3 (with APS as a
special case). As we will see in Section 2, both APS and RAPS are always guaranteed to satisfy
Eq. (1)—regardless of model and dataset. Furthermore, we show that RAPS is guaranteed to have
better performance than choosing a ﬁxed-size set. Both methods impose negligible computational
requirements in both training and evaluation, and output useful estimates of the model’s uncertainty
on a new image given, say, 1000 held-out examples.
In Section 3 we conduct the most extensive evaluation of conformal prediction in deep learning to
date on Imagenet and Imagenet-V2. We ﬁnd that RAPS sets always have smaller average size than
naive and APSsets. For example, using a ResNeXt-101, naive does not achieve coverage, while
APS and RAPS achieve it almost exactly. However,APS sets have an average size of 19, whileRAPS
sets have an average size of 2 atα = 10% (Figure 2 and Table 1). We will provide an accompanying
codebase that implements our method as a wrapper for any PyTorch classiﬁer, along with code to
exactly reproduce all of our experiments.
1.1 R ELATED WORK
Reliably estimating predictive uncertainty for neural networks is an unsolved problem. Historically,
the standard approach has been to train a Bayesian neural network to learn a distribution over net-
work weights (Quinonero-Candela et al., 2005; MacKay, 1992; Neal, 2012; Kuleshov et al., 2018;
Gal, 2016). This approach requires computational and algorithmic modiﬁcations; other approaches
avoid these via ensembles (Lakshminarayanan et al., 2017; Jiang et al., 2018) or approximations of
Bayesian inference (Riquelme et al., 2018; Sensoy et al., 2018). These methods also have major
practical limitations; for example, ensembling requires training many copies of a neural network ad-
versarially. Therefore, the most widely used strategy is ad-hoctraditional calibration of the softmax
scores with Platt scaling (Platt et al., 1999; Guo et al., 2017; Nixon et al., 2019).
2

=== PDF PAGE 3 ===
0.9 0.95 0.99
desired coverage (1- )
0.85
0.90
0.95
1.00empirical coverage
Naive
APS
RAPS
0.9 0.95 0.99
desired coverage (1- )
0
20
40
60
80
100average size
Figure 2: Coverage and average set size on Imagenet for prediction sets from three methods.All methods
use a ResNet-152 as the base classiﬁer, and results are reported for 100 random splits of Imagenet-Val, each of
size 20K. See Section 3.1 for full details.
This work develops a method for uncertainty quantiﬁcation based onconformal prediction. Originat-
ing in the online learning literature, conformal prediction is an approach for generating predictive
sets that satisfy the coverage property in Eq. (1) (V ovk et al., 1999; 2005). We use a convenient
data-splitting version known as split conformal prediction that enables conformal prediction meth-
ods to be deployed for essentially any predictor (Papadopoulos et al., 2002; Lei et al., 2018). While
mechanically very different from traditional calibration as discussed above, we will refer to our
approach as conformal calibration to highlight that the two methodologies have overlapping but
different goals.
Conformal prediction is a general framework, not a speciﬁc algorithm—important design decisions
must be made to achieve the best performance for each context. To this end, Romano et al. (2020)
and Cauchois et al. (2020) introduce techniques aimed at achieving coverage that is similar across
regions of feature space, whereas ?Hechtlinger et al. (2018) and ? introduce techniques aimed at
achieving equal coverage for each class. While these methods have conceptual appeal, thus far
there has been limited empirical evaluation of this general approach for state-of-the-art CNNs. Con-
cretely, the only works that we are aware of that include some evaluation of conformal methods on
ImageNet—the gold standard for benchmarking computer vision methods—are Hechtlinger et al.
(2018), Park et al. (2019), Cauchois et al. (2020), and Messoudi et al. (2020), although in all four
cases further experiments are needed to more fully evaluate their operating characteristics for practi-
cal deployment. At the heart of conformal prediction is theconformal score: a measure of similarity
between labeled examples which is used to compare a new point to among those in a hold out set.
Our theoretical contribution can be summarized as a modiﬁcation of the conformal score from Ro-
mano et al. (2020) to have smaller, more stable sets. Lastly, there are alternative approaches to
returning prediction sets not based on conformal prediction (Pearce et al., 2018; Zhang et al., 2018).
These methods can be used as input to a conformal procedure to potentially improve performance,
but they do not have ﬁnite-sample coverage guarantees when used alone.
2 M ETHODS
In developing uncertainty set methods to improve upon naive, we are guided by three desiderata.
First and most importantly, the coverage desideratum says the sets must provide 1−α coverage, as
Algorithm 1 Naive Prediction Sets
Input: α, sorted scoress, associated permutation of classesI, booleanrand
1: procedure NAIVE (α,s,I,rand )
2: L← 1
3: while∑Li=1si &lt; 1−α do ⊿ Stop if 1−α probability exceeded
4: L←L + 1
5: ifrand then ⊿ Break ties randomly (explained in Appendix B)
6: U← Unif(0, 1)
7: V ← (∑Li=1si− (1−α))/sL
8: ifU≤V then
9: L←L− 1
10: return
{
I1,...,I L
}
Output: The 1−α prediction set,
{
I1,...,I L
}
3

=== PDF PAGE 4 ===
τ^ccal0
25%
50%
75%
1−α′
100%
τ: set size parameter
empirical coverage
(a) Conformal calibration
0.50.5
0.770.77
0.920.92
1.021.02
1.091.09 1.151.15
kreg τ^ccal
0.0
0.2
0.4
c d f b e a
class
penalized probability
penalty
probability (b) A RAPS prediction set
Figure 3: Visualizations of conformal calibration and RAPS sets. In the left panel, the y-axis shows the
empirical coverage on the conformal calibration set, and 1−α′ =⌈(n + 1)(1−α)⌉/n. In the right panel, the
printed numbers indicate the cumulative probability plus penalty mass. For the indicated value ˆτccal, the RAPS
prediction set is{c, d, f, b}.
discussed above. Secondly, the size desideratum says we want sets of small size, since these convey
more detailed information and may be more useful in practice. Lastly, the adaptiveness desidera-
tum says we want the sets to communicate instance-wise uncertainty: they should be smaller for
easy test-time examples than for hard ones; see Figure 1 for an illustration. Coverage and size
are obviously competing objectives, but size and adaptiveness are also often in tension. The size
desideratum seeks small sets, while the adaptiveness desideratum seeks larger sets when the classi-
ﬁer is uncertain. For example, always predicting a set of size ﬁve could achieve coverage, but it is
not adaptive. As noted above, both APSand RAPS achieve correct coverage, and we will show that
RAPS improves upon APS according to the other two desiderata.
We now turn to the speciﬁcs of our proposed method. We begin in Subsection 2.1 by describing an
abstract data-splitting procedure called conformal calibration that enables the near-automatic con-
struction of valid predictive sets (that is, sets satisfying Eq. (1)). Subsequently, in Subsection 2.2, we
provide a detailed presentation of our procedure, with commentary in Section 2.3. In Subsection 2.4
we discuss the optimality of our procedure, proving that it is at least as good as the procedure that
returns sets of a ﬁxed size, unlike alternative approaches.
2.1 C ONFORMAL CALIBRATION
We ﬁrst review a general technique for producing valid prediction sets, following the articulation
in Gupta et al. (2019). Consider a procedure that outputs a predictive set for each observation,
and further suppose that this procedure has a tuning parameter τ that controls the size of the sets.
(In RAPS, τ is the cumulative sum of the sorted, penalized classiﬁer scores.) We take a small
independent conformal calibration set of data, and then choose the tuning parameter τ such that
the predictive sets are large enough to achieve 1−α coverage on this set. See Figure 3 for an
illustration. This calibration step yields a choice ofτ, and the resulting set is formally guaranteed to
have coverage 1−α on a future test point from the same distribution; see Theorem 1 below.
Formally, let (Xi,Yi)i=1,...,n be an independent and identically distributed (i.i.d.) set of variables
that was not used for model training. Further, let C(x,u,τ ) : Rd× [0, 1]× R→ 2Y be a set-
valued function that takes a feature vectorx to a subset of the possible labels. The second argument
u is included to allow for randomized procedures; let U1,...,U n be i.i.d. uniform [0, 1] random
variables that will serve as the second argument for each data point. Suppose that the sets are
indexed byτ such that they are nested, meaning larger values ofτ lead to larger sets:
C(x,u,τ 1)⊆C (x,u,τ 2) if τ1≤τ2. (2)
To ﬁnd a function that will achieve 1−α coverage on test data, we select the smallest τ that gives
at least 1−α coverage on the conformal calibration set, with a slight correction to account for the
ﬁnite sample size:
ˆτccal = inf
{
τ :|{i :Yi∈C (Xi,Ui,τ )}|n ≥⌈(n + 1)(1−α)⌉n }. (3)
The set function C(x,u,τ ) with this data-driven choice of τ is guaranteed to have correct ﬁnite-
sample coverage on a fresh test observation, as stated formally next.
4

=== PDF PAGE 5 ===
Theorem 1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi,Ui)i=1,...,n and
(Xn+1,Yn+1,Un+1) are i.i.d. and letC(x,u,τ ) be a set-valued function satisfying the nesting prop-
erty in Eq. (2). Suppose further that the sets C(x,u,τ ) grow to include all labels for large enough
τ: for all x∈ Rd,C(x,u,τ ) = Y for some τ. Then for ˆτccal deﬁned as in Eq. (3), we have the
following coverage guarantee:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≥ 1−α.
This is the same coverage property as Eq. (1) in the introduction, written in a more explicit manner.
The result is not new—a special case of this result leveraging sample-splitting ﬁrst appears in the
regression setting in Papadopoulos et al. (2002), and the core idea of conformal prediction was
introduced even earlier; see V ovk et al. (2005).
As a technical remark, the theorem also holds if the observations to satisfy the weaker condition
of exchangeability; see V ovk et al. (2005). In addition, for most families of set-valued functions
C(x,u,τ ) there is a matching upper bound:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≤ 1−α + 1n + 1.
Roughly speaking, this will hold whenever the sets grow smoothly in τ. See Lei et al. (2018) for a
formal statement of the required conditions.
2.2 O UR METHOD
Conformal calibration is a powerful general idea, allowing one to achieve the coverage desideratum
for any choice of setsC(x,u,τ ). Nonetheless, this is not yet a full solution, since the quality of the
resulting prediction sets can vary dramatically depending on the design ofC(x,u,τ ). In particular,
we recall the size and adaptiveness desiderata from Section 1—we want our uncertainty sets to be
as small as possible while faithfully articulating the instance-wise uncertainty of each test point. In
this section, we explicitly give our algorithm, which can be viewed as a special case of conformal
calibration with the uncertainty setsC designed to extract information from CNNs.
Our algorithm has three main ingredients. First, for a feature vector x, the base model computes
class probabilities ˆπx∈ Rk, and we order the classes from most probable to least probable. Then,
we add a regularization term to promote small predictive sets. Finally, we conformally calibrate the
penalized prediction sets to guarantee coverage on future test points.
Formally, letρx(y) =∑Ky′=1 ˆπx(y′)I{ˆπx(y′)&gt;ˆπx(y)} be the total probability mass of the set of labels
that are more likely than y. These are all the labels that will be included before y is included. In
addition, letox(y) =|{y′∈Y : ˆπx(y′)≥ ˆπx(y)}| be the ranking ofy among the label based on the
probabilities ˆπ. For example, ify is the third most likely label, thenox(y) = 3.1 We take
C∗(x,u,τ ) :={y : ρx(y) + ˆπx(y)·u +λ· (ox(y)−kreg)+| {z }
regularization
≤τ
}
, (4)
where (z)+ denotes the positive part of z andλ,kreg≥ 0 are regularization hyperparameters that
are introduced to encourage small set sizes. See Figure 3 for a visualization of a RAPS predictive
set and Appendix E for a discussion of how to selectkreg andλ.
Since this is the heart of our proposal, we carefully parse each term. First, the ρx(y) term increases
asy ranges from the most probable to least probable label, so our sets will prefer to include they that
are predicted to be the most probable. The second term, ˆπx(y)·u, is a randomized term to handle
the fact that the value will jump discretely with the inclusion of each newy. The randomization term
can never impact more than one value of y: there is at most one value of y such thaty∈C (x, 0,τ )
buty /∈C (x, 1,τ ). These ﬁrst two terms can be viewed as the CDF transform after arranging the
classes from most likely to least likely, randomized in the usual way to result in a continuous uniform
random variable (cf. Romano et al., 2020). We discuss randomization further in Appendix B.
Lastly, the regularization promotes small set sizes: for values ofy that occur farther down the ordered
list of classes, the termλ· (ox(y)−kreg)+ makes that value ofy require a higher value ofτ before
1For ease of notation, we assume distinct probabilities. Else, label-ordering ties should be broken randomly.
5

=== PDF PAGE 6 ===</message>
<message type="ai">
  <tool_call id="call_db5e531cc1e14b24a5773481e157ab23" name="read_file">{"file_path": "/work/literature/2402.10723.txt", "limit": 330, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-330 of 949 | next offset 330 @@
=== PDF PAGE 1 ===
CONFORMALIZED CREDAL SET PREDICTORS
A PREPRINT
Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2
1Institute of Informatics, LMU Munich, Germany
2Munich Center for Machine Learning (MCML), Germany
3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany
alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de
ABSTRACT
Credal sets are sets of probability distributions that are considered as candidates for an imprecisely
known ground-truth distribution. In machine learning, they have recently attracted attention as an
appealing formalism for uncertainty representation, in particular due to their ability to represent
both the aleatoric and epistemic uncertainty in a prediction. However, the design of methods for
learning credal set predictors remains a challenging problem. In this paper, we make use of conformal
prediction for this purpose. More specifically, we propose a method for predicting credal sets in the
classification task, given training data labeled by probability distributions. Since our method inherits
the coverage guarantees of conformal prediction, our conformal credal sets are guaranteed to be
valid with high probability (without any assumptions on model or distribution). We demonstrate the
applicability of our method to natural language inference, a highly ambiguous natural language task
where it is common to obtain multiple annotations per example.
Keywords Conformal Prediction · Uncertainty Representation · Credal Sets
1 Introduction
Representing and quantifying uncertainty is becoming increasingly important in machine learning (ML), particularly
as ML models are employed in safety-critical application domains such as medicine or autonomous driving. In such
domains, a distinction between so-called aleatoric uncertainty and epistemic uncertainty is often useful [Hora, 1996].
Broadly speaking, aleatoric uncertainty is due to the inherent randomness of the data-generating process, whereas
epistemic uncertainty stems from the learner’s lack of knowledge about the best predictive model. Thus, while the
former is irreducible, the latter can in principle be reduced through additional information, e.g., by gathering additional
data to learn from.
Representation of aleatoric and epistemic uncertainty requires formalism more expressive than standard probability
distributions [H¨ullermeier and Waegeman, 2021]. One such formalism which prevails in the recent ML literature is
second-order probability distributions. Essentially, in a classification setting, these are distributions over distributions
over classes. Models producing second-order distributions as predictions can be learned in a classical Bayesian way
[Kendall and Gal, 2017, Depeweg et al., 2018] or using more recent approaches such as evidential deep learning [Sensoy
et al., 2018]. Yet, approaches of that kind are not unproblematic and have been subject to criticism [Bengs et al., 2022,
2023]. Another formalism suitable for representing both types of uncertainty is the concept of a credal set, which is
well-established in the field of imprecise probability theory [Walley, 1991] and meanwhile also attracted attention in ML
[Shaker and H¨ullermeier, 2020, H¨ullermeier et al., 2022]. Credal sets are (convex) sets of probability distributions that
can be considered as candidates for an imprecisely known ground-truth distribution. Figure 1 shows examples of credal
sets in a three-class scenario, where the space of distributions can be visualized by the two-dimensional probability
simplex. Broadly speaking, the larger the credal set, the higher the epistemic uncertainty, and the more “in the middle”
the set is located, i.e., the closer it is to the uniform distribution, the higher the aleatoric uncertainty.
arXiv:2402.10723v1  [stat.ML]  16 Feb 2024

=== PDF PAGE 2 ===
Conformalized Credal Set Predictors A PREPRINT
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
Figure 1: For the three-class classification setting, the space of probability distributions can be illustrated by a two-
dimensional simplex: each point in the simplex corresponds to a probability distribution so that credal sets can be
depicted as regions. The left case corresponds to the special case of a singleton (credal) set, i.e., a precise probability
distribution, signifying aleatoric but no epistemic uncertainty. The case in the middle represents partial knowledge
with a certain degree of (epistemic) uncertainty about the true distribution, and the right one corresponds to the case of
complete ignorance, where nothing is known about the distribution.
Premise a child is on the
ground crying.
Hypothesis A child on the ground
crying as others look
on.
True dist. [0.06, 0.94, 0.00]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Premise uh-huh and is it true i
mean is it um
Hypothesis It is absolutely cor-
rect.
True dist. [0.31, 0.52, 0.17]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Figure 2: An illustration of our proposed conformalized credal sets on two instances from the ChaosNLI dataset [Nie
et al., 2020]. Green regions indicate credal sets, while the true and the predicted distributions are marked with orange
squares and black circles, respectively.
Learning to predict second-order representations, such as credal sets or second-order distributions, from standard
“zero-order” supervised data — training instances together with observed class labels — is a difficult endeavor. For
the case of second-order probabilities, it is even provably impossible to predict uncertainty in an “unbiased” way, i.e.,
without imposing strong prior assumptions on the epistemic uncertainty [Bengs et al., 2022, 2023]. In this paper, we
assume “first-order” training data, i.e., instances associated with probability distributions over the class labels. In other
words, instances are labeled probabilistically instead of being assigned a deterministic class label. Obviously, this type
of data facilitates second-order learning. Not less importantly, it is becoming increasingly available in practice, for
example, in the form of aggregations over multiple annotations per data instance, and hence increasingly relevant in
applications [Uma et al., 2022, Stutz et al., 2023b]
Our method leverages the framework of conformal prediction (CP), a non-parametric approach for set-valued prediction
rooted in classical frequentist statistics [V ovk et al., 2022]. Based on relatively mild assumptions, CP is able to provide
theoretical guarantees in the form of marginal coverage: Predicted sets are guaranteed to cover the true target with high
probability. Since our method inherits these coverage guarantees, our conformal credal sets are guaranteed to be valid
with high probability (without any assumptions on model or distribution).
Our main contribution is the proposal of a novel, conformal method to construct credal set predictors from first-order
training data:
• We propose a CP based method to construct conformal credal sets. To this end, we make use of two types
of nonconformity functions based on distance resp. likelihood, and leveraging first-order resp. second-order
probability predictors.
• On ChaosNLI [Nie et al., 2020], a very ambiguous natural language inference task with multiple annotations per
example, we show that our conformal credal sets are indeed valid, i.e., include the true ground truth distribution
with high probability (see Figure 2 for an illustration). We also compare the efficiency of predictions (size of
the predicted sets) for different nonconformity functions.
• We complement this study with controlled experiments on synthetic data, specifically investigating the
performance of credal set prediction in the presence of label noise.
2

=== PDF PAGE 3 ===
Conformalized Credal Set Predictors A PREPRINT
2 Related Work
Credal sets are widely used as models for representing uncertainty, notably within the domain of imprecise probabilities
[Walley, 1991]. As already mentioned, they can represent both types of uncertainty, aleatoric and epistemic. In the
context of data analysis and statistical inference, credal sets are often used as robust models of prior information, namely
for modeling imprecise information about the prior in Bayesian inference [Walley, 1996].
In machine learning, credal sets have been used for generalizing some of the standard methods, including naive Bayes
[Zaffalon, 2002, Corani and Zaffalon, 2008], Bayesian networks [Corani et al., 2012], and decision trees [Abell´an and
Moral, 2003]. Typically, these approaches generalize simple frequentist inference to robust Bayesian inference, making
use of an imprecise version of the Dirichlet model (a conjugate prior for the multinomial distribution). Compared to our
approach, these methods are learning on standard (zero-order) training data. Moreover, despite representing uncertainty
in predictions, they do not provide any formal guarantees.
Conformal prediction [V ovk et al., 2022], briefly introduced in Section 3.2 below, has recently gained attention for
various applications in machine learning, especially for classification tasks [Sadinle et al., 2019, Romano et al., 2020,
Angelopoulos et al., 2020, Stutz et al., 2021, Fisch et al., 2022]. These methods mostly focus on split conformal
prediction using a held-out calibration set [Papadopoulos et al., 2002], overcoming computational limitations of earlier
transductive or bagging approaches [V ovk et al., 2022, V ovk, 2015, Steinberger and Leeb, 2016, Barber et al., 2021,
Linusson et al., 2020]. While tackling classification tasks, our method for constructing conformal credal sets has more
similarity with conformal regression [Romano et al., 2019, Sesia and Romano, 2021], particularly in multivariate settings
[Dietterich and Hostetler, 2022], as we essentially conformalize the simplex space of categorical distributions. Our
conformity scores differ, however, in that they are specific for distributions rather than considering general multivariate
spaces. This work also relates to work on appropriate measures of inefficiency [V ovk et al., 2017] as measuring the
inefficiency of our conformal credal sets is non-trivial. Most closely related to our work is the recent work by Stutz et al.
[2023b], who consider conformal prediction in settings with high aleatoric uncertainty. However, we explicitly target
the construction of conformal credal sets, while Stutz et al. [2023b] mainly focus on constructing confidence sets of
classes.
First-order data. In settings with high aleatoric uncertainty, labeling each example with a single, unique class is clearly
insufficient. In practice, this is typically captured by high disagreement among annotators – a problem particularly
common in natural language tasks [Reidsma and op den Akker, 2008, Aroyo and Welty, 2014, 2015, Schaekermann
et al., 2016, Dumitrache et al., 2019, Pavlick and Kwiatkowski, 2019, R¨ottger et al., 2022, Abercrombie et al., 2023].
Handling this disagreement has received considerable attention lately [Uma et al., 2021] as it offers to go beyond this
zero-order information. For example, recent work on evaluation with disagreeing annotators [Stutz et al., 2023a] argues
the use of these annotations to get approximate first-order information for evaluation. This approach is becoming more
and more viable with crowdsourcing tools [Kovashka et al., 2016, Sorokin and Forsyth, 2008, Snow et al., 2008] being
an integral component of the benchmark, making multiple annotations per data instance more accessible. We follow a
similar approach in our construction of conformal credal sets.
3 Background
3.1 Supervised Learning and Predictive Uncertainty
We consider the setting of (polychotomous) classification with label space Y = {1, . . . , K} and an instance space X .
As usual, we assume an underlying data-generating process in the form of a probability distribution P on X × Y, so
that observations (X, Y) are i.i.d. samples from P . We denote by λx ∈ ∆K the conditional probability distribution
P (· |X = x), which we also consider as an element of the (K − 1)-simplex
∆K := λ = (λ1, . . . , λK)⊤ | λk ≥ 0, ∥λ∥1 = 1	 ⊂ RK .
Thus, for each class label k ∈ Y, the probability to observe Y = k as an outcome for x ∈ Xis given by λxk .
Since the dependency between instances X and outcomes Y is non-deterministic, the prediction of Y given X = x is
necessarily afflicted with uncertainty, even if the ground-truth distributionλx is known. As already said, this uncertainty
is commonly referred to as aleatoric [H ¨ullermeier and Waegeman, 2021]. Intuitively, the closer λx to the uniform
distribution puni = (1/K, . . . ,1/K)⊤, the higher the uncertainty, and the closer it is to a degenerate (Dirac) distribution
assigning all probability mass to a single class (a corner point in ∆K), the lower the uncertainty. Various measures
have been proposed to quantify this uncertainty in numerical terms, with Shannon entropy as the arguably best-known
representative [Depeweg et al., 2018].
3

=== PDF PAGE 4 ===
Conformalized Credal Set Predictors A PREPRINT
Instead of assuming λx to be known, suppose now that only a prediction ˆλx of this distribution is available. Epistemic
uncertainty refers to the uncertainty about how well the latter approximates the former, and hence to the additional
uncertainty in the prediction of outcome Y that is caused by the discrepancy between ˆλx and the ground-truth λx. We
seek to capture this discrepancy by means of credal sets
Q ∈ QK ⊂ ∆K ,
with the idea that Q ∋ λx holds with high probability. Typically, credal sets are assumed to be convex, and further
restrictions might be imposed on QK for practical and computational reasons, for example, a restriction to convex
polygons (with a finite number of extreme points).
3.2 Conformal Prediction
Conformal prediction provides a general framework for producing set-valued predictions with a certain guarantee of
validity. In a supervised setting, consider data points of the form Z = (X, U) ∈ X × U, and the task is to predict U
given X = x. We assume the space Z to be equipped with a nonconformity measure f : Z − →R that quantifies the
“strangeness” of z, i.e., the higher f (z), the less normal or expected the data point. Let Dcalib ⊂ Zbe a (randomly
generated) set of data points, called calibration data, and Z another data point that remains unobserved. Under
the assumption of exchangeability, i.e., that the calibration data and the query point Z have been generated by an
exchangeable process, we want to construct a so-called confidence set C ⊆ Uthat guarantees coverage:
P(U ∈ C) ≥ 1 − α. (1)
By a simple combinatorial argument [V ovk et al., 2022], the confidence setC can be constructed as
C(x) :=

u ∈ U |f (x, u) &lt; q(E, α′) 	 , (2)
where α′ = |E| −1⌈(1 + |E|)(1 − α)⌉, and q(E; α′) denotes the α′-quantile of E.
Importantly, the guarantee (2) holds regardless of the nonconformity function f (·), which, however, has an influence
on the efficiency of the prediction: The more appropriate the function, the smaller the prediction set C tends to be.
Normally, f (·) is not predefined but constructed in a data-driven way using training data Dtrain. For example, a common
approach is to train a predictor π : X − → Uand then define f (x, u) in terms of d(u, π(x)), where d(·, ·) is an
appropriate distance function on U. Replacing the point-prediction π(x) ∈ Uby the prediction set C(x) ⊂ Ucan then
be seen as “conformalizing” the predictor π: Using the calibration data, CP estimates a high-probability upper bound
on the distance between point-predictions and actual outcomes, and corrects the former correspondingly.
4 Conformal Credal Set Prediction
Recall the setting and notation from Section 3.1. Our goal is to learn a credal set predictor h : X − → QK, that is, a
model that makes predictions in the form of credal sets, thereby representing both aleatoric and epistemic uncertainty.
To this end, we assume probabilistic training data of the form
D =
 
x1, λx1 , . . . , xN , λxN 	 ⊂ X ×∆K . (3)
The model h should be able to predict the (probabilistic) outcomes for new query instances in a reliable way. More
specifically, suppose that xnew is a new query instance (following the same distribution as the training data) for which a
prediction is sought. The credal prediction Q = h(xnew) should then be valid in the sense that Q ∋ λxnew with high
probability. At the same time, the prediction should be informative in the sense that the (epistemic) uncertainty reflected
by Q is as small as possible. Again, various measures for quantifying the latter can be found in the literature [Klir and
Wierman, 1999, Sale et al., 2023].
We aim to construct the credal set predictor h by means of (inductive) conformal prediction. Following the confor-
malization recipe outlined in Section 3.2, we partition D into Dtrain and Dcalib, using the former for model training and
the latter for calibration. Regarding the training step, we explore two learning strategies, connected with two ways of
defining a nonconformity function, which is pivotal in the calibration step.
The first approach is based on training a standard ( first-order) probability predictor, i.e., a probabilistic classifier
g : X − →∆K that maps instances to the (first-order) probability distribution on Y. This can be achieved, for example,
by minimizing the cross-entropy loss between the ground truth and the predicted distributions, i.e.,
g = argmin
¯g∈H
X
(xi,λxi )∈Dtrain
−
KX
k=1
λxik log(¯g(xi)k),
4

=== PDF PAGE 5 ===
Conformalized Credal Set Predictors A PREPRINT
Algorithm 1 Conformal Credal Set Prediction
Input:
Data D; error rate α; query instance xnew.
Process:
Partition D into Dtrain and Dcalib.
Train a first-order (i = 1) or a second-order (i = 2) predictor using Dtrain.
Choose a nonconformity function fi as in (4) or (6) that suits the trained predictor to obtain the set of scores
Ei.
Set α′ = |Ei|−1⌈(1 + |Ei|)(1 − α)⌉.
Output:
hi(xnew) =

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 .
where H is a hypothesis space. Given a predictor g(·) of this kind, nonconformity is naturally defined in terms of
distance:
f1(x, λx) := d(λx, g(x)) , (4)
where d(·, ·) is a suitable distance function on ∆K, such as total variation, Wasserstein distance, etc.
An alternative approach is motivated by recent work on (epistemic) uncertainty representation via second-order
probability distributions. A second-order learner G : X − →P(∆K) maps each input x to a distribution over ∆K.
Given the training data, meaningful learning in this context can be accomplished, for instance, by parameterizing the
second-order distributions using Dirichlet distributions. Specifically, one can assume that each x is associated with a
Dirichlet distribution characterized by the parameter vector θx ∈ RK+ with the probability density function
P (λ | θx) = 1B(θx)
KY
k=1
λθxk −1k , (5)
where B(·) is the multivariate beta function. This way, λx can be thought of as a sample from that distribution,
i.e., λx ∼ Dir(θx). Our model then essentially yields a prediction ˆθx of the true parameter θx for every x, and its
optimization involves minimizing the negative log-likelihood loss
X
(xi,λxi )∈Dtrain

log(B(ˆθxi )) − KX
k=1
(ˆθxik − 1) log(λxik )

.
Given a second-order predictor ˆθx, nonconformity can be defined as a decreasing function of likelihood, e.g., as 1
minus relative likelihood:
f2(x, λx) = 1 − P (λx | ˆθx)maxλ∈∆K P (λ | ˆθx) . (6)
Using the nonconformity function fi(·) (i ∈ {1, 2}), we obtain the set of nonconformity scores by
Ei :=
n
fi(xj, λxj ) | (xj, λxj ) ∈ Dcalib
o
. (7)
Accordingly, the credal set can be defined as
hi(xnew) :=

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 . (8)
Algorithm 1 outlines a summary of the proposed methods. In the following theorem, we state the validity of the
predicted set, that is, the restatement of the conformal coverage guarantee [V ovk et al., 2022] adjusted to our setting.
Theorem 4.1. Let P denote the joint probability distribution on (X, Λ) ∈ X ×∆K. If data points in Dcalib and
(xnew, λxnew) are drawn i.i.d. (exchangeably) from P, then the conformal credal sets in (8) are valid, i.e.,
P
 
λxnew ∈ hi(xnew) ≥ 1 − α , for i ∈ {1, 2}.
5

=== PDF PAGE 6 ===
Conformalized Credal Set Predictors A PREPRINT
4.1 Noisy Observations
So far, we (implicitly) assumed that ground-truth probability distributions λxi will be provided as training (and
calibration) data. Needless to say, this assumption will rarely hold true in practice. Instead, observations will rather be
noisy versions ˜λxi of the true probabilities, i.e., the data will be of the form
D =
n 
x1, ˜λx1 , . . . , xN , ˜λxN o ⊂ X ×∆K . (9)
Notably, such datasets emerge in scenarios where each data instance x is annotated by multiple human experts, which
recently have attracted a lot of attention in the context of machine learning and also conformal prediction [Stutz
et al., 2023b, Javanmardi et al., 2023]. In this context, ˜λx denotes the distribution derived from aggregating annotator
disagreements concerning the label of instance x. Of course, conformal prediction can still be applied to noisy data of
that kind, but the coverage guarantee will then only hold for the noisy labeling:
P

˜λxnew ∈ h(xnew) ≥ 1 − ˜α. (10)
Practically, one may expect that the guarantees will hold for the ground-truth as well, simply because calibration on
noisy instead of clean data will tend to make prediction regions larger and hence more conservative. Moreover, since
nonconformity is derived from a predictive model g(·) that seeks to recover ground-truth probabilities, the latter should
conform at least as well as noisy distributions. Of course, this intuition is not a formal guarantee. In order to provide
such a guarantee for the ground-truth probabilities, one obviously needs to make some assumptions. Concretely, let us
make the following bounded noise assumption for the labeling process: The labeling noise is (stochastically) bounded
in the sense that, given the nonconformity function f and a (small) probability δ &gt;0, there exists a tolerance ϵ &gt;0
such that
P

|f (x, λx) − f (x, ˜λx)| &lt; ϵ ≥ 1 − δ (11)
all x ∈ X.
Theorem 4.2. Let α &gt;0 be any miscoverage rate, and suppose the bounded noise assumption holds. Let q = q(E, ˜α)
be the critical threshold on the noisy calibration data Dcalib for miscoverage rate
˜α = α − δ1 − δ .
Then, for any new query xnew ∈ X,
P
 
f (xnew, λxnew) &lt; q+ ϵ ≥ 1 − α .
The proof is deferred to Appendix A.. As a consequence of this result, a conformal predictor learned on the noisy data
with modified miscoverage rate ˜α can be turned into a valid predictor (with miscoverage rate α) for the ground-truth
data by increasing the learned rejection threshold by ϵ, provided the bounded noise property (11) can be ascertained.
Thus, if we denote the corresponding credal set predictor by hϵ, we can guarantee that
P
 
λxnew ∈ hϵ(xnew) ≥ 1 − α . (12)
5 Experiments
In this section, we evaluate the performance of our proposed methods using both synthetic and real datasets. In vanilla
conformal prediction, the performance of a method is usually assessed based on the average prediction set size, aka</message>
<message type="ai">
  <tool_call id="call_0c6933c58b004ac48d3b1036f0cb88dd" name="read_file">{"file_path": "/conversation_history/session_a5f648ccde4d4e72a7ccbf5b28ccfcb8.md", "limit": 180, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-180 of 604 | next offset 180 @@
## Summarized at 2026-11-02T18:06:18.267702+00:00

&lt;message type="human"&gt;Research only, do not implement experiment code. Workspace /work. User mandates independent research on conformal uncertainty for compositions, and forbids an unidentified existing paper AND ALL pages citing/discussing it. To avoid accidental access, NO topical search, no citation graph, no recommendation pages. Only fetch exact starter PDFs https://arxiv.org/pdf/2107.07511 (Angelopoulos Bates tutorial), https://arxiv.org/pdf/1904.06019 (Tibshirani et al covariate shift), https://arxiv.org/pdf/2009.14193 (Romano et al classifier uncertainty), https://arxiv.org/pdf/2402.10723 (Conformalized Credal Set Predictors) if desired. These are explicitly allowed. Read papers directly, summarize target distinction discrete label vs observed composition vs latent conditional probability, split quantile, Mondrian/group calibration, weighted shift, and scope limits. Save PDFs under /work/literature and read notes /work/literature_notes.md; include exact pages/equations consulted and correct BibTeX. Additionally obtain latest official ICLR template via exact official repo https://github.com/ICLR/Master-Template (raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027_conference.sty or inspect repo API), or NeurIPS 2026 official template if ICLR latest unavailable; do NOT use broad search. Download official style and template, document latest year, official URL and page limit from official instructions only to /work/template_provenance.md. Other agents handle code. Return concise findings + files + compliance log. If any forbidden content accidentally encountered STOP reading that page and record URL and amount read. Need actual readable PDFs not fabricated summaries.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_793a9683b6b64fb99bd4ee2a0bb017c8" name="search_observations"&gt;{"limit": 3, "memory_type": null, "mode": "ranked", "query": "restricted exact URL paper PDF research conformal compositions official ICLR template", "scope": null}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;{"results": []}&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_491c9f6c5fce494b92a3df7e49c962b0" name="think_tool"&gt;{"reflection": "No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit."}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Reflection recorded: No relevant stored observation. The user prohibits topical search and any citation/recommendation browsing; I will only download the four explicitly allowed exact PDFs and official ICLR repository files/API. Need inspect paper-navigation skill for direct-reading workflow without running its search steps. Verify readable PDFs locally, record exact pages/equations and BibTeX from the primary texts. Latest template can be established only from official repository instructions, with no assumptions about year/page limit.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;content&gt;No relevant prior memory was found. I’ll fetch only the four allowed PDFs and official ICLR template resources—no topical searches, citation graphs, or recommendation pages—and record page-level evidence and access provenance.&lt;/content&gt;
  &lt;tool_call id="call_09c5911ac475422797357163853a2b68" name="write_todos"&gt;{"todos": [{"content": "Download allowed PDFs and inspect direct-reading guidance and workspace.", "status": "in_progress"}, {"content": "Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.", "status": "pending"}, {"content": "Verify and download latest available official template; document provenance and official page-limit evidence.", "status": "pending"}, {"content": "Audit artifacts and report concise findings plus access-compliance log.", "status": "pending"}]}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Updated todo list to [{'content': 'Download allowed PDFs and inspect direct-reading guidance and workspace.', 'status': 'in_progress'}, {'content': 'Read primary PDFs and write page/equation-grounded literature notes with BibTeX and scope limits.', 'status': 'pending'}, {'content': 'Verify and download latest available official template; document provenance and official page-limit evidence.', 'status': 'pending'}, {'content': 'Audit artifacts and report concise findings plus access-compliance log.', 'status': 'pending'}]&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_e9fffcf55c164eeeab43a9d61afb341a" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_1c20d3175c2a49efb50cd10338db4930" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_ae6c2487b3c34554a682b877fe90b431" name="ls"&gt;{}&lt;/tool_call&gt;
  &lt;tool_call id="call_9cbe720f26bd4284aa0c6ecb6deb152a" name="ls"&gt;{}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="tool"&gt;Error invoking tool 'ls' with kwargs {} with error:
 path: Field required
 Please fix the error and try again.&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_1cbb6d81379a430da39099250d0dd123" name="ls"&gt;{"path": "/work"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/.langgraph_api/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_4a2d2382f91540aa96b5ccc0645daa62" name="ls"&gt;{"path": "/skills/paper-navigator"}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;['/skills/paper-navigator/SKILL.md', '/skills/paper-navigator/assets/', '/skills/paper-navigator/references/', '/skills/paper-navigator/requirements.txt', '/skills/paper-navigator/scripts/']&lt;/message&gt;
&lt;message type="ai"&gt;
  &lt;tool_call id="call_96b4712d994842d0b5ac184f4f890eef" name="read_file"&gt;{"file_path": "/skills/paper-navigator/SKILL.md", "limit": 1000, "offset": 0}&lt;/tool_call&gt;
&lt;/message&gt;
&lt;message type="tool"&gt;@@ lines 1-379 of 379 @@
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

Script paths in this document are relative to this skill's directory. Run via `python scripts/&amp;lt;name&amp;gt;.py`.

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
| URL | `python scripts/fetch_paper.py --url &amp;lt;URL&amp;gt;` | Paper Card + reading notes (see `references/reading-strategy.md` for L1/L2/L3) |
| Title quoted | `python scripts/match_paper_by_title.py --title "&amp;lt;title&amp;gt;"` (add `--fallback-search` for typos) | Paper Card |
| Bare ID (arXiv / DOI / S2 / CorpusId) | `python scripts/fetch_paper.py --paper-id &amp;lt;ID&amp;gt; --metadata-only` | Paper Card |

**Paper Card:**

```
📄 **&amp;lt;Title&amp;gt;**
Authors: &amp;lt;First Author&amp;gt; et al. | Year: &amp;lt;Y&amp;gt; | Venue: &amp;lt;V&amp;gt;
Citations: &amp;lt;N&amp;gt; | ID: &amp;lt;ArXiv:xxxx.xxxxx&amp;gt; | DOI: &amp;lt;...&amp;gt;
TLDR: &amp;lt;one sentence&amp;gt;
```

Stop here. Do not chain to citation expansion unless asked.

---

## LIST / ITERATIVE branch — 6 steps

### Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch. When the user gives only a bare noun (concept / model / algorithm / benchmark name) with no direction, default intent is "trace the lineage" — foundations, evolution, current state — not applications or a generic `survey`.

### Step 2: Author the RUBRIC (via `think_tool`)

Emit a structured block before any search. It persists across rounds and every later step references it.

```
RUBRIC for "&amp;lt;user query verbatim&amp;gt;"
Branch: LIST | ITERATIVE
Criteria (2–4, atomic; mark each [core] or [secondary]):
  C1 [core]     &amp;lt;what the paper MUST do/be — one sentence&amp;gt;
  C2 [core]     &amp;lt;...&amp;gt;
  C3 [secondary] &amp;lt;...&amp;gt;
Named entities to preserve verbatim: [&amp;lt;ent1&amp;gt;, &amp;lt;ent2&amp;gt;, ...]
Angle tags (3–5 sub-topic axes): [&amp;lt;tag1&amp;gt;, &amp;lt;tag2&amp;gt;, &amp;lt;tag3&amp;gt;]
Recency signal: [none | recency cue — defined in Step 3]
Disqualifiers: [&amp;lt;auto-reject if abstract shows this&amp;gt;]
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

**Probe (prerequisite — NOT counted in the 3 rounds, 2 parallel queries):** establish a comprehensive understanding of the need and lift named entities / angle gaps.</message>
<message type="ai">
  <content><reasoning>**Reading the tutorial**</reasoning></content>
  <tool_call id="call_5842b2744ef649e4b812c9406744e94c" name="read_file">{"file_path": "/work/literature/2107.07511.txt", "limit": 270, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-270 of 2462 | next offset 270 @@
=== PDF PAGE 1 ===
A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantiﬁcation
Anastasios N. Angelopoulos and Stephen Bates
December 8, 2022
Abstract
Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-
tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-
tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty
sets/intervals for the predictions of such models. Critically, the sets are valid in a distribution-free sense:
they possess explicit, non-asymptotic guarantees even without distributional assumptions or model as-
sumptions. One can use conformal prediction with any pre-trained model, such as a neural network, to
produce sets that are guaranteed to contain the ground truth with a user-speciﬁed probability, such as
90%. It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the
ﬁelds of computer vision, natural language processing, deep reinforcement learning, and so on.
This hands-on introduction is aimed to provide the reader a working understanding of conformal
prediction and related distribution-free uncertainty quantiﬁcation techniques with one self-contained
document. We lead the reader through practical theory for and examples of conformal prediction and
describe its extensions to complex machine learning tasks involving structured outputs, distribution
shift, time-series, outliers, models that abstain, and more. Throughout, there are many explanatory
illustrations, examples, and code samples in Python. With each code sample comes a Jupyter notebook
implementing the method on a real-data example; the notebooks can be accessed and easily run by
clicking on the following icons:
 .
1
arXiv:2107.07511v6  [cs.LG]  7 Dec 2022

=== PDF PAGE 2 ===
Contents
1 Conformal Prediction 4
1.1 Instructions for Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 Examples of Conformal Procedures 6
2.1 Classiﬁcation with Adaptive Prediction Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.2 Conformalized Quantile Regression . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.3 Conformalizing Scalar Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.1 The Estimated Standard Deviation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.2 Other 1-D Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.4 Conformalizing Bayes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Evaluating Conformal Prediction 11
3.1 Evaluating Adaptivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 The Eﬀect of the Size of the Calibration Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
3.3 Checking for Correct Coverage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
4 Extensions of Conformal Prediction 16
4.1 Group-Balanced Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Class-Conditional Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Conformal Risk Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Outlier Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
4.5 Conformal Prediction Under Covariate Shift . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
4.6 Conformal Prediction Under Distribution Drift . . . . . . . . . . . . . . . . . . . . . . . . . . 21
5 Worked Examples 23
5.1 Multilabel Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.2 Tumor Segmentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.3 Weather Prediction with Time-Series Distribution Shift . . . . . . . . . . . . . . . . . . . . . 24
5.4 Toxic Online Comment Identiﬁcation via Outlier Detection . . . . . . . . . . . . . . . . . . . 25
5.5 Selective Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
6 Full conformal prediction 27
6.1 Full Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.2 Cross-Conformal Prediction, CV+, and Jackknife+ . . . . . . . . . . . . . . . . . . . . . . . . 28
7 Historical Notes on Conformal Prediction 28
A Distribution-Free Control of General Risks 39
A.1 Instructions for Learn then Test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
2

=== PDF PAGE 3 ===
A.1.1 Crash Course on Generating p-values . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
A.1.2 Crash Course on Familywise-Error Rate Algorithms . . . . . . . . . . . . . . . . . . . 44
B Examples of Distribution-Free Risk Control 45
B.1 Multi-label Classiﬁcation with FDR Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
B.2 Simultaneous Guarantees on OOD Detection and Coverage . . . . . . . . . . . . . . . . . . . 46
C Concentration Properties of the Empirical Coverage 49
D Theorem and Proof: Coverage Property of Conformal Prediction 50
3

=== PDF PAGE 4 ===
Figure 1: Prediction set examples on Imagenet. We show three progressively more diﬃcult examples
of the class fox squirrel and the prediction sets (i.e., C(Xtest)) generated by conformal prediction.
1 Conformal Prediction
Conformal prediction [1–3] (a.k.a. conformal inference) is a straightforward way to generate prediction sets
for any model. We will introduce it with a short, pragmatic image classiﬁcation example, and follow up in
later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows.
First, we begin with a ﬁtted predicted model (such as a neural network classiﬁer) which we will call ˆf. Then,
we will create prediction sets (a set of possible labels) for this classiﬁer using a small amount of additional
calibration data—we will sometimes call this the calibration step.
Formally, suppose we have images as input and they each contain one of K classes. We begin with
a classiﬁer that outputs estimated probabilities (softmax scores) for each class: ˆf(x)∈ [0, 1]K. Then, we
reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training,
(X1,Y 1),..., (Xn,Yn), for use as calibration data. Using ˆf and the calibration data, we seek to construct a
prediction set of possible labels C(Xtest)⊂{ 1,...,K } that is valid in the following sense:
1−α≤ P(Ytest∈C (Xtest))≤ 1−α + 1n + 1, (1)
where (Xtest,Y test) is a fresh test point from the same distribution, and α∈ [0, 1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1 −α; we call
this property marginal coverage, since the probability is marginal (averaged) over the randomness in the
calibration and test points. See Figure 1 for examples of prediction sets on the Imagenet dataset.
To constructC from ˆf and the calibration data, we will perform a simple calibration step that requires
only a few lines of code; see the right panel of Figure 2. We now describe the calibration step in more detail,
introducing some terms that will be helpful later on. First, we set the conformal scoresi = 1− ˆf(Xi)Yi to be
one minus the softmax output of the true class. The score is high when the softmax output of the true class
is low, i.e., when the model is badly wrong. Next comes the critical step: deﬁne ˆq to be the⌈(n+1)(1−α)⌉/n
empirical quantile of s1,...,s n, where⌈·⌉ is the ceiling function (ˆq is essentially the 1−α quantile, but with
a small correction). Finally, for a new test data point (where Xtest is known but Ytest is not), create a
prediction setC(Xtest) ={y : ˆf(Xtest)y≥ 1− ˆq} that includes all classes with a high enough softmax output
(see Figure 2). Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy (1), no matter
what (possibly incorrect) model is used or what the (unknown) distribution of the data is.
true class
class
softmax output
#
scores,       class
softmax output
(1) compute scores
on holdout data
(2) get quantile (3) construct
prediction set
# 1: get conformal scores. n = calib_Y.shape[0]
cal_smx = model(calib_X).softmax(dim=1).numpy()
cal_scores = 1-cal_smx[np.arange(n),cal_labels]
# 2: get adjusted quantile
q_level = np.ceil((n+1)*(1-alpha))/n
qhat = np.quantile(cal_scores, q_level, method='higher')
val_smx = model(val_X).softmax(dim=1).numpy()
prediction_sets = val_smx &gt;= (1-qhat) # 3: form prediction sets
Figure 2: Illustration of conformal prediction with matching Python code.
4

=== PDF PAGE 5 ===
Remarks
Let us think about the interpretation of C. The function C is set-valued—it takes in an image, and it
outputs a set of classes as in Figure 1. The model’s softmax outputs help to generate the set. This method
constructs a diﬀerent output set adaptively to each particular input . The sets become larger when the model
is uncertain or the image is intrinsically hard. This is a property we want, because the size of the set gives you
an indicator of the model’s certainty. Furthermore, C(Xtest) can be interpreted as a set of plausible classes
that the image Xtest could be assigned to. Finally, C is valid, meaning it satisﬁes (1). 1 These properties of
C translate naturally to other machine learning problems, like regression, as we will see.
With an eye towards generalization, let us review in detail what happened in our classiﬁcation problem.
To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the
jth entry of the softmax vector estimated P(Y = j| X = x), the probability of class j conditionally on
an input image x. However, we had no guarantee that the softmax outputs were any good; they may have
been arbitrarily overﬁt or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face
value, we used the holdout set to adjust for their deﬁciencies.
The holdout set contained n≈ 500 fresh data points that the model never saw during training, which
allowed us to get an honest appraisal of its performance. The adjustment involved computing conformal
scores, which grow when the model is uncertain, but are not valid prediction intervals on their own. In our
case, the conformal score was one minus the softmax output of the true class, but in general, the score can
be any function of x and y. We then took ˆq to be roughly the 1−α quantile of the scores. In this case, the
quantile had a simple interpretation—when setting α = 0.1, at least 90% of ground truth softmax outputs
are guaranteed to be above the level 1 − ˆq (we prove this rigorously in Appendix D). Taking advantage of
this fact, at test-time, we got the softmax outputs of a new image Xtest and collected all classes with outputs
above 1− ˆq into a prediction setC(Xtest). Since the softmax output of the new true class Ytest is guaranteed
to be above 1− ˆq with probability at least 90%, we ﬁnally got the guarantee in Eq. (1).
1.1 Instructions for Conformal Prediction
As we said during the summary, conformal prediction is not speciﬁc to softmax outputs or classiﬁcation
problems. In fact, conformal prediction can be seen as a method for taking any heuristic notion of
uncertainty from any model and converting it to a rigorous one (see the diagram below). Conformal pre-
diction does not care if the underlying prediction problem is discrete/continuous or classiﬁcation/regression.
Heuristic
uncertainty
(per input)
Rigorous
uncertainty
(per input)
conformal
prediction
We next outline conformal prediction for a general input x and output y (not necessarily discrete).
1. Identify a heuristic notion of uncertainty using the pre-trained model.
2. Deﬁne the score function s(x,y )∈ R. (Larger scores encode worse agreement between x and y.)
3. Compute ˆq as the ⌈(n+1)(1−α)⌉n quantile of the calibration scores s1 =s(X1,Y 1),...,s n =s(Xn,Yn).
4. Use this quantile to form the prediction sets for new examples:
C(Xtest) ={y :s(Xtest,y )≤ ˆq}. (2)
As before, these sets satisfy the validity property in (1), for any (possibly uninformative) score function and
(possibly unknown) distribution of the data. We formally state the coverage guarantee next.
1Due to the discreteness of Y , a small modiﬁcation involving tie-breaking is needed to additionally satisfy the upper bound
(see [4] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
5

=== PDF PAGE 6 ===
Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [5]). Suppose (Xi,Yi)i=1,...,n
and (Xtest,Y test) are i.i.d. and deﬁne ˆq as in step 3 above andC(Xtest) as in step 4 above. Then the following
holds:
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
See Appendix D for a proof and a statement that includes the upper bound in (1). We note that the
above is only a special case of conformal prediction, called split conformal prediction . This is the most
widely-used version of conformal prediction, and it will be our primary focus. To complete the picture, we
describe conformal prediction in full generality later in Section 6 and give an overview of the literature in
Section 7.
Choice of score function
Upon ﬁrst glance, this seems too good to be true, and a skeptical reader might ask the following question:
How is it possible to construct a statistically valid prediction set even if the heuristic notion of uncertainty
of the underlying model is arbitrarily bad?
Let’s give some intuition to supplement the mathematical understanding from the proof in Appendix D.
Roughly, if the scoressi correctly rank the inputs from lowest to highest magnitude of model error, then the
resulting sets will be smaller for easy inputs and bigger for hard ones. If the scores are bad, in the sense that
they do not approximate this ranking, then the sets will be useless. For example, if the scores are random
noise, then the sets will contain a random sample of the label space, where that random sample is large
enough to provide valid marginal coverage. This illustrates an important underlying fact about conformal
prediction: although the guarantee always holds, the usefulness of the prediction sets is primarily
determined by the score function. This should be no surprise—the score function incorporates almost all
the information we know about our problem and data, including the underlying model itself. For example, the
main diﬀerence between applying conformal prediction on classiﬁcation problems versus regression problems
is the choice of score. There are also many possible score functions for a single underlying model, which have
diﬀerent properties. Therefore, constructing the right score function is an important engineering choice. We
will next show a few examples of good score functions.
2 Examples of Conformal Procedures
In this section we give examples of conformal prediction applied in many settings, with the goal of providing
the reader a bank of techniques to practically deploy. Note that we will focus only on one-dimensional Y in
this section, and smaller conformal scores will correspond to more model conﬁdence (such scores are called
nonconformity scores). Richer settings, such as high-dimensional Y , complicated (or multiple) notions of
error, or where diﬀerent mistakes cost diﬀerent amounts, often require the language of risk control, outlined
in Section A.
2.1 Classiﬁcation with Adaptive Prediction Sets
Let’s begin our sequence of examples with an improvement to the classiﬁcation example in Section 1.
The previous method produces prediction sets with the smallest average size [6], but it tends to undercover
hard subgroups and overcover easy ones. Here we develop a diﬀerent method called adaptive prediction sets
(APS) that avoids this problem. We will follow [7] and [4].
As motivation for this new procedure, note that if the softmax outputs ˆf(Xtest) were a perfect model
of Ytest|Xtest, we would greedily include the top-scoring classes until their total mass just exceeded 1 −α.
6

=== PDF PAGE 7 ===
# Get scores. calib_X.shape[0] == calib_Y.shape[0] == n
cal_pi = cal_smx.argsort(1)[:,::-1]; cal_srt = np.take_along_axis(cal_smx,cal_pi,axis=1).cumsum(axis=1)
cal_scores = np.take_along_axis(cal_srt,cal_pi.argsort(axis=1),axis=1)[range(n),cal_labels]
# Get the score quantile
qhat = np.quantile(cal_scores, np.ceil((n+1)*(1-alpha))/n, interpolation='higher')
# Deploy (output=list of length n, each element is tensor of classes)
val_pi = val_smx.argsort(1)[:,::-1]; val_srt = np.take_along_axis(val_smx,val_pi,axis=1).cumsum(axis=1)
prediction_sets = np.take_along_axis(val_srt &lt;= qhat,val_pi.argsort(axis=1),axis=1)
Figure 3: Python code for adaptive prediction sets.
Formally, we can describe this oracle algorithm as
{π1(x),...,π k(x)} , where k = sup


k′ :
k′∑
j=1
ˆf(Xtest)πj(x) &lt; 1−α


 + 1,
and π(x) is the permutation of {1,...,K} that sorts ˆf(Xtest) from most likely to least likely. In practice,
however, this procedure fails to provide coverage, since ˆf(Xtest) is not perfect; it only provides us a heuristic
notion of uncertainty. Therefore, we will use conformal prediction to turn this into a rigorous notion of
uncertainty.
To proceed, we deﬁne a score function inspired by the oracle algorithm:
s(x,y ) =
k∑
j=1
ˆf(x)πj(x), where y =πk(x).
In other words, we greedily include classes in our set until we reach the true label, then we stop. Unlike the
score from Section 1, this one utilizes the softmax outputs of all classes, not just the true class.
The next step, as in all conformal procedures, is to set ˆ q = Quantile(s1,...,s n ; ⌈(n+1)(1−α)⌉n ). Having
done so, we will form the prediction set {y :s(x,y )≤ ˆq}, modiﬁed slightly to avoid zero-size sets:
C(x) ={π1(x),...,π k(x)} , where k = sup


k′ :
k′∑
j=1
ˆf(x)πj(x) &lt; ˆq


 + 1. (3)
Figure 3 shows Python code to implement this method. As usual, these uncertainty sets (with tie-breaking)
satisfy (1). See [4] for details and signiﬁcant practical improvements, which we implemented here:
 .
fox squirrel softmax</message>
<message type="ai">
  <content><reasoning>**Fetching official resources**</reasoning></content>
  <tool_call id="call_fe3d995289304ca5bcf63553c8b5c6ee" name="read_file">{"file_path": "/work/access_log.json", "limit": 150, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-47 of 47 @@
[
  {
    "requested_url": "https://arxiv.org/pdf/2107.07511",
    "final_url": "https://arxiv.org/pdf/2107.07511",
    "status": 200,
    "bytes": 5360733,
    "sha256": "c69aa191d8363c25b36685db4adb7e6980e55ee39892fd3626206c16e1e0efa1",
    "path": "./literature/2107.07511.pdf",
    "utc": "2026-11-02T18:05:39.099243+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/1904.06019",
    "final_url": "https://arxiv.org/pdf/1904.06019",
    "status": 200,
    "bytes": 423685,
    "sha256": "d80dba944a136e075bbfe281009152ce42041e0a455f68f73684ace83cfc3fed",
    "path": "./literature/1904.06019.pdf",
    "utc": "2026-11-02T18:05:39.590307+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2009.14193",
    "final_url": "https://arxiv.org/pdf/2009.14193",
    "status": 200,
    "bytes": 1339455,
    "sha256": "ca78c0ab20b95151db93e75f0fed5ef88faf180023b80d36c9e671034bc43f85",
    "path": "./literature/2009.14193.pdf",
    "utc": "2026-11-02T18:05:40.183158+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2402.10723",
    "final_url": "https://arxiv.org/pdf/2402.10723",
    "status": 200,
    "bytes": 1756530,
    "sha256": "ac4a42679abdeaff5cfbe6bb316ac60373dfd9eefc97afc9ce94eb4899c68d09",
    "path": "./literature/2402.10723.pdf",
    "utc": "2026-11-02T18:05:40.831276+00:00"
  },
  {
    "requested_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "final_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "status": 200,
    "bytes": 16961,
    "sha256": "dc54ed42f6d93f1f1debb1d044bf45a48b2e65cbc310f914f683f3b443061f07",
    "path": "./template/repo_contents.json",
    "utc": "2026-11-02T18:05:41.442059+00:00"
  }
]</message>
<message type="ai">
  <tool_call id="call_94a0ba4d96094ee7a8ca4646b9949a46" name="execute">{"command": "python -c 'import urllib.request,json,hashlib,datetime,pathlib,zipfile; root=pathlib.Path(\"/work\"); log=json.loads((root/\"access_log.json\").read_text()); jobs=[(\"https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md\",\"template/README.md\"),(\"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027\",\"template/iclr2027_contents.json\"),(\"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip\",\"template/iclr2027.zip\")]; exec(\"for url,rel in jobs:\\n req=urllib.request.Request(url,headers={\\\"User-Agent\\\":\\\"restricted-primary-source-research/1.0\\\"})\\n with urllib.request.urlopen(req,timeout=45) as res:\\n  data=res.read(); entry={\\\"requested_url\\\":url,\\\"final_url\\\":res.url,\\\"status\\\":res.status,\\\"bytes\\\":len(data),\\\"sha256\\\":hashlib.sha256(data).hexdigest(),\\\"path\\\":str(root/rel),\\\"utc\\\":datetime.datetime.now(datetime.timezone.utc).isoformat()}\\n (root/rel).write_bytes(data); log.append(entry); (root/\\\"access_log.json\\\").write_text(json.dumps(log,indent=2)); print(entry)\\n\"); z=zipfile.ZipFile(root/\"template/iclr2027.zip\"); print(z.namelist()); z.extractall(root/\"template\")'", "timeout": 180}</tool_call>
</message>
<message type="tool">{'requested_url': 'https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md', 'final_url': 'https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md', 'status': 200, 'bytes': 52, 'sha256': '69fd79b87c37393ceb4e58ba897a26578e1384d890a09dce539aef6baaf455c1', 'path': '/work/template/README.md', 'utc': '2026-11-02T18:09:06.627454+00:00'}
{'requested_url': 'https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027', 'final_url': 'https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027', 'status': 200, 'bytes': 6179, 'sha256': '88c68c47145b42b117fbcd853ca828ecbe69eb2f6492d6ac5808f5921d49a9bf', 'path': '/work/template/iclr2027_contents.json', 'utc': '2026-11-02T18:09:07.128471+00:00'}
{'requested_url': 'https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip', 'final_url': 'https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip', 'status': 200, 'bytes': 39348, 'sha256': '0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e', 'path': '/work/template/iclr2027.zip', 'utc': '2026-11-02T18:09:07.593380+00:00'}
['iclr2027/', 'iclr2027/iclr2027_conference.bib', 'iclr2027/math_commands.tex', 'iclr2027/fancyhdr.sty', 'iclr2027/iclr2027_conference.bst', 'iclr2027/iclr2027_conference.tex', 'iclr2027/natbib.sty', 'iclr2027/iclr2027_conference.sty']

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_9725a0d3c9f84b8a9c851a7d433a37e8" name="read_file">{"file_path": "/work/literature/1904.06019.txt", "limit": 320, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-320 of 2190 | next offset 320 @@
=== PDF PAGE 1 ===
Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the training and test data are not drawn from the same distribution.
We begin by reviewing the basics of conformal prediction, in this section. In Section 2, we describe an extension of
conformal prediction to the setting of covariate shift, and give supporting empirical results. In Section 3, we cover the
mathematical details behind our conformal extension. We conclude in Section 4, and discuss several other possible
applications of our new conformal methodology.
1.1 Quantile lemma
Before explaining the basic ideas behind conformal inference (i.e., conformal prediction, we will use these two terms
interchangeably), we introduce some notation. We denote by Quantile(β;F ) the levelβ quantile of a distributionF ,
i.e., forZ∼F ,
Quantile(β;F ) = inf
{
z : P{Z≤z}≥ β
}
.
In our use of quantiles, we will allow for distributionsF on the augmented real line, R∪{∞} . For valuesv1,...,v n,
we writev1:n ={v1,...,v n} to denote their multiset. Note that this is unordered, and allows for multiple instances the
same element; thus in the present case, ifvi =vj fori⁄=j, then this value appears twice inv1:n. To denote quantiles
of the empirical distribution of the valuesv1,...,v n, we abbreviate
Quantile(β;v1:n) = Quantile
(
β; 1n
n∑
i=1
δvi
)
,
1
arXiv:1904.06019v3  [stat.ME]  6 Jul 2020

=== PDF PAGE 2 ===
whereδa denotes a point mass ata (i.e., the distribution that places all mass at the valuea). The next result is a simple
but key component underlying conformal prediction.
Lemma 1. IfV1,...,V n+1 are exchangeable random variables, then for anyβ∈ (0, 1), we have
P
{
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)}
≥β.
Furthermore, if ties betweenV1,...,V n+1 occur with probability zero, then the above probability is upper bound by
β + 1/(n + 1).
Proof. Consider the following useful fact about quantiles of a discrete distributionF , with support pointsa1,...,a k∈
R: denotingq = Quantile(β;F ), if we reassign the pointsai &gt;q to arbitrary values strictly larger thanq, yielding a
new distribution ~F , then the levelβ quantile remains unchanged, Quantile(β;F ) = Quantile(β;~F ). Using this fact,
Vn+1 &gt; Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1 &gt; Quantile
(
β;V1:(n+1)
)
,
or equivalently,
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1≤ Quantile
(
β;V1:(n+1)
)
. (2)
Moreover, it is straightforward to check that
Vn+1≤ Quantile
(
β;V1:(n+1)
)
⇐⇒ Vn+1 is among the⌈β(n + 1)⌉ smallest ofV1,...,V n+1.
By exchangeability, the latter event occurs with probability at least⌈β(n + 1)⌉/(n + 1)≥β, which proves the lower
bound; when there are almost surely no ties, it holds with probability exactly⌈β(n + 1)⌉/(n + 1)≤β + 1/(n + 1),
which proves the upper bound.
1.2 Conformal prediction
We now return to the regression setting. DenoteZi = (Xi,Yi),i = 1,...,n , andZ1:n ={Z1,...,Z n}. We will use
the abbreviationZ−i =Z1:n\{Zi}. In what follows, we describe the construction of a prediction band satisfying (1),
using conformal inference, due to V ovk et al. (2005). We ﬁrst choose a score functionS, whose arguments consist of a
point (x,y ), and a multisetZ.1 Informally, a low value ofS((x,y ),Z ) indicates that the point (x,y ) “conforms” toZ,
whereas a high value indicates that (x,y ) is atypical relative to the points inZ. For example, we might choose to deﬁne
S by
S
(
(x,y ),Z
)
=|y−ˆµ(x)|, (3)
whereˆµ : Rd→ R is a regression function that was ﬁtted by running an algorithmA on (x,y ) andZ.
Next, at eachx∈ Rd, we deﬁne the conformal prediction interval2 ˆCn(x) by repeating the following procedure for
eachy∈ R. We calculate the nonconformity scores
V (x,y)i =S(Zi,Z−i∪{ (x,y )}), i= 1,...,n, and V (x,y)n+1 =S((x,y ),Z 1:n), (4)
and includey in our prediction interval ˆCn(x) if
V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞}),
whereV (x,y)1:n ={V (x,y)1 ,...,V (x,y)n }. Importantly, the symmetry in the construction of the nonconformity scores (4)
guarantees exact coverage in ﬁnite samples. The next theorem summarizes this coverage result. The lower bound is a
standard result in conformal inference, due to V ovk et al. (2005); the upper bound, as far as we know, was ﬁrst pointed
out by Lei et al. (2018).
1We emphasize that by deﬁningZ to be a multiset, we are treating its points as unordered. Hence, to be perfectly explicit, the score function S
cannot accept the points inZ in any particular order, and it must take them in as unordered. The same is true of the base algorithm A used to deﬁne
the ﬁtted regression function ˆµ, in the choice of absolute residual score function (3).
2For convenience, throughout, we will refer to ˆCn(x) as an “interval”, even though this may actually be a union of multiple nonoverlapping
intervals. Similarly, for simplicity, we will refer to ˆCn as a “band”.
2

=== PDF PAGE 3 ===
Theorem 1 (V ovk et al. 2005; Lei et al. 2018). Assume that (Xi,Yi)∈ Rd× R,i = 1,...,n + 1 are exchangeable.
For any score functionS, and anyα∈ (0, 1), deﬁne the conformal band (based on the ﬁrstn samples) atx∈ Rd by
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞})}, (5)
whereV (x,y)i ,i = 1,...,n + 1 are as deﬁned in (4). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Furthermore, if ties betweenV (Xn+1,Yn+1)1 ,...,V (Xn+1,Yn+1)n+1 occur with probability zero, then this probability is upper
bounded by 1−α + 1/(n + 1).
Proof. To lighten notation, abbreviateVi =V (Xn+1,Yn+1)i ,i = 1,...,n + 1. Observe
Yn+1∈ ˆCn(Xn+1) ⇐⇒ Vn+1≤ Quantile(1−α;V1:n∪{∞}).
By the symmetric construction of the nonconformity scores in (4),
(Z1,...,Z n+1)
d
= (Zσ(1),...,Z σ(n+1)) ⇐⇒ (V1,...,V n+1)
d
= (Vσ(1),...,V σ(n+1)),
for any permutationσ of the numbers 1,...,n + 1. Therefore, asZ1,...,Z n+1 are exchangeable, so areV1,...,V n+1,
and applying Lemma 1 gives the result.
Remark 1. Theorem 1 is stated for exchangeable samples (Xi,Yi),i = 1,...,n + 1, which is (signiﬁcantly) weaker
than assuming i.i.d. samples. As we will see in what follows, it is furthermore possible to relax the exchangeability
assumption, under an appropriate modiﬁcation to the conformal procedure.
Remark 2. If we use an appropriate random tie-breaking rule (to determine the rank ofVn+1 amongV1,...,V n+1),
then the upper bounds in Lemma 1 and Theorem 1 hold in general (without assuming there are no ties almost surely).
The result in Theorem 1, albeit very simple to prove, is quite remarkable. It gives us a recipe for distribution-free
prediction intervals, with nearly exact coverage, starting from an arbitrary score functionS; e.g., absolute residuals
with respect to a ﬁtted regression function from any base algorithmA, as in (3). For more discussion of conformal
prediction, its properties, and its variants, we refer to V ovk et al. (2005); Lei et al. (2018) and references therein.
2 Covariate shift
In this paper, we are concerned with settings in which the data (Xi,Yi),i = 1,...,n + 1 are no longer exchangeable.
Our primary focus will be a setting in which we observe data according to
(Xi,Yi)
i.i.d.
∼ P =PX×PY|X, i= 1,...,n,
(Xn+1,Yn+1)∼ ~P = ~PX×PY|X, independently. (6)
Notice that the conditional distribution ofY|X is assumed to be the same for both the training and test data. Such a
setting is often called covariate shift (e.g., see Shimodaira 2000; Quinonero-Candela et al. 2009; see also Remark 4
below for more discussion of this literature). The key realization is the following: if we know the ratio of test to training
covariate likelihoods, d~PX/dPX, then we can still perform a modiﬁed of version conformal inference, using a quantile
of a suitably weighted empirical distribution of nonconformity scores. The next subsection gives the details; following
this, we describe a more computationally efﬁcient conformal procedure, and give an empirical demonstration.
2.1 Weighted conformal prediction
In conformal prediction, we compare the value of a nonconformity score at a test point to the empirical distribution of
nonconformity scores at the training points. In the covariate shift case, where the covariate distributions PX,~PX in
our training and test sets differ, we will now weight each nonconformity scoreV (x,y)i (which measures how wellZi =
3

=== PDF PAGE 4 ===
(Xi,Yi) conforms to the other points) by a probability proportional to the likelihood ratiow(Xi) = d~PX (Xi)/dPX (Xi).
Therefore, we will no longer be interested in the empirical distribution
1
n + 1
n∑
i=1
δV (x,y)i + 1n + 1δ∞,
as in Theorem 1, but rather, a weighted version
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞,
where the weights are deﬁned by
pwi (x) = w(Xi)∑n
j=1w(Xj) +w(x), i= 1,...,n, and pwn+1(x) = w(x)∑nj=1w(Xj) +w(x). (7)
Due this careful weighting, draws from the discrete distribution in the second to last display resemble nonconformity
scores computed on the test population, and thus, they “look exchangeable” with the nonconformity score at our test
point. Our main result below formalizes these claims.
Corollary 1. Assume data from the model(6). Assume that ~PX is absolutely continuous with respect toPX, and denote
w = d~PX/dPX. For any score functionS, and anyα∈ (0, 1), deﬁne forx∈ Rd,
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile
(
1−α;
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞
)}
, (8)
whereV (x,y)i ,i = 1,...,n + 1 are as in (4), andpwi (x),i = 1,...,n + 1 are as in (7). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Corollary 1 is a special case of a more general result that we present later in Theorem 2, which extends conformal
inference to a setting in which the data are what we call weighted exchangeable. The proof is given in Section 3.5.
Remark 3. The same result as in Corollary 1 holds ifw∝ d~PX/dPX, i.e., with an unknown normalization constant,
because this normalization constant cancels out in the calculation of probabilities in (7).
Remark 4. Though the basic premise of covariate shift—and certainly the techniques employed in addressing it—are
related to much older ideas in statistics, the speciﬁc setup (6) has recently generated great interest in machine learning:
e.g., see Sugiyama and Muller (2005); Sugiyama et al. (2007); Quinonero-Candela et al. (2009); Agarwal et al. (2011);
Wen et al. (2014); Reddi et al. (2015); Chen et al. (2016) and references therein). The focus is usually on correcting
estimators, model evaluation, or model selection approaches to account for covariate shift. Correcting distribution-free
prediction intervals, as we examine in this work, is (as far as we know) a new contribution. As one might expect, the
likelihood ratio d~PX/dPX, a key component of our conformal construction in Corollary 1, also plays a critical role in
much of the literature on covariate shift.
2.2 Weighted split conformal
In general, constructing a conformal prediction band can be computationally intensive, though this of course depends
on the choice of score function. Consider the use of absolute residuals as in (3). To compute the nonconformity scores
in (4), we must ﬁrst run our base algorithmA on the data setZ1:n∪{ (x,y )} to produce a ﬁtted regression functionˆµ,
and then calculate
V (x,y)i =|Yi−ˆµ(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−ˆµ(x)|.
As the formation of the conformal set in (5) (ordinary case) or (8) (covariate shift case) requires us to do this for each
x∈ Rd andy∈ R (which requires reﬁttingˆµ each time), this can clearly become computationally burdernsome.
A fast alternative, known as split conformal prediction (Papadopoulos et al., 2002; Lei et al., 2015), resolves this
issue by taking the score functionS to be deﬁned using absolute residuals with respect to a ﬁxed regression function,
4

=== PDF PAGE 5 ===
typically, one that has been trained on an preliminary data set. Denote by (X 01,Y 01 ),..., (X 0n0,Y 0n0 ) this preliminary
data set, used for ﬁtting the regression functionµ0, and consider the score function
S
(
(x,y ),Z
)
=|y−µ0(x)|.
Given data (X1,Y 1),..., (Xn,Yn), independent of (X 01,Y 01 ),..., (X 0n0,Y 0n0 ), we calculate
V (x,y)i =|Yi−µ0(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−µ0(x)|.
The conformal prediction interval (5), deﬁned at a pointx∈ Rd, reduces to
ˆCn(x) = µ0(x)± Quantile
(
1−α;
{
|Yi−µ0(Xi)|
}n
i=1∪{∞}
)
, (9)
and by Theorem 1 it has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ). This coverage result holds
because, when we treatµ0 as ﬁxed (meaning, condition on (X 01,Y 01 ),..., (X 0n0,Y 0n0 )), the scoresV (x,y)1 ,...,V (x,y)n+1
scores are exchangeable for (x,y ) = (Xn+1,Yn+1), as (X1,Y 1),..., (Xn+1,Yn+1) are.
As split conformal prediction can be seen as a special case of conformal prediction, in which the regression function
µ0 is treated as ﬁxed, Corollary 1 also applies to the split scenario, and guarantees that the band deﬁned forx∈ Rd by
ˆCn(x) = µ0(x)± Quantile
(
1−α;
n∑
i=1
pwi (x)δ|Yi−µ0(Xi)| +pwn+1(x)δ∞
)
, (10)
where the probabilities are as in (7), has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ).
2.3 Airfoil data example
We demonstrate the use of conformal prediction in the covariate shift setting in an empirical example. We consider the
airfoil data set from the UCI Machine Learning Repository (Dua and Graff, 2019), which hasN = 1503 observations of
a responseY (scaled sound pressure level of NASA airfoils), and a covariateX withd = 5 dimensions (log frequency,
angle of attack, chord length, free-stream velocity, and suction side log displacement thickness). For efﬁciency, we use
the split conformal prediction methods in (9) and (10) for the unweighted and weighted case, respectively. R code to
reproduce these simulation results can be found at http://www.github.com/ryantibs/conformal/.
Creating training data, test data, and covariate shift. We repeated an experiment for 5000 trials, where for each
trial we randomly partitioned the data{(Xi,Yi)}Ni=1 into three setsDpre,D train,D test, and also constructed a covariate
shift test setDshift, which have the following roles.
• Dpre, containing 25% of the data, is used to preﬁt a regression functionµ0 via linear regression, to be used in
constructing split conformal intervals.
• Dtrain, containing 25% of the data, is our training set, i.e., (Xi,Yi),i = 1,...,n , used to compute the residual
quantiles in the construction of the split conformal prediction intervals (9) and (10).
• Dtest, containing 50% of the data, is our test set (as these data points are exchangeable with those inDtrain, there
is no covariate shift in this test set).
• Dshift is a second test set, constructed to simulate covariate shift, by sampling 25% of the points fromDtest with
replacement, with probabilities proportional to
w(x) = exp(xTβ), where β = (−1, 0, 0, 0, 1). (11)
As the original data pointsDtrain∪Dtest can be seen as draws from the same underlying distribution, we can view
w(x) as the likelihood ratio of covariate distributions between the test setDshift and training setDtrain. Note that the test
covariate distribution~PX, which satisﬁes d~PX∝ exp(xTβ)dPX as we have deﬁned it here, is called an exponential
tilting of the training covariate distributionPX. Figure 1 visualizes the effect of this exponential tilting, in the airfoil
data set, with our choiceβ = (−1, 0, 0, 0, 1). Only the 1st and 5th dimensions of the covariate distribution are tilted;
the bottom row of Figure 1 plots the marginal densities of the 1st and 5th covariates (estimated via kernel smoothing)
before and after the tilt. The top row plots the response versus the 1st and 5th covariates, simply to highlight the fact
that there is heteroskedasticity, and thus we might expect the shift in the covariate distribution to have some effect on
the validity of the ordinary conformal prediction intervals.
5

=== PDF PAGE 6 ===
●
●
●●
●
●
●
●
●●● ●
●
●
●
●
●</message>
<message type="ai">
  <tool_call id="call_3f6c35736a5444cfaf191e22507b0caf" name="read_file">{"file_path": "/work/literature/2009.14193.txt", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-300 of 898 | next offset 300 @@
=== PDF PAGE 1 ===
UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in computer vision.
Formally, for a discrete responseY ∈Y ={1,...,K } and a feature vectorX∈ Rd, we desire an
uncertainty set function,C(X), mapping a feature vector to a subset of{1,...,K } such that
P (Y ∈C (X))≥ 1−α, (1)
for a pre-speciﬁed conﬁdence levelα such as 10%. Conformal predictors like our method can mod-
ify any black-box classiﬁer to output predictive sets that are rigorously guaranteed to satisfy the
∗equal contribution
†Project website here.
1
arXiv:2009.14193v5  [cs.CV]  3 Sep 2022

=== PDF PAGE 2 ===
Figure 1: Prediction set examples on Imagenet. We show three examples of the class fox squirrel and
the 95% prediction sets generated by RAPS to illustrate how the size of the set changes as a function of the
difﬁculty of a test-time image.
desired coverage property shown in Eq. (1). For evaluations, we focus on Imagenet classiﬁcation
using convolutional neural networks (CNNs) as the base classiﬁers, since this is a particularly chal-
lenging testbed. In this setting,X would be the image andY would be the class label. Note that the
guarantee in Eq. (1) is marginal overX andY —it holds on average, not for a particular imageX.
A ﬁrst approach toward this goal might be to assemble the set by including classes from highest to
lowest probability (e.g., after Platt scaling and a softmax function; see Platt et al., 1999; Guo et al.,
2017) until their sum just exceeds the threshold 1−α. We call this strategy naive and formulate
it precisely in Algorithm 1. There are two problems with naive: ﬁrst, the probabilities output by
CNNs are known to be incorrect (Nixon et al., 2019), so the sets from naive do not achieve cov-
erage. Second, image classiﬁcation models’ tail probabilities are often badly miscalibrated, leading
to large sets that do not faithfully articulate the uncertainty of the model; see Section 2.3. Moreover,
smaller sets that achieve the same coverage level can be generated with other methods.
The coverage problem can be solved by picking a new threshold using holdout samples. For exam-
ple, withα =10%, if choosing sets that contain 93% estimated probability achieves 90% coverage
on the holdout set, we use the 93% cutoff instead. We refer to this algorithm, introduced in Ro-
mano et al. (2020), as Adaptive Prediction Sets (APS). The APS procedure provides coverage but
still produces large sets. To ﬁx this, we introduce a regularization technique that tempers the in-
ﬂuence of these noisy estimates, leading to smaller, more stable sets. We describe our proposed
algorithm, Regularized Adaptive Prediction Sets (RAPS), in Algorithms 2 and 3 (with APS as a
special case). As we will see in Section 2, both APS and RAPS are always guaranteed to satisfy
Eq. (1)—regardless of model and dataset. Furthermore, we show that RAPS is guaranteed to have
better performance than choosing a ﬁxed-size set. Both methods impose negligible computational
requirements in both training and evaluation, and output useful estimates of the model’s uncertainty
on a new image given, say, 1000 held-out examples.
In Section 3 we conduct the most extensive evaluation of conformal prediction in deep learning to
date on Imagenet and Imagenet-V2. We ﬁnd that RAPS sets always have smaller average size than
naive and APSsets. For example, using a ResNeXt-101, naive does not achieve coverage, while
APS and RAPS achieve it almost exactly. However,APS sets have an average size of 19, whileRAPS
sets have an average size of 2 atα = 10% (Figure 2 and Table 1). We will provide an accompanying
codebase that implements our method as a wrapper for any PyTorch classiﬁer, along with code to
exactly reproduce all of our experiments.
1.1 R ELATED WORK
Reliably estimating predictive uncertainty for neural networks is an unsolved problem. Historically,
the standard approach has been to train a Bayesian neural network to learn a distribution over net-
work weights (Quinonero-Candela et al., 2005; MacKay, 1992; Neal, 2012; Kuleshov et al., 2018;
Gal, 2016). This approach requires computational and algorithmic modiﬁcations; other approaches
avoid these via ensembles (Lakshminarayanan et al., 2017; Jiang et al., 2018) or approximations of
Bayesian inference (Riquelme et al., 2018; Sensoy et al., 2018). These methods also have major
practical limitations; for example, ensembling requires training many copies of a neural network ad-
versarially. Therefore, the most widely used strategy is ad-hoctraditional calibration of the softmax
scores with Platt scaling (Platt et al., 1999; Guo et al., 2017; Nixon et al., 2019).
2

=== PDF PAGE 3 ===
0.9 0.95 0.99
desired coverage (1- )
0.85
0.90
0.95
1.00empirical coverage
Naive
APS
RAPS
0.9 0.95 0.99
desired coverage (1- )
0
20
40
60
80
100average size
Figure 2: Coverage and average set size on Imagenet for prediction sets from three methods.All methods
use a ResNet-152 as the base classiﬁer, and results are reported for 100 random splits of Imagenet-Val, each of
size 20K. See Section 3.1 for full details.
This work develops a method for uncertainty quantiﬁcation based onconformal prediction. Originat-
ing in the online learning literature, conformal prediction is an approach for generating predictive
sets that satisfy the coverage property in Eq. (1) (V ovk et al., 1999; 2005). We use a convenient
data-splitting version known as split conformal prediction that enables conformal prediction meth-
ods to be deployed for essentially any predictor (Papadopoulos et al., 2002; Lei et al., 2018). While
mechanically very different from traditional calibration as discussed above, we will refer to our
approach as conformal calibration to highlight that the two methodologies have overlapping but
different goals.
Conformal prediction is a general framework, not a speciﬁc algorithm—important design decisions
must be made to achieve the best performance for each context. To this end, Romano et al. (2020)
and Cauchois et al. (2020) introduce techniques aimed at achieving coverage that is similar across
regions of feature space, whereas ?Hechtlinger et al. (2018) and ? introduce techniques aimed at
achieving equal coverage for each class. While these methods have conceptual appeal, thus far
there has been limited empirical evaluation of this general approach for state-of-the-art CNNs. Con-
cretely, the only works that we are aware of that include some evaluation of conformal methods on
ImageNet—the gold standard for benchmarking computer vision methods—are Hechtlinger et al.
(2018), Park et al. (2019), Cauchois et al. (2020), and Messoudi et al. (2020), although in all four
cases further experiments are needed to more fully evaluate their operating characteristics for practi-
cal deployment. At the heart of conformal prediction is theconformal score: a measure of similarity
between labeled examples which is used to compare a new point to among those in a hold out set.
Our theoretical contribution can be summarized as a modiﬁcation of the conformal score from Ro-
mano et al. (2020) to have smaller, more stable sets. Lastly, there are alternative approaches to
returning prediction sets not based on conformal prediction (Pearce et al., 2018; Zhang et al., 2018).
These methods can be used as input to a conformal procedure to potentially improve performance,
but they do not have ﬁnite-sample coverage guarantees when used alone.
2 M ETHODS
In developing uncertainty set methods to improve upon naive, we are guided by three desiderata.
First and most importantly, the coverage desideratum says the sets must provide 1−α coverage, as
Algorithm 1 Naive Prediction Sets
Input: α, sorted scoress, associated permutation of classesI, booleanrand
1: procedure NAIVE (α,s,I,rand )
2: L← 1
3: while∑Li=1si &lt; 1−α do ⊿ Stop if 1−α probability exceeded
4: L←L + 1
5: ifrand then ⊿ Break ties randomly (explained in Appendix B)
6: U← Unif(0, 1)
7: V ← (∑Li=1si− (1−α))/sL
8: ifU≤V then
9: L←L− 1
10: return
{
I1,...,I L
}
Output: The 1−α prediction set,
{
I1,...,I L
}
3

=== PDF PAGE 4 ===
τ^ccal0
25%
50%
75%
1−α′
100%
τ: set size parameter
empirical coverage
(a) Conformal calibration
0.50.5
0.770.77
0.920.92
1.021.02
1.091.09 1.151.15
kreg τ^ccal
0.0
0.2
0.4
c d f b e a
class
penalized probability
penalty
probability (b) A RAPS prediction set
Figure 3: Visualizations of conformal calibration and RAPS sets. In the left panel, the y-axis shows the
empirical coverage on the conformal calibration set, and 1−α′ =⌈(n + 1)(1−α)⌉/n. In the right panel, the
printed numbers indicate the cumulative probability plus penalty mass. For the indicated value ˆτccal, the RAPS
prediction set is{c, d, f, b}.
discussed above. Secondly, the size desideratum says we want sets of small size, since these convey
more detailed information and may be more useful in practice. Lastly, the adaptiveness desidera-
tum says we want the sets to communicate instance-wise uncertainty: they should be smaller for
easy test-time examples than for hard ones; see Figure 1 for an illustration. Coverage and size
are obviously competing objectives, but size and adaptiveness are also often in tension. The size
desideratum seeks small sets, while the adaptiveness desideratum seeks larger sets when the classi-
ﬁer is uncertain. For example, always predicting a set of size ﬁve could achieve coverage, but it is
not adaptive. As noted above, both APSand RAPS achieve correct coverage, and we will show that
RAPS improves upon APS according to the other two desiderata.
We now turn to the speciﬁcs of our proposed method. We begin in Subsection 2.1 by describing an
abstract data-splitting procedure called conformal calibration that enables the near-automatic con-
struction of valid predictive sets (that is, sets satisfying Eq. (1)). Subsequently, in Subsection 2.2, we
provide a detailed presentation of our procedure, with commentary in Section 2.3. In Subsection 2.4
we discuss the optimality of our procedure, proving that it is at least as good as the procedure that
returns sets of a ﬁxed size, unlike alternative approaches.
2.1 C ONFORMAL CALIBRATION
We ﬁrst review a general technique for producing valid prediction sets, following the articulation
in Gupta et al. (2019). Consider a procedure that outputs a predictive set for each observation,
and further suppose that this procedure has a tuning parameter τ that controls the size of the sets.
(In RAPS, τ is the cumulative sum of the sorted, penalized classiﬁer scores.) We take a small
independent conformal calibration set of data, and then choose the tuning parameter τ such that
the predictive sets are large enough to achieve 1−α coverage on this set. See Figure 3 for an
illustration. This calibration step yields a choice ofτ, and the resulting set is formally guaranteed to
have coverage 1−α on a future test point from the same distribution; see Theorem 1 below.
Formally, let (Xi,Yi)i=1,...,n be an independent and identically distributed (i.i.d.) set of variables
that was not used for model training. Further, let C(x,u,τ ) : Rd× [0, 1]× R→ 2Y be a set-
valued function that takes a feature vectorx to a subset of the possible labels. The second argument
u is included to allow for randomized procedures; let U1,...,U n be i.i.d. uniform [0, 1] random
variables that will serve as the second argument for each data point. Suppose that the sets are
indexed byτ such that they are nested, meaning larger values ofτ lead to larger sets:
C(x,u,τ 1)⊆C (x,u,τ 2) if τ1≤τ2. (2)
To ﬁnd a function that will achieve 1−α coverage on test data, we select the smallest τ that gives
at least 1−α coverage on the conformal calibration set, with a slight correction to account for the
ﬁnite sample size:
ˆτccal = inf
{
τ :|{i :Yi∈C (Xi,Ui,τ )}|n ≥⌈(n + 1)(1−α)⌉n }. (3)
The set function C(x,u,τ ) with this data-driven choice of τ is guaranteed to have correct ﬁnite-
sample coverage on a fresh test observation, as stated formally next.
4

=== PDF PAGE 5 ===
Theorem 1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi,Ui)i=1,...,n and
(Xn+1,Yn+1,Un+1) are i.i.d. and letC(x,u,τ ) be a set-valued function satisfying the nesting prop-
erty in Eq. (2). Suppose further that the sets C(x,u,τ ) grow to include all labels for large enough
τ: for all x∈ Rd,C(x,u,τ ) = Y for some τ. Then for ˆτccal deﬁned as in Eq. (3), we have the
following coverage guarantee:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≥ 1−α.
This is the same coverage property as Eq. (1) in the introduction, written in a more explicit manner.
The result is not new—a special case of this result leveraging sample-splitting ﬁrst appears in the
regression setting in Papadopoulos et al. (2002), and the core idea of conformal prediction was
introduced even earlier; see V ovk et al. (2005).
As a technical remark, the theorem also holds if the observations to satisfy the weaker condition
of exchangeability; see V ovk et al. (2005). In addition, for most families of set-valued functions
C(x,u,τ ) there is a matching upper bound:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≤ 1−α + 1n + 1.
Roughly speaking, this will hold whenever the sets grow smoothly in τ. See Lei et al. (2018) for a
formal statement of the required conditions.
2.2 O UR METHOD
Conformal calibration is a powerful general idea, allowing one to achieve the coverage desideratum
for any choice of setsC(x,u,τ ). Nonetheless, this is not yet a full solution, since the quality of the
resulting prediction sets can vary dramatically depending on the design ofC(x,u,τ ). In particular,
we recall the size and adaptiveness desiderata from Section 1—we want our uncertainty sets to be
as small as possible while faithfully articulating the instance-wise uncertainty of each test point. In
this section, we explicitly give our algorithm, which can be viewed as a special case of conformal
calibration with the uncertainty setsC designed to extract information from CNNs.
Our algorithm has three main ingredients. First, for a feature vector x, the base model computes
class probabilities ˆπx∈ Rk, and we order the classes from most probable to least probable. Then,
we add a regularization term to promote small predictive sets. Finally, we conformally calibrate the
penalized prediction sets to guarantee coverage on future test points.
Formally, letρx(y) =∑Ky′=1 ˆπx(y′)I{ˆπx(y′)&gt;ˆπx(y)} be the total probability mass of the set of labels
that are more likely than y. These are all the labels that will be included before y is included. In
addition, letox(y) =|{y′∈Y : ˆπx(y′)≥ ˆπx(y)}| be the ranking ofy among the label based on the
probabilities ˆπ. For example, ify is the third most likely label, thenox(y) = 3.1 We take
C∗(x,u,τ ) :={y : ρx(y) + ˆπx(y)·u +λ· (ox(y)−kreg)+| {z }
regularization
≤τ
}
, (4)
where (z)+ denotes the positive part of z andλ,kreg≥ 0 are regularization hyperparameters that
are introduced to encourage small set sizes. See Figure 3 for a visualization of a RAPS predictive
set and Appendix E for a discussion of how to selectkreg andλ.
Since this is the heart of our proposal, we carefully parse each term. First, the ρx(y) term increases
asy ranges from the most probable to least probable label, so our sets will prefer to include they that
are predicted to be the most probable. The second term, ˆπx(y)·u, is a randomized term to handle
the fact that the value will jump discretely with the inclusion of each newy. The randomization term
can never impact more than one value of y: there is at most one value of y such thaty∈C (x, 0,τ )
buty /∈C (x, 1,τ ). These ﬁrst two terms can be viewed as the CDF transform after arranging the
classes from most likely to least likely, randomized in the usual way to result in a continuous uniform
random variable (cf. Romano et al., 2020). We discuss randomization further in Appendix B.
Lastly, the regularization promotes small set sizes: for values ofy that occur farther down the ordered
list of classes, the termλ· (ox(y)−kreg)+ makes that value ofy require a higher value ofτ before
1For ease of notation, we assume distinct probabilities. Else, label-ordering ties should be broken randomly.
5

=== PDF PAGE 6 ===</message>
<message type="ai">
  <content><reasoning>**Checking metadata mismatch**</reasoning></content>
  <tool_call id="call_792246dd7d884fa49b720e4595eabad5" name="read_file">{"file_path": "/work/literature/2402.10723.txt", "limit": 360, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-360 of 949 | next offset 360 @@
=== PDF PAGE 1 ===
CONFORMALIZED CREDAL SET PREDICTORS
A PREPRINT
Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2
1Institute of Informatics, LMU Munich, Germany
2Munich Center for Machine Learning (MCML), Germany
3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany
alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de
ABSTRACT
Credal sets are sets of probability distributions that are considered as candidates for an imprecisely
known ground-truth distribution. In machine learning, they have recently attracted attention as an
appealing formalism for uncertainty representation, in particular due to their ability to represent
both the aleatoric and epistemic uncertainty in a prediction. However, the design of methods for
learning credal set predictors remains a challenging problem. In this paper, we make use of conformal
prediction for this purpose. More specifically, we propose a method for predicting credal sets in the
classification task, given training data labeled by probability distributions. Since our method inherits
the coverage guarantees of conformal prediction, our conformal credal sets are guaranteed to be
valid with high probability (without any assumptions on model or distribution). We demonstrate the
applicability of our method to natural language inference, a highly ambiguous natural language task
where it is common to obtain multiple annotations per example.
Keywords Conformal Prediction · Uncertainty Representation · Credal Sets
1 Introduction
Representing and quantifying uncertainty is becoming increasingly important in machine learning (ML), particularly
as ML models are employed in safety-critical application domains such as medicine or autonomous driving. In such
domains, a distinction between so-called aleatoric uncertainty and epistemic uncertainty is often useful [Hora, 1996].
Broadly speaking, aleatoric uncertainty is due to the inherent randomness of the data-generating process, whereas
epistemic uncertainty stems from the learner’s lack of knowledge about the best predictive model. Thus, while the
former is irreducible, the latter can in principle be reduced through additional information, e.g., by gathering additional
data to learn from.
Representation of aleatoric and epistemic uncertainty requires formalism more expressive than standard probability
distributions [H¨ullermeier and Waegeman, 2021]. One such formalism which prevails in the recent ML literature is
second-order probability distributions. Essentially, in a classification setting, these are distributions over distributions
over classes. Models producing second-order distributions as predictions can be learned in a classical Bayesian way
[Kendall and Gal, 2017, Depeweg et al., 2018] or using more recent approaches such as evidential deep learning [Sensoy
et al., 2018]. Yet, approaches of that kind are not unproblematic and have been subject to criticism [Bengs et al., 2022,
2023]. Another formalism suitable for representing both types of uncertainty is the concept of a credal set, which is
well-established in the field of imprecise probability theory [Walley, 1991] and meanwhile also attracted attention in ML
[Shaker and H¨ullermeier, 2020, H¨ullermeier et al., 2022]. Credal sets are (convex) sets of probability distributions that
can be considered as candidates for an imprecisely known ground-truth distribution. Figure 1 shows examples of credal
sets in a three-class scenario, where the space of distributions can be visualized by the two-dimensional probability
simplex. Broadly speaking, the larger the credal set, the higher the epistemic uncertainty, and the more “in the middle”
the set is located, i.e., the closer it is to the uniform distribution, the higher the aleatoric uncertainty.
arXiv:2402.10723v1  [stat.ML]  16 Feb 2024

=== PDF PAGE 2 ===
Conformalized Credal Set Predictors A PREPRINT
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
Figure 1: For the three-class classification setting, the space of probability distributions can be illustrated by a two-
dimensional simplex: each point in the simplex corresponds to a probability distribution so that credal sets can be
depicted as regions. The left case corresponds to the special case of a singleton (credal) set, i.e., a precise probability
distribution, signifying aleatoric but no epistemic uncertainty. The case in the middle represents partial knowledge
with a certain degree of (epistemic) uncertainty about the true distribution, and the right one corresponds to the case of
complete ignorance, where nothing is known about the distribution.
Premise a child is on the
ground crying.
Hypothesis A child on the ground
crying as others look
on.
True dist. [0.06, 0.94, 0.00]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Premise uh-huh and is it true i
mean is it um
Hypothesis It is absolutely cor-
rect.
True dist. [0.31, 0.52, 0.17]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Figure 2: An illustration of our proposed conformalized credal sets on two instances from the ChaosNLI dataset [Nie
et al., 2020]. Green regions indicate credal sets, while the true and the predicted distributions are marked with orange
squares and black circles, respectively.
Learning to predict second-order representations, such as credal sets or second-order distributions, from standard
“zero-order” supervised data — training instances together with observed class labels — is a difficult endeavor. For
the case of second-order probabilities, it is even provably impossible to predict uncertainty in an “unbiased” way, i.e.,
without imposing strong prior assumptions on the epistemic uncertainty [Bengs et al., 2022, 2023]. In this paper, we
assume “first-order” training data, i.e., instances associated with probability distributions over the class labels. In other
words, instances are labeled probabilistically instead of being assigned a deterministic class label. Obviously, this type
of data facilitates second-order learning. Not less importantly, it is becoming increasingly available in practice, for
example, in the form of aggregations over multiple annotations per data instance, and hence increasingly relevant in
applications [Uma et al., 2022, Stutz et al., 2023b]
Our method leverages the framework of conformal prediction (CP), a non-parametric approach for set-valued prediction
rooted in classical frequentist statistics [V ovk et al., 2022]. Based on relatively mild assumptions, CP is able to provide
theoretical guarantees in the form of marginal coverage: Predicted sets are guaranteed to cover the true target with high
probability. Since our method inherits these coverage guarantees, our conformal credal sets are guaranteed to be valid
with high probability (without any assumptions on model or distribution).
Our main contribution is the proposal of a novel, conformal method to construct credal set predictors from first-order
training data:
• We propose a CP based method to construct conformal credal sets. To this end, we make use of two types
of nonconformity functions based on distance resp. likelihood, and leveraging first-order resp. second-order
probability predictors.
• On ChaosNLI [Nie et al., 2020], a very ambiguous natural language inference task with multiple annotations per
example, we show that our conformal credal sets are indeed valid, i.e., include the true ground truth distribution
with high probability (see Figure 2 for an illustration). We also compare the efficiency of predictions (size of
the predicted sets) for different nonconformity functions.
• We complement this study with controlled experiments on synthetic data, specifically investigating the
performance of credal set prediction in the presence of label noise.
2

=== PDF PAGE 3 ===
Conformalized Credal Set Predictors A PREPRINT
2 Related Work
Credal sets are widely used as models for representing uncertainty, notably within the domain of imprecise probabilities
[Walley, 1991]. As already mentioned, they can represent both types of uncertainty, aleatoric and epistemic. In the
context of data analysis and statistical inference, credal sets are often used as robust models of prior information, namely
for modeling imprecise information about the prior in Bayesian inference [Walley, 1996].
In machine learning, credal sets have been used for generalizing some of the standard methods, including naive Bayes
[Zaffalon, 2002, Corani and Zaffalon, 2008], Bayesian networks [Corani et al., 2012], and decision trees [Abell´an and
Moral, 2003]. Typically, these approaches generalize simple frequentist inference to robust Bayesian inference, making
use of an imprecise version of the Dirichlet model (a conjugate prior for the multinomial distribution). Compared to our
approach, these methods are learning on standard (zero-order) training data. Moreover, despite representing uncertainty
in predictions, they do not provide any formal guarantees.
Conformal prediction [V ovk et al., 2022], briefly introduced in Section 3.2 below, has recently gained attention for
various applications in machine learning, especially for classification tasks [Sadinle et al., 2019, Romano et al., 2020,
Angelopoulos et al., 2020, Stutz et al., 2021, Fisch et al., 2022]. These methods mostly focus on split conformal
prediction using a held-out calibration set [Papadopoulos et al., 2002], overcoming computational limitations of earlier
transductive or bagging approaches [V ovk et al., 2022, V ovk, 2015, Steinberger and Leeb, 2016, Barber et al., 2021,
Linusson et al., 2020]. While tackling classification tasks, our method for constructing conformal credal sets has more
similarity with conformal regression [Romano et al., 2019, Sesia and Romano, 2021], particularly in multivariate settings
[Dietterich and Hostetler, 2022], as we essentially conformalize the simplex space of categorical distributions. Our
conformity scores differ, however, in that they are specific for distributions rather than considering general multivariate
spaces. This work also relates to work on appropriate measures of inefficiency [V ovk et al., 2017] as measuring the
inefficiency of our conformal credal sets is non-trivial. Most closely related to our work is the recent work by Stutz et al.
[2023b], who consider conformal prediction in settings with high aleatoric uncertainty. However, we explicitly target
the construction of conformal credal sets, while Stutz et al. [2023b] mainly focus on constructing confidence sets of
classes.
First-order data. In settings with high aleatoric uncertainty, labeling each example with a single, unique class is clearly
insufficient. In practice, this is typically captured by high disagreement among annotators – a problem particularly
common in natural language tasks [Reidsma and op den Akker, 2008, Aroyo and Welty, 2014, 2015, Schaekermann
et al., 2016, Dumitrache et al., 2019, Pavlick and Kwiatkowski, 2019, R¨ottger et al., 2022, Abercrombie et al., 2023].
Handling this disagreement has received considerable attention lately [Uma et al., 2021] as it offers to go beyond this
zero-order information. For example, recent work on evaluation with disagreeing annotators [Stutz et al., 2023a] argues
the use of these annotations to get approximate first-order information for evaluation. This approach is becoming more
and more viable with crowdsourcing tools [Kovashka et al., 2016, Sorokin and Forsyth, 2008, Snow et al., 2008] being
an integral component of the benchmark, making multiple annotations per data instance more accessible. We follow a
similar approach in our construction of conformal credal sets.
3 Background
3.1 Supervised Learning and Predictive Uncertainty
We consider the setting of (polychotomous) classification with label space Y = {1, . . . , K} and an instance space X .
As usual, we assume an underlying data-generating process in the form of a probability distribution P on X × Y, so
that observations (X, Y) are i.i.d. samples from P . We denote by λx ∈ ∆K the conditional probability distribution
P (· |X = x), which we also consider as an element of the (K − 1)-simplex
∆K := λ = (λ1, . . . , λK)⊤ | λk ≥ 0, ∥λ∥1 = 1	 ⊂ RK .
Thus, for each class label k ∈ Y, the probability to observe Y = k as an outcome for x ∈ Xis given by λxk .
Since the dependency between instances X and outcomes Y is non-deterministic, the prediction of Y given X = x is
necessarily afflicted with uncertainty, even if the ground-truth distributionλx is known. As already said, this uncertainty
is commonly referred to as aleatoric [H ¨ullermeier and Waegeman, 2021]. Intuitively, the closer λx to the uniform
distribution puni = (1/K, . . . ,1/K)⊤, the higher the uncertainty, and the closer it is to a degenerate (Dirac) distribution
assigning all probability mass to a single class (a corner point in ∆K), the lower the uncertainty. Various measures
have been proposed to quantify this uncertainty in numerical terms, with Shannon entropy as the arguably best-known
representative [Depeweg et al., 2018].
3

=== PDF PAGE 4 ===
Conformalized Credal Set Predictors A PREPRINT
Instead of assuming λx to be known, suppose now that only a prediction ˆλx of this distribution is available. Epistemic
uncertainty refers to the uncertainty about how well the latter approximates the former, and hence to the additional
uncertainty in the prediction of outcome Y that is caused by the discrepancy between ˆλx and the ground-truth λx. We
seek to capture this discrepancy by means of credal sets
Q ∈ QK ⊂ ∆K ,
with the idea that Q ∋ λx holds with high probability. Typically, credal sets are assumed to be convex, and further
restrictions might be imposed on QK for practical and computational reasons, for example, a restriction to convex
polygons (with a finite number of extreme points).
3.2 Conformal Prediction
Conformal prediction provides a general framework for producing set-valued predictions with a certain guarantee of
validity. In a supervised setting, consider data points of the form Z = (X, U) ∈ X × U, and the task is to predict U
given X = x. We assume the space Z to be equipped with a nonconformity measure f : Z − →R that quantifies the
“strangeness” of z, i.e., the higher f (z), the less normal or expected the data point. Let Dcalib ⊂ Zbe a (randomly
generated) set of data points, called calibration data, and Z another data point that remains unobserved. Under
the assumption of exchangeability, i.e., that the calibration data and the query point Z have been generated by an
exchangeable process, we want to construct a so-called confidence set C ⊆ Uthat guarantees coverage:
P(U ∈ C) ≥ 1 − α. (1)
By a simple combinatorial argument [V ovk et al., 2022], the confidence setC can be constructed as
C(x) :=

u ∈ U |f (x, u) &lt; q(E, α′) 	 , (2)
where α′ = |E| −1⌈(1 + |E|)(1 − α)⌉, and q(E; α′) denotes the α′-quantile of E.
Importantly, the guarantee (2) holds regardless of the nonconformity function f (·), which, however, has an influence
on the efficiency of the prediction: The more appropriate the function, the smaller the prediction set C tends to be.
Normally, f (·) is not predefined but constructed in a data-driven way using training data Dtrain. For example, a common
approach is to train a predictor π : X − → Uand then define f (x, u) in terms of d(u, π(x)), where d(·, ·) is an
appropriate distance function on U. Replacing the point-prediction π(x) ∈ Uby the prediction set C(x) ⊂ Ucan then
be seen as “conformalizing” the predictor π: Using the calibration data, CP estimates a high-probability upper bound
on the distance between point-predictions and actual outcomes, and corrects the former correspondingly.
4 Conformal Credal Set Prediction
Recall the setting and notation from Section 3.1. Our goal is to learn a credal set predictor h : X − → QK, that is, a
model that makes predictions in the form of credal sets, thereby representing both aleatoric and epistemic uncertainty.
To this end, we assume probabilistic training data of the form
D =
 
x1, λx1 , . . . , xN , λxN 	 ⊂ X ×∆K . (3)
The model h should be able to predict the (probabilistic) outcomes for new query instances in a reliable way. More
specifically, suppose that xnew is a new query instance (following the same distribution as the training data) for which a
prediction is sought. The credal prediction Q = h(xnew) should then be valid in the sense that Q ∋ λxnew with high
probability. At the same time, the prediction should be informative in the sense that the (epistemic) uncertainty reflected
by Q is as small as possible. Again, various measures for quantifying the latter can be found in the literature [Klir and
Wierman, 1999, Sale et al., 2023].
We aim to construct the credal set predictor h by means of (inductive) conformal prediction. Following the confor-
malization recipe outlined in Section 3.2, we partition D into Dtrain and Dcalib, using the former for model training and
the latter for calibration. Regarding the training step, we explore two learning strategies, connected with two ways of
defining a nonconformity function, which is pivotal in the calibration step.
The first approach is based on training a standard ( first-order) probability predictor, i.e., a probabilistic classifier
g : X − →∆K that maps instances to the (first-order) probability distribution on Y. This can be achieved, for example,
by minimizing the cross-entropy loss between the ground truth and the predicted distributions, i.e.,
g = argmin
¯g∈H
X
(xi,λxi )∈Dtrain
−
KX
k=1
λxik log(¯g(xi)k),
4

=== PDF PAGE 5 ===
Conformalized Credal Set Predictors A PREPRINT
Algorithm 1 Conformal Credal Set Prediction
Input:
Data D; error rate α; query instance xnew.
Process:
Partition D into Dtrain and Dcalib.
Train a first-order (i = 1) or a second-order (i = 2) predictor using Dtrain.
Choose a nonconformity function fi as in (4) or (6) that suits the trained predictor to obtain the set of scores
Ei.
Set α′ = |Ei|−1⌈(1 + |Ei|)(1 − α)⌉.
Output:
hi(xnew) =

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 .
where H is a hypothesis space. Given a predictor g(·) of this kind, nonconformity is naturally defined in terms of
distance:
f1(x, λx) := d(λx, g(x)) , (4)
where d(·, ·) is a suitable distance function on ∆K, such as total variation, Wasserstein distance, etc.
An alternative approach is motivated by recent work on (epistemic) uncertainty representation via second-order
probability distributions. A second-order learner G : X − →P(∆K) maps each input x to a distribution over ∆K.
Given the training data, meaningful learning in this context can be accomplished, for instance, by parameterizing the
second-order distributions using Dirichlet distributions. Specifically, one can assume that each x is associated with a
Dirichlet distribution characterized by the parameter vector θx ∈ RK+ with the probability density function
P (λ | θx) = 1B(θx)
KY
k=1
λθxk −1k , (5)
where B(·) is the multivariate beta function. This way, λx can be thought of as a sample from that distribution,
i.e., λx ∼ Dir(θx). Our model then essentially yields a prediction ˆθx of the true parameter θx for every x, and its
optimization involves minimizing the negative log-likelihood loss
X
(xi,λxi )∈Dtrain

log(B(ˆθxi )) − KX
k=1
(ˆθxik − 1) log(λxik )

.
Given a second-order predictor ˆθx, nonconformity can be defined as a decreasing function of likelihood, e.g., as 1
minus relative likelihood:
f2(x, λx) = 1 − P (λx | ˆθx)maxλ∈∆K P (λ | ˆθx) . (6)
Using the nonconformity function fi(·) (i ∈ {1, 2}), we obtain the set of nonconformity scores by
Ei :=
n
fi(xj, λxj ) | (xj, λxj ) ∈ Dcalib
o
. (7)
Accordingly, the credal set can be defined as
hi(xnew) :=

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 . (8)
Algorithm 1 outlines a summary of the proposed methods. In the following theorem, we state the validity of the
predicted set, that is, the restatement of the conformal coverage guarantee [V ovk et al., 2022] adjusted to our setting.
Theorem 4.1. Let P denote the joint probability distribution on (X, Λ) ∈ X ×∆K. If data points in Dcalib and
(xnew, λxnew) are drawn i.i.d. (exchangeably) from P, then the conformal credal sets in (8) are valid, i.e.,
P
 
λxnew ∈ hi(xnew) ≥ 1 − α , for i ∈ {1, 2}.
5

=== PDF PAGE 6 ===
Conformalized Credal Set Predictors A PREPRINT
4.1 Noisy Observations
So far, we (implicitly) assumed that ground-truth probability distributions λxi will be provided as training (and
calibration) data. Needless to say, this assumption will rarely hold true in practice. Instead, observations will rather be
noisy versions ˜λxi of the true probabilities, i.e., the data will be of the form
D =
n 
x1, ˜λx1 , . . . , xN , ˜λxN o ⊂ X ×∆K . (9)
Notably, such datasets emerge in scenarios where each data instance x is annotated by multiple human experts, which
recently have attracted a lot of attention in the context of machine learning and also conformal prediction [Stutz
et al., 2023b, Javanmardi et al., 2023]. In this context, ˜λx denotes the distribution derived from aggregating annotator
disagreements concerning the label of instance x. Of course, conformal prediction can still be applied to noisy data of
that kind, but the coverage guarantee will then only hold for the noisy labeling:
P

˜λxnew ∈ h(xnew) ≥ 1 − ˜α. (10)
Practically, one may expect that the guarantees will hold for the ground-truth as well, simply because calibration on
noisy instead of clean data will tend to make prediction regions larger and hence more conservative. Moreover, since
nonconformity is derived from a predictive model g(·) that seeks to recover ground-truth probabilities, the latter should
conform at least as well as noisy distributions. Of course, this intuition is not a formal guarantee. In order to provide
such a guarantee for the ground-truth probabilities, one obviously needs to make some assumptions. Concretely, let us
make the following bounded noise assumption for the labeling process: The labeling noise is (stochastically) bounded
in the sense that, given the nonconformity function f and a (small) probability δ &gt;0, there exists a tolerance ϵ &gt;0
such that
P

|f (x, λx) − f (x, ˜λx)| &lt; ϵ ≥ 1 − δ (11)
all x ∈ X.
Theorem 4.2. Let α &gt;0 be any miscoverage rate, and suppose the bounded noise assumption holds. Let q = q(E, ˜α)
be the critical threshold on the noisy calibration data Dcalib for miscoverage rate
˜α = α − δ1 − δ .
Then, for any new query xnew ∈ X,
P
 
f (xnew, λxnew) &lt; q+ ϵ ≥ 1 − α .
The proof is deferred to Appendix A.. As a consequence of this result, a conformal predictor learned on the noisy data
with modified miscoverage rate ˜α can be turned into a valid predictor (with miscoverage rate α) for the ground-truth
data by increasing the learned rejection threshold by ϵ, provided the bounded noise property (11) can be ascertained.
Thus, if we denote the corresponding credal set predictor by hϵ, we can guarantee that
P
 
λxnew ∈ hϵ(xnew) ≥ 1 − α . (12)
5 Experiments
In this section, we evaluate the performance of our proposed methods using both synthetic and real datasets. In vanilla
conformal prediction, the performance of a method is usually assessed based on the average prediction set size, aka
efficiency, and the average coverage on the test set. It is more appealing to have the promised coverage with smaller
sets. In our scenario, the analytical calculation of credal sets is not feasible. Therefore, for the sake of illustration as
well as other analyses, such as efficiency calculation, we resort to approximations. We discretize the simplex with a
resolution of 0.005, yielding M = 19969 distributions. This enables the straightforward construction of credal sets, as
defined in (8). The efficiency is gauged by considering the fraction of all M distributions that lie within the predicted
credal sets. All implementations and experiments can be found in the technical supplement of this work.1
5.1 Learning Model
In our experiments, we employ a deep neural network as the learner. Specifically, the model consists of three hidden
layers with 256, 64, and 16 units, utilizing ReLU as the activation function. Prior to the output layer, a dropout
1The link to the code: https://github.com/alireza-javanmardi/conformal-credal-sets
6

=== PDF PAGE 7 ===
Conformalized Credal Set Predictors A PREPRINT
Table 1: Summary of the nonconformity functions used in experiments.
Name Formulation Predictor
TV 12 PKk=1 |λxk − g(x)k| first-order
WS - first-order
KL PKk=1 λxk log( λxkg(x)k ) first-order
Inner 1 − PKk=1 λxk g(x)k first-order
SO as in (6) second-order
layer with a rate of 0.3 is incorporated. The same model architecture serves both first- and second-order predictors,
differing only in the activation functions of the output layers. For the first-order predictor, softmax is used, while for
the second-order predictor, ReLU is employed. Learning is facilitated using the Adam optimizer with a learning rate
of 10−4, utilizing cross-entropy as the loss function for the first-order predictor and negative log-likelihood for the
second-order predictor.
5.2 Nonconformity Functions
CP should work regardless of the choice of nonconformity score function, while this choice can affect the efficiency
and geometry of the prediction set. For the sake of comparison, we examine different nonconformity functions in our
experiments. When utilizing a first-order predictor, besides total variation (TV) and the First Wasserstein (WS) distance,</message>
<message type="ai">
  <content><reasoning>**Reviewing flagged mismatch**</reasoning></content>
  <tool_call id="call_1b68f85a133d41c49dae2d973d4a2156" name="think_tool">{"reflection": "Direct reads reveal a critical identifier mismatch: arXiv:2009.14193 is Angelopoulos et al., Uncertainty Sets for Image Classifiers Using Conformal Prediction, not a Romano-authored paper. Do not silently fetch a substitute. The credal paper explicitly separates exact first-order labels (Theorem 4.1) from noisy compositions (Eq.10) and requires bounded score noise for latent-probability transfer (Theorem 4.2). It also prints strict '&lt;' despite potentially tied scores, so notes must contrast the robust &lt;= order-statistic convention. Need exact tutorial sections for group calibration and full experimental details from allowed PDFs, plus official template instructions. No external search is necessary or permitted."}</tool_call>
</message>
<message type="tool">Reflection recorded: Direct reads reveal a critical identifier mismatch: arXiv:2009.14193 is Angelopoulos et al., Uncertainty Sets for Image Classifiers Using Conformal Prediction, not a Romano-authored paper. Do not silently fetch a substitute. The credal paper explicitly separates exact first-order labels (Theorem 4.1) from noisy compositions (Eq.10) and requires bounded score noise for latent-probability transfer (Theorem 4.2). It also prints strict '&lt;' despite potentially tied scores, so notes must contrast the robust &lt;= order-statistic convention. Need exact tutorial sections for group calibration and full experimental details from allowed PDFs, plus official template instructions. No external search is necessary or permitted.</message>
<message type="ai">
  <tool_call id="call_0fb51a7324ee422f848a99939300a952" name="read_file">{"file_path": "/work/literature/2107.07511.txt", "limit": 220, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-220 of 2462 | next offset 220 @@
=== PDF PAGE 1 ===
A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantiﬁcation
Anastasios N. Angelopoulos and Stephen Bates
December 8, 2022
Abstract
Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-
tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-
tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty
sets/intervals for the predictions of such models. Critically, the sets are valid in a distribution-free sense:
they possess explicit, non-asymptotic guarantees even without distributional assumptions or model as-
sumptions. One can use conformal prediction with any pre-trained model, such as a neural network, to
produce sets that are guaranteed to contain the ground truth with a user-speciﬁed probability, such as
90%. It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the
ﬁelds of computer vision, natural language processing, deep reinforcement learning, and so on.
This hands-on introduction is aimed to provide the reader a working understanding of conformal
prediction and related distribution-free uncertainty quantiﬁcation techniques with one self-contained
document. We lead the reader through practical theory for and examples of conformal prediction and
describe its extensions to complex machine learning tasks involving structured outputs, distribution
shift, time-series, outliers, models that abstain, and more. Throughout, there are many explanatory
illustrations, examples, and code samples in Python. With each code sample comes a Jupyter notebook
implementing the method on a real-data example; the notebooks can be accessed and easily run by
clicking on the following icons:
 .
1
arXiv:2107.07511v6  [cs.LG]  7 Dec 2022

=== PDF PAGE 2 ===
Contents
1 Conformal Prediction 4
1.1 Instructions for Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 Examples of Conformal Procedures 6
2.1 Classiﬁcation with Adaptive Prediction Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.2 Conformalized Quantile Regression . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.3 Conformalizing Scalar Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.1 The Estimated Standard Deviation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.2 Other 1-D Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.4 Conformalizing Bayes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Evaluating Conformal Prediction 11
3.1 Evaluating Adaptivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 The Eﬀect of the Size of the Calibration Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
3.3 Checking for Correct Coverage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
4 Extensions of Conformal Prediction 16
4.1 Group-Balanced Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Class-Conditional Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Conformal Risk Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Outlier Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
4.5 Conformal Prediction Under Covariate Shift . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
4.6 Conformal Prediction Under Distribution Drift . . . . . . . . . . . . . . . . . . . . . . . . . . 21
5 Worked Examples 23
5.1 Multilabel Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.2 Tumor Segmentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.3 Weather Prediction with Time-Series Distribution Shift . . . . . . . . . . . . . . . . . . . . . 24
5.4 Toxic Online Comment Identiﬁcation via Outlier Detection . . . . . . . . . . . . . . . . . . . 25
5.5 Selective Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
6 Full conformal prediction 27
6.1 Full Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.2 Cross-Conformal Prediction, CV+, and Jackknife+ . . . . . . . . . . . . . . . . . . . . . . . . 28
7 Historical Notes on Conformal Prediction 28
A Distribution-Free Control of General Risks 39
A.1 Instructions for Learn then Test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
2

=== PDF PAGE 3 ===
A.1.1 Crash Course on Generating p-values . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
A.1.2 Crash Course on Familywise-Error Rate Algorithms . . . . . . . . . . . . . . . . . . . 44
B Examples of Distribution-Free Risk Control 45
B.1 Multi-label Classiﬁcation with FDR Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
B.2 Simultaneous Guarantees on OOD Detection and Coverage . . . . . . . . . . . . . . . . . . . 46
C Concentration Properties of the Empirical Coverage 49
D Theorem and Proof: Coverage Property of Conformal Prediction 50
3

=== PDF PAGE 4 ===
Figure 1: Prediction set examples on Imagenet. We show three progressively more diﬃcult examples
of the class fox squirrel and the prediction sets (i.e., C(Xtest)) generated by conformal prediction.
1 Conformal Prediction
Conformal prediction [1–3] (a.k.a. conformal inference) is a straightforward way to generate prediction sets
for any model. We will introduce it with a short, pragmatic image classiﬁcation example, and follow up in
later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows.
First, we begin with a ﬁtted predicted model (such as a neural network classiﬁer) which we will call ˆf. Then,
we will create prediction sets (a set of possible labels) for this classiﬁer using a small amount of additional
calibration data—we will sometimes call this the calibration step.
Formally, suppose we have images as input and they each contain one of K classes. We begin with
a classiﬁer that outputs estimated probabilities (softmax scores) for each class: ˆf(x)∈ [0, 1]K. Then, we
reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training,
(X1,Y 1),..., (Xn,Yn), for use as calibration data. Using ˆf and the calibration data, we seek to construct a
prediction set of possible labels C(Xtest)⊂{ 1,...,K } that is valid in the following sense:
1−α≤ P(Ytest∈C (Xtest))≤ 1−α + 1n + 1, (1)
where (Xtest,Y test) is a fresh test point from the same distribution, and α∈ [0, 1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1 −α; we call
this property marginal coverage, since the probability is marginal (averaged) over the randomness in the
calibration and test points. See Figure 1 for examples of prediction sets on the Imagenet dataset.
To constructC from ˆf and the calibration data, we will perform a simple calibration step that requires
only a few lines of code; see the right panel of Figure 2. We now describe the calibration step in more detail,
introducing some terms that will be helpful later on. First, we set the conformal scoresi = 1− ˆf(Xi)Yi to be
one minus the softmax output of the true class. The score is high when the softmax output of the true class
is low, i.e., when the model is badly wrong. Next comes the critical step: deﬁne ˆq to be the⌈(n+1)(1−α)⌉/n
empirical quantile of s1,...,s n, where⌈·⌉ is the ceiling function (ˆq is essentially the 1−α quantile, but with
a small correction). Finally, for a new test data point (where Xtest is known but Ytest is not), create a
prediction setC(Xtest) ={y : ˆf(Xtest)y≥ 1− ˆq} that includes all classes with a high enough softmax output
(see Figure 2). Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy (1), no matter
what (possibly incorrect) model is used or what the (unknown) distribution of the data is.
true class
class
softmax output
#
scores,       class
softmax output
(1) compute scores
on holdout data
(2) get quantile (3) construct
prediction set
# 1: get conformal scores. n = calib_Y.shape[0]
cal_smx = model(calib_X).softmax(dim=1).numpy()
cal_scores = 1-cal_smx[np.arange(n),cal_labels]
# 2: get adjusted quantile
q_level = np.ceil((n+1)*(1-alpha))/n
qhat = np.quantile(cal_scores, q_level, method='higher')
val_smx = model(val_X).softmax(dim=1).numpy()
prediction_sets = val_smx &gt;= (1-qhat) # 3: form prediction sets
Figure 2: Illustration of conformal prediction with matching Python code.
4

=== PDF PAGE 5 ===
Remarks
Let us think about the interpretation of C. The function C is set-valued—it takes in an image, and it
outputs a set of classes as in Figure 1. The model’s softmax outputs help to generate the set. This method
constructs a diﬀerent output set adaptively to each particular input . The sets become larger when the model
is uncertain or the image is intrinsically hard. This is a property we want, because the size of the set gives you
an indicator of the model’s certainty. Furthermore, C(Xtest) can be interpreted as a set of plausible classes
that the image Xtest could be assigned to. Finally, C is valid, meaning it satisﬁes (1). 1 These properties of
C translate naturally to other machine learning problems, like regression, as we will see.
With an eye towards generalization, let us review in detail what happened in our classiﬁcation problem.
To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the
jth entry of the softmax vector estimated P(Y = j| X = x), the probability of class j conditionally on
an input image x. However, we had no guarantee that the softmax outputs were any good; they may have
been arbitrarily overﬁt or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face
value, we used the holdout set to adjust for their deﬁciencies.
The holdout set contained n≈ 500 fresh data points that the model never saw during training, which
allowed us to get an honest appraisal of its performance. The adjustment involved computing conformal
scores, which grow when the model is uncertain, but are not valid prediction intervals on their own. In our
case, the conformal score was one minus the softmax output of the true class, but in general, the score can
be any function of x and y. We then took ˆq to be roughly the 1−α quantile of the scores. In this case, the
quantile had a simple interpretation—when setting α = 0.1, at least 90% of ground truth softmax outputs
are guaranteed to be above the level 1 − ˆq (we prove this rigorously in Appendix D). Taking advantage of
this fact, at test-time, we got the softmax outputs of a new image Xtest and collected all classes with outputs
above 1− ˆq into a prediction setC(Xtest). Since the softmax output of the new true class Ytest is guaranteed
to be above 1− ˆq with probability at least 90%, we ﬁnally got the guarantee in Eq. (1).
1.1 Instructions for Conformal Prediction
As we said during the summary, conformal prediction is not speciﬁc to softmax outputs or classiﬁcation
problems. In fact, conformal prediction can be seen as a method for taking any heuristic notion of
uncertainty from any model and converting it to a rigorous one (see the diagram below). Conformal pre-
diction does not care if the underlying prediction problem is discrete/continuous or classiﬁcation/regression.
Heuristic
uncertainty
(per input)
Rigorous
uncertainty
(per input)
conformal
prediction
We next outline conformal prediction for a general input x and output y (not necessarily discrete).
1. Identify a heuristic notion of uncertainty using the pre-trained model.
2. Deﬁne the score function s(x,y )∈ R. (Larger scores encode worse agreement between x and y.)
3. Compute ˆq as the ⌈(n+1)(1−α)⌉n quantile of the calibration scores s1 =s(X1,Y 1),...,s n =s(Xn,Yn).
4. Use this quantile to form the prediction sets for new examples:
C(Xtest) ={y :s(Xtest,y )≤ ˆq}. (2)
As before, these sets satisfy the validity property in (1), for any (possibly uninformative) score function and
(possibly unknown) distribution of the data. We formally state the coverage guarantee next.
1Due to the discreteness of Y , a small modiﬁcation involving tie-breaking is needed to additionally satisfy the upper bound
(see [4] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
5

=== PDF PAGE 6 ===
Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [5]). Suppose (Xi,Yi)i=1,...,n
and (Xtest,Y test) are i.i.d. and deﬁne ˆq as in step 3 above andC(Xtest) as in step 4 above. Then the following
holds:
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
See Appendix D for a proof and a statement that includes the upper bound in (1). We note that the
above is only a special case of conformal prediction, called split conformal prediction . This is the most
widely-used version of conformal prediction, and it will be our primary focus. To complete the picture, we
describe conformal prediction in full generality later in Section 6 and give an overview of the literature in
Section 7.
Choice of score function
Upon ﬁrst glance, this seems too good to be true, and a skeptical reader might ask the following question:
How is it possible to construct a statistically valid prediction set even if the heuristic notion of uncertainty
of the underlying model is arbitrarily bad?
Let’s give some intuition to supplement the mathematical understanding from the proof in Appendix D.
Roughly, if the scoressi correctly rank the inputs from lowest to highest magnitude of model error, then the
resulting sets will be smaller for easy inputs and bigger for hard ones. If the scores are bad, in the sense that
they do not approximate this ranking, then the sets will be useless. For example, if the scores are random
noise, then the sets will contain a random sample of the label space, where that random sample is large
enough to provide valid marginal coverage. This illustrates an important underlying fact about conformal
prediction: although the guarantee always holds, the usefulness of the prediction sets is primarily
determined by the score function. This should be no surprise—the score function incorporates almost all
the information we know about our problem and data, including the underlying model itself. For example, the
main diﬀerence between applying conformal prediction on classiﬁcation problems versus regression problems
is the choice of score. There are also many possible score functions for a single underlying model, which have
diﬀerent properties. Therefore, constructing the right score function is an important engineering choice. We
will next show a few examples of good score functions.
2 Examples of Conformal Procedures
In this section we give examples of conformal prediction applied in many settings, with the goal of providing
the reader a bank of techniques to practically deploy. Note that we will focus only on one-dimensional Y in
this section, and smaller conformal scores will correspond to more model conﬁdence (such scores are called
nonconformity scores). Richer settings, such as high-dimensional Y , complicated (or multiple) notions of
error, or where diﬀerent mistakes cost diﬀerent amounts, often require the language of risk control, outlined
in Section A.
2.1 Classiﬁcation with Adaptive Prediction Sets
Let’s begin our sequence of examples with an improvement to the classiﬁcation example in Section 1.
The previous method produces prediction sets with the smallest average size [6], but it tends to undercover
hard subgroups and overcover easy ones. Here we develop a diﬀerent method called adaptive prediction sets
(APS) that avoids this problem. We will follow [7] and [4].
As motivation for this new procedure, note that if the softmax outputs ˆf(Xtest) were a perfect model
of Ytest|Xtest, we would greedily include the top-scoring classes until their total mass just exceeded 1 −α.</message>
<message type="ai">
  <content><reasoning>**Extracting page snippets**</reasoning></content>
  <tool_call id="call_8070bc6d59ff49f9920301aee75f919f" name="execute">{"command": "python -c 'from pathlib import Path; from pypdf import PdfReader; specs={\"2107.07511\":[11,12,13,14,15,16,17,20,50],\"1904.06019\":[6,7],\"2009.14193\":[6,7,8,9,10,14,15,16,17],\"2402.10723\":[7,8,9,13]}; [(Path(\"/work/literature/\"+i+\"_consulted.txt\").write_text(\"\\n\\n\".join(\"=== PDF PAGE \"+str(p)+\" ===\\n\"+r.pages[p-1].extract_text() for p in pages)),print(i,pages)) for i,pages in specs.items() for r in [PdfReader(\"/work/literature/\"+i+\".pdf\")]]'", "timeout": 120}</tool_call>
</message>
<message type="tool">2107.07511 [11, 12, 13, 14, 15, 16, 17, 20, 50]
1904.06019 [6, 7]
2009.14193 [6, 7, 8, 9, 10, 14, 15, 16, 17]
2402.10723 [7, 8, 9, 13]

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_43307d367d794b11ae730f1b4ae18632" name="read_file">{"file_path": "/work/literature/1904.06019.txt", "limit": 340, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-340 of 2190 | next offset 340 @@
=== PDF PAGE 1 ===
Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the training and test data are not drawn from the same distribution.
We begin by reviewing the basics of conformal prediction, in this section. In Section 2, we describe an extension of
conformal prediction to the setting of covariate shift, and give supporting empirical results. In Section 3, we cover the
mathematical details behind our conformal extension. We conclude in Section 4, and discuss several other possible
applications of our new conformal methodology.
1.1 Quantile lemma
Before explaining the basic ideas behind conformal inference (i.e., conformal prediction, we will use these two terms
interchangeably), we introduce some notation. We denote by Quantile(β;F ) the levelβ quantile of a distributionF ,
i.e., forZ∼F ,
Quantile(β;F ) = inf
{
z : P{Z≤z}≥ β
}
.
In our use of quantiles, we will allow for distributionsF on the augmented real line, R∪{∞} . For valuesv1,...,v n,
we writev1:n ={v1,...,v n} to denote their multiset. Note that this is unordered, and allows for multiple instances the
same element; thus in the present case, ifvi =vj fori⁄=j, then this value appears twice inv1:n. To denote quantiles
of the empirical distribution of the valuesv1,...,v n, we abbreviate
Quantile(β;v1:n) = Quantile
(
β; 1n
n∑
i=1
δvi
)
,
1
arXiv:1904.06019v3  [stat.ME]  6 Jul 2020

=== PDF PAGE 2 ===
whereδa denotes a point mass ata (i.e., the distribution that places all mass at the valuea). The next result is a simple
but key component underlying conformal prediction.
Lemma 1. IfV1,...,V n+1 are exchangeable random variables, then for anyβ∈ (0, 1), we have
P
{
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)}
≥β.
Furthermore, if ties betweenV1,...,V n+1 occur with probability zero, then the above probability is upper bound by
β + 1/(n + 1).
Proof. Consider the following useful fact about quantiles of a discrete distributionF , with support pointsa1,...,a k∈
R: denotingq = Quantile(β;F ), if we reassign the pointsai &gt;q to arbitrary values strictly larger thanq, yielding a
new distribution ~F , then the levelβ quantile remains unchanged, Quantile(β;F ) = Quantile(β;~F ). Using this fact,
Vn+1 &gt; Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1 &gt; Quantile
(
β;V1:(n+1)
)
,
or equivalently,
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1≤ Quantile
(
β;V1:(n+1)
)
. (2)
Moreover, it is straightforward to check that
Vn+1≤ Quantile
(
β;V1:(n+1)
)
⇐⇒ Vn+1 is among the⌈β(n + 1)⌉ smallest ofV1,...,V n+1.
By exchangeability, the latter event occurs with probability at least⌈β(n + 1)⌉/(n + 1)≥β, which proves the lower
bound; when there are almost surely no ties, it holds with probability exactly⌈β(n + 1)⌉/(n + 1)≤β + 1/(n + 1),
which proves the upper bound.
1.2 Conformal prediction
We now return to the regression setting. DenoteZi = (Xi,Yi),i = 1,...,n , andZ1:n ={Z1,...,Z n}. We will use
the abbreviationZ−i =Z1:n\{Zi}. In what follows, we describe the construction of a prediction band satisfying (1),
using conformal inference, due to V ovk et al. (2005). We ﬁrst choose a score functionS, whose arguments consist of a
point (x,y ), and a multisetZ.1 Informally, a low value ofS((x,y ),Z ) indicates that the point (x,y ) “conforms” toZ,
whereas a high value indicates that (x,y ) is atypical relative to the points inZ. For example, we might choose to deﬁne
S by
S
(
(x,y ),Z
)
=|y−ˆµ(x)|, (3)
whereˆµ : Rd→ R is a regression function that was ﬁtted by running an algorithmA on (x,y ) andZ.
Next, at eachx∈ Rd, we deﬁne the conformal prediction interval2 ˆCn(x) by repeating the following procedure for
eachy∈ R. We calculate the nonconformity scores
V (x,y)i =S(Zi,Z−i∪{ (x,y )}), i= 1,...,n, and V (x,y)n+1 =S((x,y ),Z 1:n), (4)
and includey in our prediction interval ˆCn(x) if
V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞}),
whereV (x,y)1:n ={V (x,y)1 ,...,V (x,y)n }. Importantly, the symmetry in the construction of the nonconformity scores (4)
guarantees exact coverage in ﬁnite samples. The next theorem summarizes this coverage result. The lower bound is a
standard result in conformal inference, due to V ovk et al. (2005); the upper bound, as far as we know, was ﬁrst pointed
out by Lei et al. (2018).
1We emphasize that by deﬁningZ to be a multiset, we are treating its points as unordered. Hence, to be perfectly explicit, the score function S
cannot accept the points inZ in any particular order, and it must take them in as unordered. The same is true of the base algorithm A used to deﬁne
the ﬁtted regression function ˆµ, in the choice of absolute residual score function (3).
2For convenience, throughout, we will refer to ˆCn(x) as an “interval”, even though this may actually be a union of multiple nonoverlapping
intervals. Similarly, for simplicity, we will refer to ˆCn as a “band”.
2

=== PDF PAGE 3 ===
Theorem 1 (V ovk et al. 2005; Lei et al. 2018). Assume that (Xi,Yi)∈ Rd× R,i = 1,...,n + 1 are exchangeable.
For any score functionS, and anyα∈ (0, 1), deﬁne the conformal band (based on the ﬁrstn samples) atx∈ Rd by
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞})}, (5)
whereV (x,y)i ,i = 1,...,n + 1 are as deﬁned in (4). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Furthermore, if ties betweenV (Xn+1,Yn+1)1 ,...,V (Xn+1,Yn+1)n+1 occur with probability zero, then this probability is upper
bounded by 1−α + 1/(n + 1).
Proof. To lighten notation, abbreviateVi =V (Xn+1,Yn+1)i ,i = 1,...,n + 1. Observe
Yn+1∈ ˆCn(Xn+1) ⇐⇒ Vn+1≤ Quantile(1−α;V1:n∪{∞}).
By the symmetric construction of the nonconformity scores in (4),
(Z1,...,Z n+1)
d
= (Zσ(1),...,Z σ(n+1)) ⇐⇒ (V1,...,V n+1)
d
= (Vσ(1),...,V σ(n+1)),
for any permutationσ of the numbers 1,...,n + 1. Therefore, asZ1,...,Z n+1 are exchangeable, so areV1,...,V n+1,
and applying Lemma 1 gives the result.
Remark 1. Theorem 1 is stated for exchangeable samples (Xi,Yi),i = 1,...,n + 1, which is (signiﬁcantly) weaker
than assuming i.i.d. samples. As we will see in what follows, it is furthermore possible to relax the exchangeability
assumption, under an appropriate modiﬁcation to the conformal procedure.
Remark 2. If we use an appropriate random tie-breaking rule (to determine the rank ofVn+1 amongV1,...,V n+1),
then the upper bounds in Lemma 1 and Theorem 1 hold in general (without assuming there are no ties almost surely).
The result in Theorem 1, albeit very simple to prove, is quite remarkable. It gives us a recipe for distribution-free
prediction intervals, with nearly exact coverage, starting from an arbitrary score functionS; e.g., absolute residuals
with respect to a ﬁtted regression function from any base algorithmA, as in (3). For more discussion of conformal
prediction, its properties, and its variants, we refer to V ovk et al. (2005); Lei et al. (2018) and references therein.
2 Covariate shift
In this paper, we are concerned with settings in which the data (Xi,Yi),i = 1,...,n + 1 are no longer exchangeable.
Our primary focus will be a setting in which we observe data according to
(Xi,Yi)
i.i.d.
∼ P =PX×PY|X, i= 1,...,n,
(Xn+1,Yn+1)∼ ~P = ~PX×PY|X, independently. (6)
Notice that the conditional distribution ofY|X is assumed to be the same for both the training and test data. Such a
setting is often called covariate shift (e.g., see Shimodaira 2000; Quinonero-Candela et al. 2009; see also Remark 4
below for more discussion of this literature). The key realization is the following: if we know the ratio of test to training
covariate likelihoods, d~PX/dPX, then we can still perform a modiﬁed of version conformal inference, using a quantile
of a suitably weighted empirical distribution of nonconformity scores. The next subsection gives the details; following
this, we describe a more computationally efﬁcient conformal procedure, and give an empirical demonstration.
2.1 Weighted conformal prediction
In conformal prediction, we compare the value of a nonconformity score at a test point to the empirical distribution of
nonconformity scores at the training points. In the covariate shift case, where the covariate distributions PX,~PX in
our training and test sets differ, we will now weight each nonconformity scoreV (x,y)i (which measures how wellZi =
3

=== PDF PAGE 4 ===
(Xi,Yi) conforms to the other points) by a probability proportional to the likelihood ratiow(Xi) = d~PX (Xi)/dPX (Xi).
Therefore, we will no longer be interested in the empirical distribution
1
n + 1
n∑
i=1
δV (x,y)i + 1n + 1δ∞,
as in Theorem 1, but rather, a weighted version
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞,
where the weights are deﬁned by
pwi (x) = w(Xi)∑n
j=1w(Xj) +w(x), i= 1,...,n, and pwn+1(x) = w(x)∑nj=1w(Xj) +w(x). (7)
Due this careful weighting, draws from the discrete distribution in the second to last display resemble nonconformity
scores computed on the test population, and thus, they “look exchangeable” with the nonconformity score at our test
point. Our main result below formalizes these claims.
Corollary 1. Assume data from the model(6). Assume that ~PX is absolutely continuous with respect toPX, and denote
w = d~PX/dPX. For any score functionS, and anyα∈ (0, 1), deﬁne forx∈ Rd,
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile
(
1−α;
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞
)}
, (8)
whereV (x,y)i ,i = 1,...,n + 1 are as in (4), andpwi (x),i = 1,...,n + 1 are as in (7). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Corollary 1 is a special case of a more general result that we present later in Theorem 2, which extends conformal
inference to a setting in which the data are what we call weighted exchangeable. The proof is given in Section 3.5.
Remark 3. The same result as in Corollary 1 holds ifw∝ d~PX/dPX, i.e., with an unknown normalization constant,
because this normalization constant cancels out in the calculation of probabilities in (7).
Remark 4. Though the basic premise of covariate shift—and certainly the techniques employed in addressing it—are
related to much older ideas in statistics, the speciﬁc setup (6) has recently generated great interest in machine learning:
e.g., see Sugiyama and Muller (2005); Sugiyama et al. (2007); Quinonero-Candela et al. (2009); Agarwal et al. (2011);
Wen et al. (2014); Reddi et al. (2015); Chen et al. (2016) and references therein). The focus is usually on correcting
estimators, model evaluation, or model selection approaches to account for covariate shift. Correcting distribution-free
prediction intervals, as we examine in this work, is (as far as we know) a new contribution. As one might expect, the
likelihood ratio d~PX/dPX, a key component of our conformal construction in Corollary 1, also plays a critical role in
much of the literature on covariate shift.
2.2 Weighted split conformal
In general, constructing a conformal prediction band can be computationally intensive, though this of course depends
on the choice of score function. Consider the use of absolute residuals as in (3). To compute the nonconformity scores
in (4), we must ﬁrst run our base algorithmA on the data setZ1:n∪{ (x,y )} to produce a ﬁtted regression functionˆµ,
and then calculate
V (x,y)i =|Yi−ˆµ(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−ˆµ(x)|.
As the formation of the conformal set in (5) (ordinary case) or (8) (covariate shift case) requires us to do this for each
x∈ Rd andy∈ R (which requires reﬁttingˆµ each time), this can clearly become computationally burdernsome.
A fast alternative, known as split conformal prediction (Papadopoulos et al., 2002; Lei et al., 2015), resolves this
issue by taking the score functionS to be deﬁned using absolute residuals with respect to a ﬁxed regression function,
4

=== PDF PAGE 5 ===
typically, one that has been trained on an preliminary data set. Denote by (X 01,Y 01 ),..., (X 0n0,Y 0n0 ) this preliminary
data set, used for ﬁtting the regression functionµ0, and consider the score function
S
(
(x,y ),Z
)
=|y−µ0(x)|.
Given data (X1,Y 1),..., (Xn,Yn), independent of (X 01,Y 01 ),..., (X 0n0,Y 0n0 ), we calculate
V (x,y)i =|Yi−µ0(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−µ0(x)|.
The conformal prediction interval (5), deﬁned at a pointx∈ Rd, reduces to
ˆCn(x) = µ0(x)± Quantile
(
1−α;
{
|Yi−µ0(Xi)|
}n
i=1∪{∞}
)
, (9)
and by Theorem 1 it has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ). This coverage result holds
because, when we treatµ0 as ﬁxed (meaning, condition on (X 01,Y 01 ),..., (X 0n0,Y 0n0 )), the scoresV (x,y)1 ,...,V (x,y)n+1
scores are exchangeable for (x,y ) = (Xn+1,Yn+1), as (X1,Y 1),..., (Xn+1,Yn+1) are.
As split conformal prediction can be seen as a special case of conformal prediction, in which the regression function
µ0 is treated as ﬁxed, Corollary 1 also applies to the split scenario, and guarantees that the band deﬁned forx∈ Rd by
ˆCn(x) = µ0(x)± Quantile
(
1−α;
n∑
i=1
pwi (x)δ|Yi−µ0(Xi)| +pwn+1(x)δ∞
)
, (10)
where the probabilities are as in (7), has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ).
2.3 Airfoil data example
We demonstrate the use of conformal prediction in the covariate shift setting in an empirical example. We consider the
airfoil data set from the UCI Machine Learning Repository (Dua and Graff, 2019), which hasN = 1503 observations of
a responseY (scaled sound pressure level of NASA airfoils), and a covariateX withd = 5 dimensions (log frequency,
angle of attack, chord length, free-stream velocity, and suction side log displacement thickness). For efﬁciency, we use
the split conformal prediction methods in (9) and (10) for the unweighted and weighted case, respectively. R code to
reproduce these simulation results can be found at http://www.github.com/ryantibs/conformal/.
Creating training data, test data, and covariate shift. We repeated an experiment for 5000 trials, where for each
trial we randomly partitioned the data{(Xi,Yi)}Ni=1 into three setsDpre,D train,D test, and also constructed a covariate
shift test setDshift, which have the following roles.
• Dpre, containing 25% of the data, is used to preﬁt a regression functionµ0 via linear regression, to be used in
constructing split conformal intervals.
• Dtrain, containing 25% of the data, is our training set, i.e., (Xi,Yi),i = 1,...,n , used to compute the residual
quantiles in the construction of the split conformal prediction intervals (9) and (10).
• Dtest, containing 50% of the data, is our test set (as these data points are exchangeable with those inDtrain, there
is no covariate shift in this test set).
• Dshift is a second test set, constructed to simulate covariate shift, by sampling 25% of the points fromDtest with
replacement, with probabilities proportional to
w(x) = exp(xTβ), where β = (−1, 0, 0, 0, 1). (11)
As the original data pointsDtrain∪Dtest can be seen as draws from the same underlying distribution, we can view
w(x) as the likelihood ratio of covariate distributions between the test setDshift and training setDtrain. Note that the test
covariate distribution~PX, which satisﬁes d~PX∝ exp(xTβ)dPX as we have deﬁned it here, is called an exponential
tilting of the training covariate distributionPX. Figure 1 visualizes the effect of this exponential tilting, in the airfoil
data set, with our choiceβ = (−1, 0, 0, 0, 1). Only the 1st and 5th dimensions of the covariate distribution are tilted;
the bottom row of Figure 1 plots the marginal densities of the 1st and 5th covariates (estimated via kernel smoothing)
before and after the tilt. The top row plots the response versus the 1st and 5th covariates, simply to highlight the fact
that there is heteroskedasticity, and thus we might expect the shift in the covariate distribution to have some effect on
the validity of the ordinary conformal prediction intervals.
5

=== PDF PAGE 6 ===
●
●
●●
●
●
●
●
●●● ●
●
●
●
●
●
●
●
●●●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●
●●</message>
<message type="ai">
  <tool_call id="call_4d862f45c9da410cab8c4e630159cab5" name="read_file">{"file_path": "/work/literature/2009.14193.txt", "limit": 290, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-290 of 898 | next offset 290 @@
=== PDF PAGE 1 ===
UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in computer vision.
Formally, for a discrete responseY ∈Y ={1,...,K } and a feature vectorX∈ Rd, we desire an
uncertainty set function,C(X), mapping a feature vector to a subset of{1,...,K } such that
P (Y ∈C (X))≥ 1−α, (1)
for a pre-speciﬁed conﬁdence levelα such as 10%. Conformal predictors like our method can mod-
ify any black-box classiﬁer to output predictive sets that are rigorously guaranteed to satisfy the
∗equal contribution
†Project website here.
1
arXiv:2009.14193v5  [cs.CV]  3 Sep 2022

=== PDF PAGE 2 ===
Figure 1: Prediction set examples on Imagenet. We show three examples of the class fox squirrel and
the 95% prediction sets generated by RAPS to illustrate how the size of the set changes as a function of the
difﬁculty of a test-time image.
desired coverage property shown in Eq. (1). For evaluations, we focus on Imagenet classiﬁcation
using convolutional neural networks (CNNs) as the base classiﬁers, since this is a particularly chal-
lenging testbed. In this setting,X would be the image andY would be the class label. Note that the
guarantee in Eq. (1) is marginal overX andY —it holds on average, not for a particular imageX.
A ﬁrst approach toward this goal might be to assemble the set by including classes from highest to
lowest probability (e.g., after Platt scaling and a softmax function; see Platt et al., 1999; Guo et al.,
2017) until their sum just exceeds the threshold 1−α. We call this strategy naive and formulate
it precisely in Algorithm 1. There are two problems with naive: ﬁrst, the probabilities output by
CNNs are known to be incorrect (Nixon et al., 2019), so the sets from naive do not achieve cov-
erage. Second, image classiﬁcation models’ tail probabilities are often badly miscalibrated, leading
to large sets that do not faithfully articulate the uncertainty of the model; see Section 2.3. Moreover,
smaller sets that achieve the same coverage level can be generated with other methods.
The coverage problem can be solved by picking a new threshold using holdout samples. For exam-
ple, withα =10%, if choosing sets that contain 93% estimated probability achieves 90% coverage
on the holdout set, we use the 93% cutoff instead. We refer to this algorithm, introduced in Ro-
mano et al. (2020), as Adaptive Prediction Sets (APS). The APS procedure provides coverage but
still produces large sets. To ﬁx this, we introduce a regularization technique that tempers the in-
ﬂuence of these noisy estimates, leading to smaller, more stable sets. We describe our proposed
algorithm, Regularized Adaptive Prediction Sets (RAPS), in Algorithms 2 and 3 (with APS as a
special case). As we will see in Section 2, both APS and RAPS are always guaranteed to satisfy
Eq. (1)—regardless of model and dataset. Furthermore, we show that RAPS is guaranteed to have
better performance than choosing a ﬁxed-size set. Both methods impose negligible computational
requirements in both training and evaluation, and output useful estimates of the model’s uncertainty
on a new image given, say, 1000 held-out examples.
In Section 3 we conduct the most extensive evaluation of conformal prediction in deep learning to
date on Imagenet and Imagenet-V2. We ﬁnd that RAPS sets always have smaller average size than
naive and APSsets. For example, using a ResNeXt-101, naive does not achieve coverage, while
APS and RAPS achieve it almost exactly. However,APS sets have an average size of 19, whileRAPS
sets have an average size of 2 atα = 10% (Figure 2 and Table 1). We will provide an accompanying
codebase that implements our method as a wrapper for any PyTorch classiﬁer, along with code to
exactly reproduce all of our experiments.
1.1 R ELATED WORK
Reliably estimating predictive uncertainty for neural networks is an unsolved problem. Historically,
the standard approach has been to train a Bayesian neural network to learn a distribution over net-
work weights (Quinonero-Candela et al., 2005; MacKay, 1992; Neal, 2012; Kuleshov et al., 2018;
Gal, 2016). This approach requires computational and algorithmic modiﬁcations; other approaches
avoid these via ensembles (Lakshminarayanan et al., 2017; Jiang et al., 2018) or approximations of
Bayesian inference (Riquelme et al., 2018; Sensoy et al., 2018). These methods also have major
practical limitations; for example, ensembling requires training many copies of a neural network ad-
versarially. Therefore, the most widely used strategy is ad-hoctraditional calibration of the softmax
scores with Platt scaling (Platt et al., 1999; Guo et al., 2017; Nixon et al., 2019).
2

=== PDF PAGE 3 ===
0.9 0.95 0.99
desired coverage (1- )
0.85
0.90
0.95
1.00empirical coverage
Naive
APS
RAPS
0.9 0.95 0.99
desired coverage (1- )
0
20
40
60
80
100average size
Figure 2: Coverage and average set size on Imagenet for prediction sets from three methods.All methods
use a ResNet-152 as the base classiﬁer, and results are reported for 100 random splits of Imagenet-Val, each of
size 20K. See Section 3.1 for full details.
This work develops a method for uncertainty quantiﬁcation based onconformal prediction. Originat-
ing in the online learning literature, conformal prediction is an approach for generating predictive
sets that satisfy the coverage property in Eq. (1) (V ovk et al., 1999; 2005). We use a convenient
data-splitting version known as split conformal prediction that enables conformal prediction meth-
ods to be deployed for essentially any predictor (Papadopoulos et al., 2002; Lei et al., 2018). While
mechanically very different from traditional calibration as discussed above, we will refer to our
approach as conformal calibration to highlight that the two methodologies have overlapping but
different goals.
Conformal prediction is a general framework, not a speciﬁc algorithm—important design decisions
must be made to achieve the best performance for each context. To this end, Romano et al. (2020)
and Cauchois et al. (2020) introduce techniques aimed at achieving coverage that is similar across
regions of feature space, whereas ?Hechtlinger et al. (2018) and ? introduce techniques aimed at
achieving equal coverage for each class. While these methods have conceptual appeal, thus far
there has been limited empirical evaluation of this general approach for state-of-the-art CNNs. Con-
cretely, the only works that we are aware of that include some evaluation of conformal methods on
ImageNet—the gold standard for benchmarking computer vision methods—are Hechtlinger et al.
(2018), Park et al. (2019), Cauchois et al. (2020), and Messoudi et al. (2020), although in all four
cases further experiments are needed to more fully evaluate their operating characteristics for practi-
cal deployment. At the heart of conformal prediction is theconformal score: a measure of similarity
between labeled examples which is used to compare a new point to among those in a hold out set.
Our theoretical contribution can be summarized as a modiﬁcation of the conformal score from Ro-
mano et al. (2020) to have smaller, more stable sets. Lastly, there are alternative approaches to
returning prediction sets not based on conformal prediction (Pearce et al., 2018; Zhang et al., 2018).
These methods can be used as input to a conformal procedure to potentially improve performance,
but they do not have ﬁnite-sample coverage guarantees when used alone.
2 M ETHODS
In developing uncertainty set methods to improve upon naive, we are guided by three desiderata.
First and most importantly, the coverage desideratum says the sets must provide 1−α coverage, as
Algorithm 1 Naive Prediction Sets
Input: α, sorted scoress, associated permutation of classesI, booleanrand
1: procedure NAIVE (α,s,I,rand )
2: L← 1
3: while∑Li=1si &lt; 1−α do ⊿ Stop if 1−α probability exceeded
4: L←L + 1
5: ifrand then ⊿ Break ties randomly (explained in Appendix B)
6: U← Unif(0, 1)
7: V ← (∑Li=1si− (1−α))/sL
8: ifU≤V then
9: L←L− 1
10: return
{
I1,...,I L
}
Output: The 1−α prediction set,
{
I1,...,I L
}
3

=== PDF PAGE 4 ===
τ^ccal0
25%
50%
75%
1−α′
100%
τ: set size parameter
empirical coverage
(a) Conformal calibration
0.50.5
0.770.77
0.920.92
1.021.02
1.091.09 1.151.15
kreg τ^ccal
0.0
0.2
0.4
c d f b e a
class
penalized probability
penalty
probability (b) A RAPS prediction set
Figure 3: Visualizations of conformal calibration and RAPS sets. In the left panel, the y-axis shows the
empirical coverage on the conformal calibration set, and 1−α′ =⌈(n + 1)(1−α)⌉/n. In the right panel, the
printed numbers indicate the cumulative probability plus penalty mass. For the indicated value ˆτccal, the RAPS
prediction set is{c, d, f, b}.
discussed above. Secondly, the size desideratum says we want sets of small size, since these convey
more detailed information and may be more useful in practice. Lastly, the adaptiveness desidera-
tum says we want the sets to communicate instance-wise uncertainty: they should be smaller for
easy test-time examples than for hard ones; see Figure 1 for an illustration. Coverage and size
are obviously competing objectives, but size and adaptiveness are also often in tension. The size
desideratum seeks small sets, while the adaptiveness desideratum seeks larger sets when the classi-
ﬁer is uncertain. For example, always predicting a set of size ﬁve could achieve coverage, but it is
not adaptive. As noted above, both APSand RAPS achieve correct coverage, and we will show that
RAPS improves upon APS according to the other two desiderata.
We now turn to the speciﬁcs of our proposed method. We begin in Subsection 2.1 by describing an
abstract data-splitting procedure called conformal calibration that enables the near-automatic con-
struction of valid predictive sets (that is, sets satisfying Eq. (1)). Subsequently, in Subsection 2.2, we
provide a detailed presentation of our procedure, with commentary in Section 2.3. In Subsection 2.4
we discuss the optimality of our procedure, proving that it is at least as good as the procedure that
returns sets of a ﬁxed size, unlike alternative approaches.
2.1 C ONFORMAL CALIBRATION
We ﬁrst review a general technique for producing valid prediction sets, following the articulation
in Gupta et al. (2019). Consider a procedure that outputs a predictive set for each observation,
and further suppose that this procedure has a tuning parameter τ that controls the size of the sets.
(In RAPS, τ is the cumulative sum of the sorted, penalized classiﬁer scores.) We take a small
independent conformal calibration set of data, and then choose the tuning parameter τ such that
the predictive sets are large enough to achieve 1−α coverage on this set. See Figure 3 for an
illustration. This calibration step yields a choice ofτ, and the resulting set is formally guaranteed to
have coverage 1−α on a future test point from the same distribution; see Theorem 1 below.
Formally, let (Xi,Yi)i=1,...,n be an independent and identically distributed (i.i.d.) set of variables
that was not used for model training. Further, let C(x,u,τ ) : Rd× [0, 1]× R→ 2Y be a set-
valued function that takes a feature vectorx to a subset of the possible labels. The second argument
u is included to allow for randomized procedures; let U1,...,U n be i.i.d. uniform [0, 1] random
variables that will serve as the second argument for each data point. Suppose that the sets are
indexed byτ such that they are nested, meaning larger values ofτ lead to larger sets:
C(x,u,τ 1)⊆C (x,u,τ 2) if τ1≤τ2. (2)
To ﬁnd a function that will achieve 1−α coverage on test data, we select the smallest τ that gives
at least 1−α coverage on the conformal calibration set, with a slight correction to account for the
ﬁnite sample size:
ˆτccal = inf
{
τ :|{i :Yi∈C (Xi,Ui,τ )}|n ≥⌈(n + 1)(1−α)⌉n }. (3)
The set function C(x,u,τ ) with this data-driven choice of τ is guaranteed to have correct ﬁnite-
sample coverage on a fresh test observation, as stated formally next.
4

=== PDF PAGE 5 ===
Theorem 1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi,Ui)i=1,...,n and
(Xn+1,Yn+1,Un+1) are i.i.d. and letC(x,u,τ ) be a set-valued function satisfying the nesting prop-
erty in Eq. (2). Suppose further that the sets C(x,u,τ ) grow to include all labels for large enough
τ: for all x∈ Rd,C(x,u,τ ) = Y for some τ. Then for ˆτccal deﬁned as in Eq. (3), we have the
following coverage guarantee:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≥ 1−α.
This is the same coverage property as Eq. (1) in the introduction, written in a more explicit manner.
The result is not new—a special case of this result leveraging sample-splitting ﬁrst appears in the
regression setting in Papadopoulos et al. (2002), and the core idea of conformal prediction was
introduced even earlier; see V ovk et al. (2005).
As a technical remark, the theorem also holds if the observations to satisfy the weaker condition
of exchangeability; see V ovk et al. (2005). In addition, for most families of set-valued functions
C(x,u,τ ) there is a matching upper bound:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≤ 1−α + 1n + 1.
Roughly speaking, this will hold whenever the sets grow smoothly in τ. See Lei et al. (2018) for a
formal statement of the required conditions.
2.2 O UR METHOD
Conformal calibration is a powerful general idea, allowing one to achieve the coverage desideratum
for any choice of setsC(x,u,τ ). Nonetheless, this is not yet a full solution, since the quality of the
resulting prediction sets can vary dramatically depending on the design ofC(x,u,τ ). In particular,
we recall the size and adaptiveness desiderata from Section 1—we want our uncertainty sets to be
as small as possible while faithfully articulating the instance-wise uncertainty of each test point. In
this section, we explicitly give our algorithm, which can be viewed as a special case of conformal
calibration with the uncertainty setsC designed to extract information from CNNs.
Our algorithm has three main ingredients. First, for a feature vector x, the base model computes
class probabilities ˆπx∈ Rk, and we order the classes from most probable to least probable. Then,
we add a regularization term to promote small predictive sets. Finally, we conformally calibrate the
penalized prediction sets to guarantee coverage on future test points.
Formally, letρx(y) =∑Ky′=1 ˆπx(y′)I{ˆπx(y′)&gt;ˆπx(y)} be the total probability mass of the set of labels
that are more likely than y. These are all the labels that will be included before y is included. In
addition, letox(y) =|{y′∈Y : ˆπx(y′)≥ ˆπx(y)}| be the ranking ofy among the label based on the
probabilities ˆπ. For example, ify is the third most likely label, thenox(y) = 3.1 We take
C∗(x,u,τ ) :={y : ρx(y) + ˆπx(y)·u +λ· (ox(y)−kreg)+| {z }
regularization
≤τ
}
, (4)
where (z)+ denotes the positive part of z andλ,kreg≥ 0 are regularization hyperparameters that
are introduced to encourage small set sizes. See Figure 3 for a visualization of a RAPS predictive
set and Appendix E for a discussion of how to selectkreg andλ.
Since this is the heart of our proposal, we carefully parse each term. First, the ρx(y) term increases
asy ranges from the most probable to least probable label, so our sets will prefer to include they that
are predicted to be the most probable. The second term, ˆπx(y)·u, is a randomized term to handle
the fact that the value will jump discretely with the inclusion of each newy. The randomization term</message>
<message type="ai">
  <content>Two important distinctions are emerging. The allowed `2009.14193` PDF is by Angelopoulos et al., not Romano et al.; I’ll cite it correctly without fetching a substitute. The credal-set paper also distinguishes coverage of observed compositions from coverage of latent probabilities—the latter needs an additional bounded-noise assumption.</content>
  <tool_call id="call_ae02e593b3a4428dbb39eac09fa28b57" name="read_file">{"file_path": "/work/literature/2402.10723.txt", "limit": 330, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-330 of 949 | next offset 330 @@
=== PDF PAGE 1 ===
CONFORMALIZED CREDAL SET PREDICTORS
A PREPRINT
Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2
1Institute of Informatics, LMU Munich, Germany
2Munich Center for Machine Learning (MCML), Germany
3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany
alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de
ABSTRACT
Credal sets are sets of probability distributions that are considered as candidates for an imprecisely
known ground-truth distribution. In machine learning, they have recently attracted attention as an
appealing formalism for uncertainty representation, in particular due to their ability to represent
both the aleatoric and epistemic uncertainty in a prediction. However, the design of methods for
learning credal set predictors remains a challenging problem. In this paper, we make use of conformal
prediction for this purpose. More specifically, we propose a method for predicting credal sets in the
classification task, given training data labeled by probability distributions. Since our method inherits
the coverage guarantees of conformal prediction, our conformal credal sets are guaranteed to be
valid with high probability (without any assumptions on model or distribution). We demonstrate the
applicability of our method to natural language inference, a highly ambiguous natural language task
where it is common to obtain multiple annotations per example.
Keywords Conformal Prediction · Uncertainty Representation · Credal Sets
1 Introduction
Representing and quantifying uncertainty is becoming increasingly important in machine learning (ML), particularly
as ML models are employed in safety-critical application domains such as medicine or autonomous driving. In such
domains, a distinction between so-called aleatoric uncertainty and epistemic uncertainty is often useful [Hora, 1996].
Broadly speaking, aleatoric uncertainty is due to the inherent randomness of the data-generating process, whereas
epistemic uncertainty stems from the learner’s lack of knowledge about the best predictive model. Thus, while the
former is irreducible, the latter can in principle be reduced through additional information, e.g., by gathering additional
data to learn from.
Representation of aleatoric and epistemic uncertainty requires formalism more expressive than standard probability
distributions [H¨ullermeier and Waegeman, 2021]. One such formalism which prevails in the recent ML literature is
second-order probability distributions. Essentially, in a classification setting, these are distributions over distributions
over classes. Models producing second-order distributions as predictions can be learned in a classical Bayesian way
[Kendall and Gal, 2017, Depeweg et al., 2018] or using more recent approaches such as evidential deep learning [Sensoy
et al., 2018]. Yet, approaches of that kind are not unproblematic and have been subject to criticism [Bengs et al., 2022,
2023]. Another formalism suitable for representing both types of uncertainty is the concept of a credal set, which is
well-established in the field of imprecise probability theory [Walley, 1991] and meanwhile also attracted attention in ML
[Shaker and H¨ullermeier, 2020, H¨ullermeier et al., 2022]. Credal sets are (convex) sets of probability distributions that
can be considered as candidates for an imprecisely known ground-truth distribution. Figure 1 shows examples of credal
sets in a three-class scenario, where the space of distributions can be visualized by the two-dimensional probability
simplex. Broadly speaking, the larger the credal set, the higher the epistemic uncertainty, and the more “in the middle”
the set is located, i.e., the closer it is to the uniform distribution, the higher the aleatoric uncertainty.
arXiv:2402.10723v1  [stat.ML]  16 Feb 2024

=== PDF PAGE 2 ===
Conformalized Credal Set Predictors A PREPRINT
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
FODVV
Figure 1: For the three-class classification setting, the space of probability distributions can be illustrated by a two-
dimensional simplex: each point in the simplex corresponds to a probability distribution so that credal sets can be
depicted as regions. The left case corresponds to the special case of a singleton (credal) set, i.e., a precise probability
distribution, signifying aleatoric but no epistemic uncertainty. The case in the middle represents partial knowledge
with a certain degree of (epistemic) uncertainty about the true distribution, and the right one corresponds to the case of
complete ignorance, where nothing is known about the distribution.
Premise a child is on the
ground crying.
Hypothesis A child on the ground
crying as others look
on.
True dist. [0.06, 0.94, 0.00]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Premise uh-huh and is it true i
mean is it um
Hypothesis It is absolutely cor-
rect.
True dist. [0.31, 0.52, 0.17]
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
Figure 2: An illustration of our proposed conformalized credal sets on two instances from the ChaosNLI dataset [Nie
et al., 2020]. Green regions indicate credal sets, while the true and the predicted distributions are marked with orange
squares and black circles, respectively.
Learning to predict second-order representations, such as credal sets or second-order distributions, from standard
“zero-order” supervised data — training instances together with observed class labels — is a difficult endeavor. For
the case of second-order probabilities, it is even provably impossible to predict uncertainty in an “unbiased” way, i.e.,
without imposing strong prior assumptions on the epistemic uncertainty [Bengs et al., 2022, 2023]. In this paper, we
assume “first-order” training data, i.e., instances associated with probability distributions over the class labels. In other
words, instances are labeled probabilistically instead of being assigned a deterministic class label. Obviously, this type
of data facilitates second-order learning. Not less importantly, it is becoming increasingly available in practice, for
example, in the form of aggregations over multiple annotations per data instance, and hence increasingly relevant in
applications [Uma et al., 2022, Stutz et al., 2023b]
Our method leverages the framework of conformal prediction (CP), a non-parametric approach for set-valued prediction
rooted in classical frequentist statistics [V ovk et al., 2022]. Based on relatively mild assumptions, CP is able to provide
theoretical guarantees in the form of marginal coverage: Predicted sets are guaranteed to cover the true target with high
probability. Since our method inherits these coverage guarantees, our conformal credal sets are guaranteed to be valid
with high probability (without any assumptions on model or distribution).
Our main contribution is the proposal of a novel, conformal method to construct credal set predictors from first-order
training data:
• We propose a CP based method to construct conformal credal sets. To this end, we make use of two types
of nonconformity functions based on distance resp. likelihood, and leveraging first-order resp. second-order
probability predictors.
• On ChaosNLI [Nie et al., 2020], a very ambiguous natural language inference task with multiple annotations per
example, we show that our conformal credal sets are indeed valid, i.e., include the true ground truth distribution
with high probability (see Figure 2 for an illustration). We also compare the efficiency of predictions (size of
the predicted sets) for different nonconformity functions.
• We complement this study with controlled experiments on synthetic data, specifically investigating the
performance of credal set prediction in the presence of label noise.
2

=== PDF PAGE 3 ===
Conformalized Credal Set Predictors A PREPRINT
2 Related Work
Credal sets are widely used as models for representing uncertainty, notably within the domain of imprecise probabilities
[Walley, 1991]. As already mentioned, they can represent both types of uncertainty, aleatoric and epistemic. In the
context of data analysis and statistical inference, credal sets are often used as robust models of prior information, namely
for modeling imprecise information about the prior in Bayesian inference [Walley, 1996].
In machine learning, credal sets have been used for generalizing some of the standard methods, including naive Bayes
[Zaffalon, 2002, Corani and Zaffalon, 2008], Bayesian networks [Corani et al., 2012], and decision trees [Abell´an and
Moral, 2003]. Typically, these approaches generalize simple frequentist inference to robust Bayesian inference, making
use of an imprecise version of the Dirichlet model (a conjugate prior for the multinomial distribution). Compared to our
approach, these methods are learning on standard (zero-order) training data. Moreover, despite representing uncertainty
in predictions, they do not provide any formal guarantees.
Conformal prediction [V ovk et al., 2022], briefly introduced in Section 3.2 below, has recently gained attention for
various applications in machine learning, especially for classification tasks [Sadinle et al., 2019, Romano et al., 2020,
Angelopoulos et al., 2020, Stutz et al., 2021, Fisch et al., 2022]. These methods mostly focus on split conformal
prediction using a held-out calibration set [Papadopoulos et al., 2002], overcoming computational limitations of earlier
transductive or bagging approaches [V ovk et al., 2022, V ovk, 2015, Steinberger and Leeb, 2016, Barber et al., 2021,
Linusson et al., 2020]. While tackling classification tasks, our method for constructing conformal credal sets has more
similarity with conformal regression [Romano et al., 2019, Sesia and Romano, 2021], particularly in multivariate settings
[Dietterich and Hostetler, 2022], as we essentially conformalize the simplex space of categorical distributions. Our
conformity scores differ, however, in that they are specific for distributions rather than considering general multivariate
spaces. This work also relates to work on appropriate measures of inefficiency [V ovk et al., 2017] as measuring the
inefficiency of our conformal credal sets is non-trivial. Most closely related to our work is the recent work by Stutz et al.
[2023b], who consider conformal prediction in settings with high aleatoric uncertainty. However, we explicitly target
the construction of conformal credal sets, while Stutz et al. [2023b] mainly focus on constructing confidence sets of
classes.
First-order data. In settings with high aleatoric uncertainty, labeling each example with a single, unique class is clearly
insufficient. In practice, this is typically captured by high disagreement among annotators – a problem particularly
common in natural language tasks [Reidsma and op den Akker, 2008, Aroyo and Welty, 2014, 2015, Schaekermann
et al., 2016, Dumitrache et al., 2019, Pavlick and Kwiatkowski, 2019, R¨ottger et al., 2022, Abercrombie et al., 2023].
Handling this disagreement has received considerable attention lately [Uma et al., 2021] as it offers to go beyond this
zero-order information. For example, recent work on evaluation with disagreeing annotators [Stutz et al., 2023a] argues
the use of these annotations to get approximate first-order information for evaluation. This approach is becoming more
and more viable with crowdsourcing tools [Kovashka et al., 2016, Sorokin and Forsyth, 2008, Snow et al., 2008] being
an integral component of the benchmark, making multiple annotations per data instance more accessible. We follow a
similar approach in our construction of conformal credal sets.
3 Background
3.1 Supervised Learning and Predictive Uncertainty
We consider the setting of (polychotomous) classification with label space Y = {1, . . . , K} and an instance space X .
As usual, we assume an underlying data-generating process in the form of a probability distribution P on X × Y, so
that observations (X, Y) are i.i.d. samples from P . We denote by λx ∈ ∆K the conditional probability distribution
P (· |X = x), which we also consider as an element of the (K − 1)-simplex
∆K := λ = (λ1, . . . , λK)⊤ | λk ≥ 0, ∥λ∥1 = 1	 ⊂ RK .
Thus, for each class label k ∈ Y, the probability to observe Y = k as an outcome for x ∈ Xis given by λxk .
Since the dependency between instances X and outcomes Y is non-deterministic, the prediction of Y given X = x is
necessarily afflicted with uncertainty, even if the ground-truth distributionλx is known. As already said, this uncertainty
is commonly referred to as aleatoric [H ¨ullermeier and Waegeman, 2021]. Intuitively, the closer λx to the uniform
distribution puni = (1/K, . . . ,1/K)⊤, the higher the uncertainty, and the closer it is to a degenerate (Dirac) distribution
assigning all probability mass to a single class (a corner point in ∆K), the lower the uncertainty. Various measures
have been proposed to quantify this uncertainty in numerical terms, with Shannon entropy as the arguably best-known
representative [Depeweg et al., 2018].
3

=== PDF PAGE 4 ===
Conformalized Credal Set Predictors A PREPRINT
Instead of assuming λx to be known, suppose now that only a prediction ˆλx of this distribution is available. Epistemic
uncertainty refers to the uncertainty about how well the latter approximates the former, and hence to the additional
uncertainty in the prediction of outcome Y that is caused by the discrepancy between ˆλx and the ground-truth λx. We
seek to capture this discrepancy by means of credal sets
Q ∈ QK ⊂ ∆K ,
with the idea that Q ∋ λx holds with high probability. Typically, credal sets are assumed to be convex, and further
restrictions might be imposed on QK for practical and computational reasons, for example, a restriction to convex
polygons (with a finite number of extreme points).
3.2 Conformal Prediction
Conformal prediction provides a general framework for producing set-valued predictions with a certain guarantee of
validity. In a supervised setting, consider data points of the form Z = (X, U) ∈ X × U, and the task is to predict U
given X = x. We assume the space Z to be equipped with a nonconformity measure f : Z − →R that quantifies the
“strangeness” of z, i.e., the higher f (z), the less normal or expected the data point. Let Dcalib ⊂ Zbe a (randomly
generated) set of data points, called calibration data, and Z another data point that remains unobserved. Under
the assumption of exchangeability, i.e., that the calibration data and the query point Z have been generated by an
exchangeable process, we want to construct a so-called confidence set C ⊆ Uthat guarantees coverage:
P(U ∈ C) ≥ 1 − α. (1)
By a simple combinatorial argument [V ovk et al., 2022], the confidence setC can be constructed as
C(x) :=

u ∈ U |f (x, u) &lt; q(E, α′) 	 , (2)
where α′ = |E| −1⌈(1 + |E|)(1 − α)⌉, and q(E; α′) denotes the α′-quantile of E.
Importantly, the guarantee (2) holds regardless of the nonconformity function f (·), which, however, has an influence
on the efficiency of the prediction: The more appropriate the function, the smaller the prediction set C tends to be.
Normally, f (·) is not predefined but constructed in a data-driven way using training data Dtrain. For example, a common
approach is to train a predictor π : X − → Uand then define f (x, u) in terms of d(u, π(x)), where d(·, ·) is an
appropriate distance function on U. Replacing the point-prediction π(x) ∈ Uby the prediction set C(x) ⊂ Ucan then
be seen as “conformalizing” the predictor π: Using the calibration data, CP estimates a high-probability upper bound
on the distance between point-predictions and actual outcomes, and corrects the former correspondingly.
4 Conformal Credal Set Prediction
Recall the setting and notation from Section 3.1. Our goal is to learn a credal set predictor h : X − → QK, that is, a
model that makes predictions in the form of credal sets, thereby representing both aleatoric and epistemic uncertainty.
To this end, we assume probabilistic training data of the form
D =
 
x1, λx1 , . . . , xN , λxN 	 ⊂ X ×∆K . (3)
The model h should be able to predict the (probabilistic) outcomes for new query instances in a reliable way. More
specifically, suppose that xnew is a new query instance (following the same distribution as the training data) for which a
prediction is sought. The credal prediction Q = h(xnew) should then be valid in the sense that Q ∋ λxnew with high
probability. At the same time, the prediction should be informative in the sense that the (epistemic) uncertainty reflected
by Q is as small as possible. Again, various measures for quantifying the latter can be found in the literature [Klir and
Wierman, 1999, Sale et al., 2023].
We aim to construct the credal set predictor h by means of (inductive) conformal prediction. Following the confor-
malization recipe outlined in Section 3.2, we partition D into Dtrain and Dcalib, using the former for model training and
the latter for calibration. Regarding the training step, we explore two learning strategies, connected with two ways of
defining a nonconformity function, which is pivotal in the calibration step.
The first approach is based on training a standard ( first-order) probability predictor, i.e., a probabilistic classifier
g : X − →∆K that maps instances to the (first-order) probability distribution on Y. This can be achieved, for example,
by minimizing the cross-entropy loss between the ground truth and the predicted distributions, i.e.,
g = argmin
¯g∈H
X
(xi,λxi )∈Dtrain
−
KX
k=1
λxik log(¯g(xi)k),
4

=== PDF PAGE 5 ===
Conformalized Credal Set Predictors A PREPRINT
Algorithm 1 Conformal Credal Set Prediction
Input:
Data D; error rate α; query instance xnew.
Process:
Partition D into Dtrain and Dcalib.
Train a first-order (i = 1) or a second-order (i = 2) predictor using Dtrain.
Choose a nonconformity function fi as in (4) or (6) that suits the trained predictor to obtain the set of scores
Ei.
Set α′ = |Ei|−1⌈(1 + |Ei|)(1 − α)⌉.
Output:
hi(xnew) =

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 .
where H is a hypothesis space. Given a predictor g(·) of this kind, nonconformity is naturally defined in terms of
distance:
f1(x, λx) := d(λx, g(x)) , (4)
where d(·, ·) is a suitable distance function on ∆K, such as total variation, Wasserstein distance, etc.
An alternative approach is motivated by recent work on (epistemic) uncertainty representation via second-order
probability distributions. A second-order learner G : X − →P(∆K) maps each input x to a distribution over ∆K.
Given the training data, meaningful learning in this context can be accomplished, for instance, by parameterizing the
second-order distributions using Dirichlet distributions. Specifically, one can assume that each x is associated with a
Dirichlet distribution characterized by the parameter vector θx ∈ RK+ with the probability density function
P (λ | θx) = 1B(θx)
KY
k=1
λθxk −1k , (5)
where B(·) is the multivariate beta function. This way, λx can be thought of as a sample from that distribution,
i.e., λx ∼ Dir(θx). Our model then essentially yields a prediction ˆθx of the true parameter θx for every x, and its
optimization involves minimizing the negative log-likelihood loss
X
(xi,λxi )∈Dtrain

log(B(ˆθxi )) − KX
k=1
(ˆθxik − 1) log(λxik )

.
Given a second-order predictor ˆθx, nonconformity can be defined as a decreasing function of likelihood, e.g., as 1
minus relative likelihood:
f2(x, λx) = 1 − P (λx | ˆθx)maxλ∈∆K P (λ | ˆθx) . (6)
Using the nonconformity function fi(·) (i ∈ {1, 2}), we obtain the set of nonconformity scores by
Ei :=
n
fi(xj, λxj ) | (xj, λxj ) ∈ Dcalib
o
. (7)
Accordingly, the credal set can be defined as
hi(xnew) :=

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 . (8)
Algorithm 1 outlines a summary of the proposed methods. In the following theorem, we state the validity of the
predicted set, that is, the restatement of the conformal coverage guarantee [V ovk et al., 2022] adjusted to our setting.
Theorem 4.1. Let P denote the joint probability distribution on (X, Λ) ∈ X ×∆K. If data points in Dcalib and
(xnew, λxnew) are drawn i.i.d. (exchangeably) from P, then the conformal credal sets in (8) are valid, i.e.,
P
 
λxnew ∈ hi(xnew) ≥ 1 − α , for i ∈ {1, 2}.
5

=== PDF PAGE 6 ===
Conformalized Credal Set Predictors A PREPRINT
4.1 Noisy Observations
So far, we (implicitly) assumed that ground-truth probability distributions λxi will be provided as training (and
calibration) data. Needless to say, this assumption will rarely hold true in practice. Instead, observations will rather be
noisy versions ˜λxi of the true probabilities, i.e., the data will be of the form
D =
n 
x1, ˜λx1 , . . . , xN , ˜λxN o ⊂ X ×∆K . (9)
Notably, such datasets emerge in scenarios where each data instance x is annotated by multiple human experts, which
recently have attracted a lot of attention in the context of machine learning and also conformal prediction [Stutz
et al., 2023b, Javanmardi et al., 2023]. In this context, ˜λx denotes the distribution derived from aggregating annotator
disagreements concerning the label of instance x. Of course, conformal prediction can still be applied to noisy data of
that kind, but the coverage guarantee will then only hold for the noisy labeling:
P

˜λxnew ∈ h(xnew) ≥ 1 − ˜α. (10)
Practically, one may expect that the guarantees will hold for the ground-truth as well, simply because calibration on
noisy instead of clean data will tend to make prediction regions larger and hence more conservative. Moreover, since
nonconformity is derived from a predictive model g(·) that seeks to recover ground-truth probabilities, the latter should
conform at least as well as noisy distributions. Of course, this intuition is not a formal guarantee. In order to provide
such a guarantee for the ground-truth probabilities, one obviously needs to make some assumptions. Concretely, let us
make the following bounded noise assumption for the labeling process: The labeling noise is (stochastically) bounded
in the sense that, given the nonconformity function f and a (small) probability δ &gt;0, there exists a tolerance ϵ &gt;0
such that
P

|f (x, λx) − f (x, ˜λx)| &lt; ϵ ≥ 1 − δ (11)
all x ∈ X.
Theorem 4.2. Let α &gt;0 be any miscoverage rate, and suppose the bounded noise assumption holds. Let q = q(E, ˜α)
be the critical threshold on the noisy calibration data Dcalib for miscoverage rate
˜α = α − δ1 − δ .
Then, for any new query xnew ∈ X,
P
 
f (xnew, λxnew) &lt; q+ ϵ ≥ 1 − α .
The proof is deferred to Appendix A.. As a consequence of this result, a conformal predictor learned on the noisy data
with modified miscoverage rate ˜α can be turned into a valid predictor (with miscoverage rate α) for the ground-truth
data by increasing the learned rejection threshold by ϵ, provided the bounded noise property (11) can be ascertained.
Thus, if we denote the corresponding credal set predictor by hϵ, we can guarantee that
P
 
λxnew ∈ hϵ(xnew) ≥ 1 − α . (12)
5 Experiments
In this section, we evaluate the performance of our proposed methods using both synthetic and real datasets. In vanilla
conformal prediction, the performance of a method is usually assessed based on the average prediction set size, aka</message>
<message type="ai">
  <content><reasoning>**Reviewing Theorem 4.2 claim**</reasoning></content>
  <tool_call id="call_26a3c5b6222b4687b3321efad7b25b5a" name="read_file">{"file_path": "/work/literature/2402.10723_consulted.txt", "limit": 350, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-235 of 235 @@
=== PDF PAGE 7 ===
Conformalized Credal Set Predictors A PREPRINT
Table 1: Summary of the nonconformity functions used in experiments.
Name Formulation Predictor
TV 12 PKk=1 |λxk − g(x)k| first-order
WS - first-order
KL PKk=1 λxk log( λxkg(x)k ) first-order
Inner 1 − PKk=1 λxk g(x)k first-order
SO as in (6) second-order
layer with a rate of 0.3 is incorporated. The same model architecture serves both first- and second-order predictors,
differing only in the activation functions of the output layers. For the first-order predictor, softmax is used, while for
the second-order predictor, ReLU is employed. Learning is facilitated using the Adam optimizer with a learning rate
of 10−4, utilizing cross-entropy as the loss function for the first-order predictor and negative log-likelihood for the
second-order predictor.
5.2 Nonconformity Functions
CP should work regardless of the choice of nonconformity score function, while this choice can affect the efficiency
and geometry of the prediction set. For the sake of comparison, we examine different nonconformity functions in our
experiments. When utilizing a first-order predictor, besides total variation (TV) and the First Wasserstein (WS) distance,
we also investigate the Kullback–Leibler (KL) divergence and 1 minus the inner product (Inner) as nonconformity
functions. For the second-order predictor, we consider 1 minus the relative likelihood (SO) as defined in (6). Table 1
offers a summary of all five nonconformity functions employed in our experiments.
5.3 Real Data
We focus on the ChaosNLI dataset [Nie et al., 2020], an English Natural Language Inference (NLI) dataset that captures
the inherent variability in human judgments of textual entailment. Here, the classes are entailment, neutral, and
contradiction for each premise-hypothesis pair. Instances in this dataset are selected from the development sets of SNLI
[Bowman et al., 2015], MNLI [Williams et al., 2018], and AbductiveNLI [Bhagavatula et al., 2019], for which the
majority vote was less than three among the five human annotators. These instances were then given to100 independent
humans for annotation, given strict annotation guidelines.
We combine the chaos-SNLI and chaos-MNLI subsets, resulting in a dataset of 3113 datapoints. For model training,
we leverage a language model from the Hugging Face transformers library [Wolf et al., 2019], initially trained on
SNLI and MultiNLI datasets for classification tasks2. We utilize the last hidden layer output of this model to embed the
premise-hypothesis pairs from our 3113 instances, serving as inputs for our deep neural network. To split the data, we
randomly select 500 instances for calibration, 500 for testing, and the remaining for training. This process is repeated
ten times with different random seeds. In Figure 3, we compare the resulting credal sets of different nonconformity
functions for three specific instances. Figure 4 summarizes the overall performance of the proposed methods on this
data under different miscoverage rates (α). Notably, the mean of the average coverage over the test data across various
random seeds aligns with or exceeds the nominal value, consistent with the conformal prediction guarantee.
5.4 Synthetic Data
The primary objective of conducting experiments with synthetic data is to illustrate the impact of noisy observations,
particularly to showcase the behavior of the proposed credal sets when we only have access to an approximation of the
ground truth distributions. Our experiment revolves around a K-class classification task with K ∈ {3, 4, 6, 8, 10}. For
each K, we consider 10-dimensional features X ∈ R10, where each X1, . . . , X10 are independent standard normal
random variables. Subsequently, we generate a random matrix β ∈ R10×K, with its elements drawn independently
from the standard normal distribution. To define the ground truth probability over the classes for object X, we use the
following formulation:
λxk := P(Y = k|x) = Zj(x)P
j Zj(x) ,
2The model can be found at https://huggingface.co/cross-encoder/nli-deberta-base
7

=== PDF PAGE 8 ===
Conformalized Credal Set Predictors A PREPRINT
Premise-Hypothesis pair TV KL WS Inner SO
Premise: A man in a bar drinks from
a pitcher while a man in a green hat
looks on and a woman in a black
shirt drink from a glass.
Hypothesis: The women is drinking
water.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.24 0 .18 0 .28 0 .36 0 .06
Premise: The streets are busy and
people contemplate their futures.
Hypothesis: People are screaming
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.33 0 .20 0 .33 0 .41 0 .47
Premise: A photographer snaps a
midair action shot of a snowboarder.
Hypothesis: The midair shot snaps
at a boarder of snow.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.31 0 .27 0 .26 0 .34 0 .08
Figure 3: Various credal sets obtained for three instances from ChaosNLI dataset [Nie et al., 2020]. The ground
truth distributions are denoted by orange squares. Black circles indicate model predictions in cases employing a
first-order learner (first four columns). For the last column, utilizing a second-order learner, the predicted second-order
distributions are represented through contour plots. The miscoverage rate is α = 0.2, and the efficiency of each credal
set is written below it.
79 ./ :6 ,QQHU 62
              
0 LVFRYHUDJHUDWH 





$YHUDJH&amp;RYHUDJH






$YHUDJH(IILFLHQF\$YHUDJH&amp;RYHUDJH
$YHUDJH(IILFLHQF\
Figure 4: Coverage and efficiency results of different nonconformity functions applied on the ChaosNLI dataset [Nie
et al., 2020]. The horizontal dashed lines indicate the nominal coverage levels.
where Z(x) := exp(x⊤β). Employing this data-generating process, we generate N = 1500 samples to construct the
dataset DK = {(xi, λxi )}Ni=1.
To obtain noisy versions of DK, we employ a sampling approach. Specifically, we independently sample each
distribution λxi m times and utilize relative frequencies to create its noisy counterpart ˜λxim . We represent the resulting
dataset as DKm = {(xi, ˜λxim )}Ni=1. We repeat this process four times with m ∈ {1, 5, 10, 100}.
Given each dataset DKm, we randomly partition data points equally into training, calibration, and test sets and perform
the proposed methodologies accordingly. Again, we repeat this process ten times with different random seeds for each
dataset DKm. Due to the computational complexity in calculating efficiency for cases with K &gt;3, we utilize the quantile
of the calibration nonconformity scores as an efficiency metric. In Figure 5, we represent the overall result for TV
under different K and m values. It can be observed that the coverage is fulfilled across almost all scenarios, including
m = 1 with degenerate distributions. This observed behavior is somewhat intuitive. The model endeavors to learn the
underlying probabilistic relationship between X and Y , even given the noisy data 3. Consequently, during calibration
3Of course, this holds under some reasonable assumptions on noise.
8

=== PDF PAGE 9 ===
Conformalized Credal Set Predictors A PREPRINT
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH$YHUDJH&amp;RYHUDJH
$YHUDJH4XDQWLOH
Figure 5: Coverage and quantile results for synthetic data, where the ground truth distributions are approximated by
observing m samples from them. The horizontal dashed line indicates the nominal coverage levels 1 − α = 0.9.
with noisy instances, the nonconformity scores of noise-free instances are mostly upper-bounded by the scores of their
noisy counterparts, resulting in more conservative sets that effectively cover the ground-truth distributions. It can also
be seen that the quantile of the nonconformity scores shrinks as m increases. Results for other nonconformity functions,
along with some visualizations for the specific case of K = 3, can be found in Appendix B..
6 Limitations
The methods we proposed are promising but still subject to certain limitations. One challenge, for example, lies in the
representation of credal sets as subsets of the probability simplex. For the nonconformity functions we used in this
work, there are no closed-form equations for the resulting credal sets. Instead, the sets are only represented implicitly
(through the nonconformity threshold). Numerical approximation is feasible but essentially limited to scenarios with a
small number of classes.
The issue of representation is also connected to the computation of uncertainty measures, i.e., numerical measures
quantifying the total, aleatoric, and epistemic uncertainty associated with a credal set [Klir and Wierman, 1999].
Computation of these measures involves the computation of specific characteristics of the set, such as its distance from
the center of the simplex or its volume [Sale et al., 2023].
Our generalization to the case of noisy training data, i.e., labelings˜λ that only approximate the ground-truth probabilities
λ, provides guarantees under the bounded noise assumption. While this assumption is plausible, and in a sense always
achievable with a sufficiently large ϵ, its practical use requires a meaningful choice of ϵ and δ, which leads to inference
that is both valid and efficient. This will be difficult in cases of limited knowledge about the labeling noise. If labels are
constructed from relative frequencies (like in the case of multiple annotators), classical statistical methods might be
applicable. In general, however, an appropriate choice of ϵ and δ for practical problems is still an open problem.
7 Conclusion and Future Work
Conformal credal set prediction connects machine learning with imprecise probability theory and offers a novel data-
driven approach to constructing predictions that effectively capture both aleatoric and epistemic uncertainty. Thereby, it
provides the basis of a new approach to reliable, uncertainty-aware machine learning. Leveraging the inherent validity
of the conformal prediction framework, our conformalized credal sets are assured to cover the ground truth distributions
with high probability. We have explored different nonconformity functions within this novel setting and evaluated their
performance through numerical experiments.
A natural next step is to explore alternative approaches for defining nonconformity functions, with the goal of devising
formulations amenable to closed-form solutions for credal sets. Besides, the nonconformity has a strong influence on
the efficiency and hence the uncertainty of credal set predictions. Obviously, there is a preference for nonconformity
functions leading to higher efficiency and lower uncertainty.
Another interesting direction is to extend the learning of credal set predictors to standard (zero-order) training data.
As already mentioned, learning a second-order predictor from data of that kind turns out to be difficult in the case of
second-order probability distributions. Broadly speaking, this is due to the inherent ambiguity of the missing first-order
information, which cannot be resolved due to certain averaging effects [Bengs et al., 2022, 2023]. For the case of credal
predictors, the situation is still less clear.
9

=== PDF PAGE 13 ===
Conformalized Credal Set Predictors A PREPRINT
Appendix A. Proof of Theorem 4.2
Proof. Let A denote the event f (xnew, λxnew) &lt; q+ ϵ and ˜A the event f (xnew, ˜λxnew) &lt; q. We have
P (A) ≥ P (A ∧ ˜A)
= P ( ˜A) · P (A | ˜A)
= P ( ˜A) · (1 − P (¬A | ˜A))
Since ¬A means that f (xnew, λxnew) ≥ q + ϵ, the conditional event ¬A | B implies a violation of the closeness
condition in (11), wherefore the probability P (¬A | B) is upper-bounded by δ according to (11). Therefore, noting that
P ( ˜A) ≥ 1 − ˜α is the standard guarantee by CP,
P (A) ≥ P ( ˜A) · (1 − P (¬A | ˜A))
≥ (1 − ˜α) · (1 − δ)
= 1 − α .
Appendix B. More Results for the Synthetic Data
Figure 6 depicts the overall coverage and quantile comparison between four different nonconformity functions TV,
KL, WS, and Inner. In Figure 7, we illustrate the evolution of the credal sets as m changes from 1 to 100 for different
nonconformity functions when K = 3. For this case, the full comparison of efficiency and coverage across various
nonconformity functions is provided in Figure 8.
13



</message>
<message type="ai">
  <content><reasoning>**Auditing the proof gap**</reasoning></content>
  <tool_call id="call_39bd2076aecf4fd9824f0af0d87d5b74" name="ls">{"path": "/work/template"}</tool_call>
</message>
<message type="tool">['/template/README.md', '/template/iclr2027.zip', '/template/iclr2027/', '/template/iclr2027_contents.json', '/template/repo_contents.json']</message>
<message type="ai">
  <tool_call id="call_af5464dd9e7844569b8ef514cbcbc081" name="ls">{"path": "/work/template/iclr2027"}</tool_call>
</message>
<message type="tool">['/template/iclr2027/fancyhdr.sty', '/template/iclr2027/iclr2027_conference.bib', '/template/iclr2027/iclr2027_conference.bst', '/template/iclr2027/iclr2027_conference.sty', '/template/iclr2027/iclr2027_conference.tex', '/template/iclr2027/math_commands.tex', '/template/iclr2027/natbib.sty']</message>
<message type="ai">
  <tool_call id="call_dd358536e3ca4ec4bc2db2dcce8fe2db" name="read_file">{"file_path": "/work/template/README.md", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-2 of 2 @@
# Master-Template
Template and style files for ICLR</message>
<message type="ai">
  <tool_call id="call_7867a7f33f794e3d904597b9588616ef" name="read_file">{"file_path": "/work/template/iclr2027/iclr2027_conference.tex", "limit": 330, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-330 of 463 | next offset 330 @@

\documentclass{article} % For LaTeX2e
\usepackage{iclr2027_conference,times}

% Optional math commands from https://github.com/goodfeli/dlbook_notation.
\input{math_commands.tex}

\usepackage{hyperref}
\usepackage{url}


\title{Formatting Instructions for ICLR 2027 \\ Conference Submissions}

% Authors must not appear in the submitted version. They should be hidden
% as long as the \iclrfinalcopy macro remains commented out below.
% Non-anonymous submissions will be rejected without review.

\author{Antiquus S.~Hippocampus, Natalia Cerebro \&amp; Amelie P. Amygdale \thanks{ Use footnote for providing further information
about author (webpage, alternative address)---\emph{not} for acknowledging
funding agencies.  Funding acknowledgements go at the end of the paper.} \\
Department of Computer Science\\
Cranberry-Lemon University\\
Pittsburgh, PA 15213, USA \\
\texttt{\{hippo,brain,jen\}@cs.cranberry-lemon.edu} \\
\And
Ji Q. Ren \&amp; Yevgeny LeNet \\
Department of Computational Neuroscience \\
University of the Witwatersrand \\
Joburg, South Africa \\
\texttt{\{robot,net\}@wits.ac.za} \\
\AND
Coauthor \\
Affiliation \\
Address \\
\texttt{email}
}

% The \author macro works with any number of authors. There are two commands
% used to separate the names and addresses of multiple authors: \And and \AND.
%
% Using \And between authors leaves it to \LaTeX{} to determine where to break
% the lines. Using \AND forces a linebreak at that point. So, if \LaTeX{}
% puts 3 of 4 authors names on the first line, and the last on the second
% line, try using \AND instead of \And before the third author name.

\newcommand{\fix}{\marginpar{FIX}}
\newcommand{\new}{\marginpar{NEW}}

%\iclrfinalcopy % Uncomment for camera-ready version, but NOT for submission.
\begin{document}


\maketitle

\begin{abstract}
The abstract paragraph should be indented 1/2~inch (3~picas) on both left and
right-hand margins. Use 10~point type, with a vertical spacing of 11~points.
The word \textsc{Abstract} must be centered, in small caps, and in point size 12. Two
line spaces precede the abstract. The abstract must be limited to one
paragraph.
\end{abstract}

\section{Submission of conference papers to ICLR 2027}

ICLR requires electronic submissions, processed by
\url{https://openreview.net/}. See ICLR's website for more instructions.

If your paper is ultimately accepted, the statement {\tt
  {\textbackslash}iclrfinalcopy} should be inserted to adjust the
format to the camera ready requirements.

The format for the submissions is a variant of the NeurIPS format.
Please read carefully the instructions below, and follow them
faithfully.

\subsection{Style}

Papers to be submitted to ICLR 2027 must be prepared according to the
instructions presented here.

%% Please note that we have introduced automatic line number generation
%% into the style file for \LaTeXe. This is to help reviewers
%% refer to specific lines of the paper when they make their comments. Please do
%% NOT refer to these line numbers in your paper as they will be removed from the
%% style file for the final version of accepted papers.

Authors are required to use the ICLR \LaTeX{} style files obtainable at the
ICLR website. Please make sure you use the current files and
not previous versions. Tweaking the style files may be grounds for rejection.

\subsection{Retrieval of style files}

The style files for ICLR and other conference information are available online at:
\begin{center}
   \url{http://www.iclr.cc/}
\end{center}
The file \verb+iclr2027_conference.pdf+ contains these
instructions and illustrates the
various formatting requirements your ICLR paper must satisfy.
Submissions must be made using \LaTeX{} and the style files
\verb+iclr2027_conference.sty+ and \verb+iclr2027_conference.bst+ (to be used with \LaTeX{}2e). The file
\verb+iclr2027_conference.tex+ may be used as a ``shell'' for writing your paper. All you
have to do is replace the author, title, abstract, and text of the paper with
your own.

The formatting instructions contained in these style files are summarized in
sections \ref{gen_inst}, \ref{headings}, and \ref{others} below.

\section{General formatting instructions}
\label{gen_inst}

The text must be confined within a rectangle 5.5~inches (33~picas) wide and
9~inches (54~picas) long. The left margin is 1.5~inch (9~picas).
Use 10~point type with a vertical spacing of 11~points. Times New Roman is the
preferred typeface throughout. Paragraphs are separated by 1/2~line space,
with no indentation.

Paper title is 17~point, in small caps and left-aligned.
All pages should start at 1~inch (6~picas) from the top of the page.

Authors' names are
set in boldface, and each name is placed above its corresponding
address. The lead author's name is to be listed first, and
the co-authors' names are set to follow. Authors sharing the
same address can be on the same line.

Please pay special attention to the instructions in section \ref{others}
regarding figures, tables, acknowledgments, and references.


There will be a strict upper limit of \textbf{9 pages} for the main text of the initial submission, with unlimited additional pages for citations. This limit will be expanded to \textbf{10 pages} for rebuttal/camera ready.

\section{Headings: first level}
\label{headings}

First level headings are in small caps,
flush left and in point size 12. One line space before the first level
heading and 1/2~line space after the first level heading.

\subsection{Headings: second level}

Second level headings are in small caps,
flush left and in point size 10. One line space before the second level
heading and 1/2~line space after the second level heading.

\subsubsection{Headings: third level}

Third level headings are in small caps,
flush left and in point size 10. One line space before the third level
heading and 1/2~line space after the third level heading.

\section{Citations, figures, tables, references}
\label{others}

These instructions apply to everyone, regardless of the formatter being used.

\subsection{Citations within the text}

Citations within the text should be based on the \texttt{natbib} package
and include the authors' last names and year (with the ``et~al.'' construct
for more than two authors). When the authors or the publication are
included in the sentence, the citation should not be in parenthesis using \verb|\citet{}| (as
in ``See \citet{Hinton06} for more information.''). Otherwise, the citation
should be in parenthesis using \verb|\citep{}| (as in ``Deep learning shows promise to make progress
towards AI~\citep{Bengio+chapter2007}.'').

The corresponding references are to be listed in alphabetical order of
authors, in the \textsc{References} section. As to the format of the
references themselves, any style is acceptable as long as it is used
consistently.

\subsection{Footnotes}

Indicate footnotes with a number\footnote{Sample of the first footnote} in the
text. Place the footnotes at the bottom of the page on which they appear.
Precede the footnote with a horizontal rule of 2~inches
(12~picas).\footnote{Sample of the second footnote}

\subsection{Figures}

All artwork must be neat, clean, and legible. Lines should be dark
enough for purposes of reproduction; art work should not be
hand-drawn. The figure number and caption always appear after the
figure. Place one line space before the figure caption, and one line
space after the figure. The figure caption is lower case (except for
first word and proper nouns); figures are numbered consecutively.

Make sure the figure caption does not get separated from the figure.
Leave sufficient space to avoid splitting the figure and figure caption.

You may use color figures.
However, it is best for the
figure captions and the paper body to make sense if the paper is printed
either in black/white or in color.
\begin{figure}[h]
\begin{center}
%\framebox[4.0in]{$\;$}
\fbox{\rule[-.5cm]{0cm}{4cm} \rule[-.5cm]{4cm}{0cm}}
\end{center}
\caption{Sample figure caption.}
\end{figure}

\subsection{Tables}

All tables must be centered, neat, clean and legible. Do not use hand-drawn
tables. The table number and title always appear before the table. See
Table~\ref{sample-table}.

Place one line space before the table title, one line space after the table
title, and one line space after the table. The table title must be lower case
(except for first word and proper nouns); tables are numbered consecutively.

\begin{table}[t]
\caption{Sample table title}
\label{sample-table}
\begin{center}
\begin{tabular}{ll}
\multicolumn{1}{c}{\bf PART}  &amp;\multicolumn{1}{c}{\bf DESCRIPTION}
\\ \hline \\
Dendrite         &amp;Input terminal \\
Axon             &amp;Output terminal \\
Soma             &amp;Cell body (contains cell nucleus) \\
\end{tabular}
\end{center}
\end{table}

\section{Default Notation}

In an attempt to encourage standardized notation, we have included the
notation file from the textbook, \textit{Deep Learning}
\cite{goodfellow2016deep} available at
\url{https://github.com/goodfeli/dlbook_notation/}.  Use of this style
is not required and can be disabled by commenting out
\texttt{math\_commands.tex}.


\centerline{\bf Numbers and Arrays}
\bgroup
\def\arraystretch{1.5}
\begin{tabular}{p{1in}p{3.25in}}
$\displaystyle a$ &amp; A scalar (integer or real)\\
$\displaystyle \va$ &amp; A vector\\
$\displaystyle \mA$ &amp; A matrix\\
$\displaystyle \tA$ &amp; A tensor\\
$\displaystyle \mI_n$ &amp; Identity matrix with $n$ rows and $n$ columns\\
$\displaystyle \mI$ &amp; Identity matrix with dimensionality implied by context\\
$\displaystyle \ve^{(i)}$ &amp; Standard basis vector $[0,\dots,0,1,0,\dots,0]$ with a 1 at position $i$\\
$\displaystyle \text{diag}(\va)$ &amp; A square, diagonal matrix with diagonal entries given by $\va$\\
$\displaystyle \ra$ &amp; A scalar random variable\\
$\displaystyle \rva$ &amp; A vector-valued random variable\\
$\displaystyle \rmA$ &amp; A matrix-valued random variable\\
\end{tabular}
\egroup
\vspace{0.25cm}

\centerline{\bf Sets and Graphs}
\bgroup
\def\arraystretch{1.5}

\begin{tabular}{p{1.25in}p{3.25in}}
$\displaystyle \sA$ &amp; A set\\
$\displaystyle \R$ &amp; The set of real numbers \\
$\displaystyle \{0, 1\}$ &amp; The set containing 0 and 1 \\
$\displaystyle \{0, 1, \dots, n \}$ &amp; The set of all integers between $0$ and $n$\\
$\displaystyle [a, b]$ &amp; The real interval including $a$ and $b$\\
$\displaystyle (a, b]$ &amp; The real interval excluding $a$ but including $b$\\
$\displaystyle \sA \backslash \sB$ &amp; Set subtraction, i.e., the set containing the elements of $\sA$ that are not in $\sB$\\
$\displaystyle \gG$ &amp; A graph\\
$\displaystyle \parents_\gG(\ervx_i)$ &amp; The parents of $\ervx_i$ in $\gG$
\end{tabular}
\vspace{0.25cm}


\centerline{\bf Indexing}
\bgroup
\def\arraystretch{1.5}

\begin{tabular}{p{1.25in}p{3.25in}}
$\displaystyle \eva_i$ &amp; Element $i$ of vector $\va$, with indexing starting at 1 \\
$\displaystyle \eva_{-i}$ &amp; All elements of vector $\va$ except for element $i$ \\
$\displaystyle \emA_{i,j}$ &amp; Element $i, j$ of matrix $\mA$ \\
$\displaystyle \mA_{i, :}$ &amp; Row $i$ of matrix $\mA$ \\
$\displaystyle \mA_{:, i}$ &amp; Column $i$ of matrix $\mA$ \\
$\displaystyle \etA_{i, j, k}$ &amp; Element $(i, j, k)$ of a 3-D tensor $\tA$\\
$\displaystyle \tA_{:, :, i}$ &amp; 2-D slice of a 3-D tensor\\
$\displaystyle \erva_i$ &amp; Element $i$ of the random vector $\rva$ \\
\end{tabular}
\egroup
\vspace{0.25cm}


\centerline{\bf Calculus}
\bgroup
\def\arraystretch{1.5}
\begin{tabular}{p{1.25in}p{3.25in}}
% NOTE: the [2ex] on the next line adds extra height to that row of the table.
% Without that command, the fraction on the first line is too tall and collides
% with the fraction on the second line.
$\displaystyle\frac{d y} {d x}$ &amp; Derivative of $y$ with respect to $x$\\ [2ex]
$\displaystyle \frac{\partial y} {\partial x} $ &amp; Partial derivative of $y$ with respect to $x$ \\
$\displaystyle \nabla_\vx y $ &amp; Gradient of $y$ with respect to $\vx$ \\
$\displaystyle \nabla_\mX y $ &amp; Matrix derivatives of $y$ with respect to $\mX$ \\
$\displaystyle \nabla_\tX y $ &amp; Tensor containing derivatives of $y$ with respect to $\tX$ \\
$\displaystyle \frac{\partial f}{\partial \vx} $ &amp; Jacobian matrix $\mJ \in \R^{m\times n}$ of $f: \R^n \rightarrow \R^m$\\
$\displaystyle \nabla_\vx^2 f(\vx)\text{ or }\mH( f)(\vx)$ &amp; The Hessian matrix of $f$ at input point $\vx$\\
$\displaystyle \int f(\vx) d\vx $ &amp; Definite integral over the entire domain of $\vx$ \\
$\displaystyle \int_\sS f(\vx) d\vx$ &amp; Definite integral with respect to $\vx$ over the set $\sS$ \\
\end{tabular}
\egroup
\vspace{0.25cm}

\centerline{\bf Probability and Information Theory}
\bgroup
\def\arraystretch{1.5}
\begin{tabular}{p{1.25in}p{3.25in}}
$\displaystyle P(\ra)$ &amp; A probability distribution over a discrete variable\\
$\displaystyle p(\ra)$ &amp; A probability distribution over a continuous variable, or over
a variable whose type has not been specified\\
$\displaystyle \ra \sim P$ &amp; Random variable $\ra$ has distribution $P$\\% so thing on left of \sim should always be a random variable, with name beginning with \r
$\displaystyle  \E_{\rx\sim P} [ f(x) ]\text{ or } \E f(x)$ &amp; Expectation of $f(x)$ with respect to $P(\rx)$ \\
$\displaystyle \Var(f(x)) $ &amp;  Variance of $f(x)$ under $P(\rx)$ \\
$\displaystyle \Cov(f(x),g(x)) $ &amp; Covariance of $f(x)$ and $g(x)$ under $P(\rx)$\\
$\displaystyle H(\rx) $ &amp; Shannon entropy of the random variable $\rx$\\
$\displaystyle \KL ( P \Vert Q ) $ &amp; Kullback-Leibler divergence of P and Q \\
$\displaystyle \mathcal{N} ( \vx ; \vmu , \mSigma)$ &amp; Gaussian distribution %
over $\vx$ with mean $\vmu$ and covariance $\mSigma$ \\
\end{tabular}
\egroup
\vspace{0.25cm}
</message>
<message type="ai">
  <tool_call id="call_672068db46724df58df3f22abe1f3eea" name="read_file">{"file_path": "/work/literature/2107.07511_consulted.txt", "limit": 600, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-426 of 426 @@
=== PDF PAGE 11 ===
Let us ﬁrst describe what a Bayesian would do, given a Bayesian model ˆf(y| x), which estimates the
value of the posterior distribution of Ytest at label y with input Xtest =x. If one believed all the necessary
assumptions—mainly, a correctly speciﬁed model and asymptotically large n—the following would be the
optimal prediction set:
S(x) =
{
y : ˆf(y|x)&gt;t
}
, where t is chosen so
∫
y∈S(x)
ˆf(y|x)dy = 1−α.
However, because we cannot make assumptions on the model and data, we can only consider ˆf(y|x) to be
a heuristic notion of uncertainty.
Following our now-familiar checklist, we can deﬁne a conformal score,
s(x,y ) =− ˆf(y|x),
which is high when the model is uncertain and otherwise low. After computing ˆ q over the calibration data,
we can then construct prediction sets:
C(x) =
{
y : ˆf(y|x)&gt;−ˆq
}
. (6)
prediction set
Figure 9: A visualization of the conformalized Bayes algorithm in Eq. (6). The prediction set is a
superlevel set of the posterior predictive density.
This set is valid because we chose the threshold ˆq via conformal prediction. Furthermore, when certain
technical assumptions are satisﬁed, it has the best Bayes risk among all prediction sets with 1 −α coverage.
To be more precise, under the assumptions in [11], C(Xtest) has the smallest average size of any conformal
procedure with 1−α coverage, where the average is taken over the data and the parameters. This result
should not be a surprise to those familiar with decision theory, as the argument we are making feels similar
to that of the Neyman-Pearson lemma. This concludes the ﬁnal example.
Discussion
As our examples have shown, conformal prediction is a simple and pragmatic technique with many use
cases. It is also easy to implement and computationally trivial. Additionally, the above four examples serve
as roadmaps to the user for designing score functions with various notions of optimality, including average
size, adaptivity, and Bayes risk. Still more is yet to come—conformal prediction can be applied more broadly
than it may ﬁrst seem at this point. We will outline extensions of conformal prediction to other prediction
tasks such as outlier detection, image segmentation, serial time-series prediction, and so on in Section 4.
Before addressing these extensions, we will take a deep dive into diagnostics for conformal prediction in the
standard setting, including the important topic of conditional coverage.
3 Evaluating Conformal Prediction
We have spent the last two sections learning how to form valid prediction sets satisfying rigorous statistical
guarantees. Now we will discuss how to evaluate them. Our evaluations will fall into one of two categories.
11

=== PDF PAGE 12 ===
1. Evaluating adaptivity. It is extremely important to keep in mind that the conformal prediction
procedure with the smallest average set size is not necessarily the best. A good conformal prediction
procedure will give small sets on easy inputs and large sets on hard inputs in a way that faithfully
reﬂects the model’s uncertainty. This adaptivity is not implied by conformal prediction’s coverage
guarantee, but it is non-negotiable in practical deployments of conformal prediction. We will formalize
adaptivity, explore its consequences, and suggest practical algorithms for evaluating it.
2. Correctness checks. Correctness checks help you test whether you’ve implemented conformal predic-
tion correctly. We will empirically check that the coverage satisﬁes Theorem 1. Rigorously evaluating
whether this property holds requires a careful accounting of the ﬁnite-sample variability present with
real datasets. We develop explicit formulae for the size of the benign ﬂuctuations—if one observes
deviations from 1−α in coverage that are larger than these formulae dictate, then there is a problem
with the implementation.
Many of the evaluations we suggest are computationally intensive, and require running the entire confor-
mal procedure on diﬀerent splits of data at least 100 times. Na¨ ıve implementations of these evaluations can
be slow when the score takes a long time to compute. With some simple computational tricks and strategic
caching, we can speed this process up by orders of magnitude. Therefore to aid the reader, we intersperse
the mathematical descriptions with code to eﬃciently implement these computations.
3.1 Evaluating Adaptivity
Although any conformal procedure yields prediction intervals that satisfy (1), there are many such procedures,
and they diﬀer in other important ways. In particular, a key design consideration for conformal prediction
is adaptivity: we want the procedure to return larger sets for harder inputs and smaller sets for easier
inputs. While most reasonable conformal procedures will satisfy this to some extent, we now discuss precise
metrics for adaptivity that allow the user to check a conformal procedure and to compare multiple alternative
conformal procedures.
Set size. The ﬁrst step is to plot histograms of set sizes. This histogram helps us in two ways. Firstly,
a large average set size indicates the conformal procedure is not very precise, indicating a possible problem
with the score or underlying model. Secondly, the spread of the set sizes shows whether the prediction sets
properly adapt to the diﬃculty of examples. A wider spread is generally desirable, since it means that the
procedure is eﬀectively distinguishing between easy and hard inputs.
set size
#
set size
#
It can be tempting to stop evaluations after plotting the coverage and set size, but certain important
questions remain unanswered. A good spread of set sizes is generally better, but it does not necessarily
indicate that the sets adapt properly to the diﬃculty of X. Above seeing that the set sizes have dynamic
range, we will need to verify that large sets occur for hard examples. We next formalize this notion and give
metrics for evaluating it.
Conditional coverage. Adaptivity is typically formalized by asking for the conditional coverage [14]
property:
P [Ytest∈C (Xtest)|Xtest]≥ 1−α. (7)
12

=== PDF PAGE 13 ===
That is, for every value of the input Xtest, we seek to return prediction sets with 1 −α coverage. This is
a stronger property than the marginal coverage property in (1) that conformal prediction is guaranteed to
achieve—indeed, in the most general case, conditional coverage is impossible to achieve [14]. In other words,
conformal procedures are not guaranteed to satisfy (7), so we must check how close our procedure comes to
approximating it.
The diﬀerence between marginal and conditional coverage is subtle but of great practical importance, so
we will spend some time think about the diﬀerences here. Imagine there are two groups of people, group A
and group B, with frequencies 90% and 10%. The prediction sets always cover Y among people in group A
and never cover Y when the person comes from group B. Then the prediction sets have 90% coverage, but
not conditional coverage. Conditional coverage would imply that the prediction sets cover Y at least 90% of
the time in both groups. This is necessary, but not suﬃcient; conditional coverage is a very strong property
that states the probability of the prediction set needs to be ≥ 90% for a particular person . In other words,
for any subset of the population, the coverage should be ≥ 90%. See Figure 10 for a visualization of the
diﬀerence between conditional and marginal coverage.
errors by group
regression
no coverage
5% coverage
Group 1 Group 1 Group 1Group 2 Group 2 Group 2
marginal conditional
14% coverage 100% coverage 80% coverage 90% coverage 90% coverage
correctly covered example
incorrectly covered example
Figure 10: Prediction sets with various notions of coverage: no coverage, marginal coverage, or
conditional coverage (at a level of 90%). In the marginal case, all the errors happen in the same groups and
regions in X-space. Conditional coverage disallows this behavior, and errors are evenly distributed.
Feature-stratiﬁed coverage metric. As a ﬁrst metric for conditional coverage, we will formalize the
example we gave earlier, where coverage is unequal over some groups. The reader can think of these groups
as discrete categories, like race, or as a discretization of continuous features, like age ranges. Formally,
suppose we have features X(val)i,1 that take values in{1,...,G } for some G. (Here, i = 1,...,n val indexes the
example in the validation set, and the ﬁrst coordinate of each feature is the group.) Let Ig⊂{ 1,...,n val}
be the set of observations such that X(val)i,1 =g for g = 1,...,G . Since conditional coverage implies that the
procedure has the same coverage for all values of Xtest, we use the following measure:
FSC metric : min
g∈{1,...,G}
1
|Ig|
∑
i∈Ig
1
{
Y (val)i ∈C(X(val)i )}
In words, this is the observed coverage among all instances where the discrete feature takes the value g. If
conditional coverage were achieved, this would be 1 −α, and values farther below 1 −α indicate a greater
violation of conditional coverage. Note that this metric can also be used with a continuous feature by binning
the features into a ﬁnite number of categories.
13

=== PDF PAGE 14 ===
Size-stratiﬁed coverage metric. We next consider a more general-purpose metric for how close a confor-
mal procedure comes to satisfying (7), introduced in [4]. First, we discretize the possible cardinalities ofC(x),
into G bins, B1,...,B G. For example, in classiﬁcation we might divide the observations into three groups,
depending on whetherC(x) has one element, two elements, or more than two elements. LetIg⊂{ 1,...,n val}
be the set of observations falling in bin g for g = 1,...,G . Then we consider the following
SSC metric : min
g∈{1,...,G}
1
|Ig|
∑
i∈Ig
1
{
Y (val)i ∈C(X(val)i )}
In words, this is the observed coverage for all units for which the set size |C(x)| falls into bin g. As before,
if conditional coverage were achieved, this would be 1−α, and values farther below 1−α indicate a greater
violation of conditional coverage. Note that this is the same expression as for the FSC metric, except that
the deﬁnition ofIg has changed. Unlike the FSC metric, the user does not have to deﬁne an important set
of discrete features a-priori—it is a general metric that can apply to any example.
See [15] and [16] for additional metrics of conditional coverage.
3.2 The Eﬀect of the Size of the Calibration Set
We ﬁrst pause to discuss how the size of the calibration set aﬀects conformal prediction. We consider this
question for two reasons. First, the user must choose this for a practical deployment. Roughly speaking, our
conclusion will that be choosing a calibration set of size n = 1000 is suﬃcient for most purposes. Second, the
size of the calibration set is one source of ﬁnite-sample variability that we will need to analyze to correctly
check the coverage. We will build on the results here in the next section, where we give a complete description
of how to check coverage in practice.
How does the size of the calibration set, n, aﬀect conformal prediction? The coverage guarantee in (1)
holds for any n, so we can see that our prediction sets have coverage at least 1 −α even with a very small
calibration set. Intuitively, however, it may seem that largern is better, and leads to more stable procedures.
This intuition is correct, and it explains why using a larger calibration set is beneﬁcial in practice. The details
are subtle, so we carefully work through them here.
The key idea is that the coverage of conformal prediction conditionally on the calibration set is a random
quantity. That is, if we run the conformal prediction algorithm twice, each time sampling a new calibration
dataset, then check the coverage on an inﬁnite number of validation points, those two numbers will not be
equal. The coverage property in (1) says that coverage will be at least 1−α on average over the randomness
in the calibration set, but with any one ﬁxed calibration set, the coverage on an inﬁnite validation set will
be some number that is not exactly 1 −α. Nonetheless, we can choose n large enough to control these
ﬂuctuations in coverage by analyzing its distribution.
In particular, the distribution of coverage has an analytic form, ﬁrst introduced by Vladimir Vovk in [14],
namely,
P
(
Ytest∈C (Xtest)
⏐⏐{(Xi,Yi)}ni=1)∼ Beta (n + 1−l,l ),
where
l =⌊(n + 1)α⌋.
Notice that the conditional expectation above is the coverage with an inﬁnite validation data set, holding the
calibration data ﬁxed. A simple proof of this fact is available in [14]. We plot the distribution of coverage
for several values of n in Figure 11.
Inspecting Figure 11, we see that choosing n = 1000 calibration points leads to coverage that is typically
between .88 and .92, hence our rough guideline of choosing about 1000 calibration points. More formally,
we can compute exactly the number of calibration points n needed to achieve a coverage of 1 −α±ϵ with
probability 1−δ. Again, the average coverage is always at least 1 −α; the parameter δ controls the tail
probabilities of the coverage conditionally on the calibration data. For any δ, the required calibration set
size n can be explicitly computed from a simple expression, and we report on several values in Table 1 for
the reader’s reference. Code allowing the user to produce results for any choice of n andα accompanies the
table.
14

=== PDF PAGE 15 ===
0.82 0.84 0.86 0.88 0.90 0.92 0.94 0.96 0.98
Distribution of coverage (infinite validation set)
n=100
n=1000
n=10000
1
Figure 11: The distribution of coverage with an inﬁnite validation set is plotted for diﬀerent values of
n with α = 0.1. The distribution converges to 1−α with rateO
(
n−1/2).
ϵ 0.1 0.05 0.01 0.005 0.001
n(ϵ) 22 102 2491 9812 244390
Table 1: Calibration set size n(ϵ) required for coverage slack ϵ with δ = 0.1 and α = 0.1.
3.3 Checking for Correct Coverage
As an obvious diagnostic, the user will want to assess whether the conformal procedure has the correct
coverage. This can be accomplished by running the procedure over R trials with new calibration and
validation sets, and then calculating the empirical coverage for each,
Cj = 1nval
nval∑
i=1
1
{
Y (val)i,j ∈C j
(
X(val)i,j
)}
, for j = 1,...,R,
where nval is the size of the validation set, ( X(val)i,j ,Y (val)i,j ) is the ith validation example in trial j, andCj is
calibrated using the calibration data from the jth trial. A histogram of the Cj should be centered at roughly
1−α, as in Figure 11. Likewise, the mean value,
C = 1R
R∑
j=1
Cj,
should be approximately 1−α.
With real datasets, we only have n +nval data points total to evaluate our conformal algorithm and
therefore cannot draw new data for each of the R rounds. So, we compute the coverage values by randomly
splitting the n +nval data points R times into calibration and validation datasets, then running conformal.
Notice that rather than splitting the data points themselves many times, we can instead ﬁrst cache all
conformal scores and then compute the coverage values over many random splits, as in the code sample in
Figure 12.
If properly implemented, conformal prediction is guaranteed to satisfy the inequality in (1). However, if
the reader sees minor ﬂuctuations in the observed coverage, they may not need to worry: the ﬁniteness of
n, nval, and R can lead to benign ﬂuctuations in coverage which add some width to the Beta distribution
in Figure 11. Appendix C gives exact theory for analyzing the mean and standard deviation of C. From
this, we will be able to tell if any deviation from 1 −α indicates a problem with the implementation, or
15

=== PDF PAGE 16 ===
try: # try loading the scores first
scores = np.load('scores.npy')
except:
# X and Y have n + n_val rows each
scores = get_scores(X,Y)
np.save(scores, 'scores.npy')
# calculate the coverage R times and store in list
coverages = np.zeros((R,))
for r in range(R):
np.random.shuffle(scores) # shuffle
calib_scores, val_scores = (scores[:n],scores[n:]) # split
qhat = np.quantile(calib_scores, np.ceil((n+1)*(1-alpha)/n), method='higher') # calibrate
coverages[r] = (val_scores &lt;= qhat).astype(float).mean() # see caption
average_coverage = coverages.mean() # should be close to 1-alpha
plt.hist(coverages) # should be roughly centered at 1-alpha
Figure 12: Python code for computing coverage with eﬃcient score caching. Notice that from the
expression for conformal sets in (2), a validation point is covered if and only if s(X,Y )≤ ˆq, which is how
the third to last line is succinctly computing the coverage.
if it is benign. Code for checking the coverage at all diﬀerent values of n, nval, and R is available in the
accompanying Jupyter notebook of Figure 12.
4 Extensions of Conformal Prediction
At this point, we have seen the core of the matter: how to construct prediction sets with coverage in
any standard supervised prediction problem. We now broaden our horizons towards prediction tasks with
diﬀerent structure, such as side information, covariate shift, and so on. These more exotic problems arise
quite frequently in the real world, so we present practical conformal algorithms to address them.
4.1 Group-Balanced Conformal Prediction
In certain settings, we might want prediction intervals that have equal error rates across certain subsets of
the data. For example, we may require our medical classiﬁer to have coverage that is correct for all racial
and ethnic groups. To formalize this, we suppose that the ﬁrst feature of our inputs, Xi,1, i = 1,...,n takes
values in some discrete set {1,...,G} corresponding to categorical groups. We then ask for group-balanced
coverage:
P (Ytest∈C (Xtest)|Xtest,1 =g)≥ 1−α, (8)
for all groups g∈{ 1,...,G }. In words, this means we have a 1−α coverage rate for all groups. Notice that
the group output could be a post-processing of the original features in the data. For example, we might bin
the values of Xtest into a discrete set.
Recall that a standard application of conformal prediction will not necessarily yield coverage within each
group simultaneously—that is, (8) may not be satisﬁed. We saw an example in Figure 10; the marginal
guarantee from normal conformal prediction can still be satisﬁed even if all errors happen in one group.
In order to achieve group-balanced coverage, we will simply run conformal prediction seperately for each
group, as visualized below.
16

=== PDF PAGE 17 ===
Making this formal, given a conformal score function s, we stratify the scores on the calibration set by
group,
s(g)i =s(Xj,Yj), where Xj,1 is the ith occurrence of group g.
Then, within each group, we calculate the conformal quantile
ˆq(g) = Quantile
(
s1,...,s n(g);
⌈
(n(g) + 1)(1−α)⌉
n(g)
)
, where n(g) is the number of examples of group g.
Finally, we form prediction sets by ﬁrst picking the relevant quantile,
C(x) =
{
y :s(x,y )≤ ˆq(x1)
}
.
That is, for a point x that we see falls in group x1, we use the threshold ˆq(x1) to form the prediction set, and
so on. This choice of C satisﬁes (8), as was ﬁrst documented by Vovk in [14].
Proposition 1 (Error control guarantee for group-balanced conformal prediction) . Suppose (X1,Y 1),...,
(Xn,Yn), (Xtest,Ytest) are an i.i.d. sample from some distribution. Then the set C deﬁned above satisﬁes the
error control property in (8).
4.2 Class-Conditional Conformal Prediction
In classiﬁcation problems, we might similarly ask for coverage onevery ground truth class. For example, if we
had a medical classiﬁer assigning inputs to class normal or class cancer, we might ask that the prediction sets
are 95% accurate both when the ground truth is class cancer and also when the ground truth is class normal.
Formally, we return to the classiﬁcation setting, where Y ={1,...,K}. We seek to achieve class-balanced
coverage,
P (Ytest∈C (Xtest)|Ytest =y)≥ 1−α, (9)
for all classes y∈{ 1,...,K }.
To achieve class-balanced coverage, we will calibrate within each class separately. The algorithm will be
similar to the group-balanced coverage of Section 4.1, but we must modify it because we do not know the
correct class at test time. (In contrast, in Section 4.1, we observed the group information Xtest,1 as an input
feature.) See the visualization below.
17

=== PDF PAGE 20 ===
Proposition 3 (Error control guarantee for outlier detection). SupposeX1,...,X n,X test are an i.i.d. sam-
ple from some distribution. Then the set C deﬁned above satisﬁes the error control property in (14).
As with standard conformal prediction, the score function is very important for the method to perform
well—that is, to be eﬀective at ﬂagging outliers. Here, we wish to choose the score function to eﬀectively
distinguish the type of outliers that we expect to see in the test data from the clean data. The general
problem of training models to distinguish outliers is sometimes called anomaly detection, novelty detection,
or one-class classiﬁcation, and there are good out-of-the box methods for doing this; see [19] for an overview
of outlier detection. Conformal outlier detection can also be seen as a hypothesis testing problem; points
that are rejected as outliers have a p-value less thanalpha for the null hypothesis of exchangeability with the
calibration data. This interpretation is closely related to the classical permutation test [20, 21]. See [22–24]
for more on this interpretation and other statistical properties of conformal outlier detection.
4.5 Conformal Prediction Under Covariate Shift
All previous conformal methods rely on Theorem 1, which assumes that the incoming test points come from
the same distribution as the calibration points. However, past data is not necessarily representative of future
data in practice.
One type of distribution shift that conformal prediction can handle is covariate shift. Covariate shift
refers to the situation where the distribution of Xtest changes fromP toPtest, but the relationship between
Xtest and Ytest, i.e. the distribution of Ytest|Xtest, stays ﬁxed.
Imagine our calibration features {Xi}ni=1 are drawn independently from P but our test feature Xtest is
drawn fromPtest. Then, there has been a covariate shift, and the data are no longer i.i.d. This problem is
common in the real world. For example,
• You are trying to predict diseases from MRI scans. You conformalized on a balanced dataset of 50%
infants and 50% adults, but in reality, the frequency is 5% infants and 95% adults. Deploying the
model in the real world would invalidate coverage; the infants are over-represented in our sample, so
diseases present during infancy will be over-predicted. This was a covariate shift in age.
• You are trying to do instance segmentation, i.e., to segment each object in an image from the back-
ground. You collected your calibration images in the morning but seek to deploy your system in the
afternoon. The amount of sunlight has changed, and more people are eating lunch. This was a covariate
shift in the time of day.
To address the covariate shift from P toPtest, one can form valid prediction sets with weighted conformal
prediction, ﬁrst developed in [25].
In weighted conformal prediction, we account for covariate shift by upweighting conformal scores from
calibration points that would be more likely under the new distribution. We will be using the likelihood ratio
w(x) = dPtest(x)dP(x) ;
20

=== PDF PAGE 50 ===
0.896 0.898 0.900 0.902 0.904
Distribution of C with n = 1000, nval = 1000
0.896 0.898 0.900 0.902 0.904
Distribution of C with n = 10000, nval = 10000
R = 100
R = 1000
R = 10000
Figure 26: The distribution of average empirical coverage over R trials with n calibration points
and nval validation points.
Furthermore, we can analytically reason about the tail properties of C. Since C is the average of R i.i.d.
beta-binomial random variables, its mean and standard deviation are
E
(
C
)
= 1− ln + 1 and
√
Var
(
C
)
=
√
l(n + 1−l)(n +nval + 1)
nvalR(n + 1)2(n + 2) =O
(
1√
R min(n,n val)
)
.
The best way for a practitioner to carefully debug their procedure is to compute C empirically, and then
cross-reference with Figure 26. We give code to simulate histograms with any n, R, and nval in the linked
notebook of Figure 26. If the simulated average empirical coverage does not align well with the coverage
observed on the real data, there is likely a problem in the conformal implementation.
D Theorem and Proof: Coverage Property of Conformal Predic-
tion
This is a standard proof of validity for split-conformal prediction ﬁrst appearing in [2], but we reproduce it
here for completeness. Let us begin with the lower bound.
Theorem D.1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi)i=1,...,n and (Xtest,Y test) are
i.i.d. Then deﬁne ˆq as
ˆq = inf
{
q :|{i :s(Xi,Yi)≤q}|n ≥⌈(n + 1)(1−α)⌉n }.
and the resulting prediction sets as
C(X) ={y :s(X,y )≤ ˆq}.
Then,
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
This is the same coverage property as (1) in the introduction, but written more formally. As a technical
remark, the theorem also holds if the observations to satisfy the weaker condition of exchangeability; see [1].
Below, we prove the lower bound.
Proof of Theorem 1. Letsi =s(Xi,Yi) fori = 1,...,n andstest =s(Xtest,Y test). To avoid handling ties, we
consider the case where the si are distinct with probability 1. See [25] for a proof in the general case.
50</message>
<message type="ai">
  <content><reasoning>**Capturing stable sections**</reasoning></content>
  <tool_call id="call_fd10d6685ea64b5fb191a47a0e81f237" name="read_file">{"file_path": "/work/literature/2107.07511.txt", "limit": 240, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-240 of 2462 | next offset 240 @@
=== PDF PAGE 1 ===
A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantiﬁcation
Anastasios N. Angelopoulos and Stephen Bates
December 8, 2022
Abstract
Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-
tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-
tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty
sets/intervals for the predictions of such models. Critically, the sets are valid in a distribution-free sense:
they possess explicit, non-asymptotic guarantees even without distributional assumptions or model as-
sumptions. One can use conformal prediction with any pre-trained model, such as a neural network, to
produce sets that are guaranteed to contain the ground truth with a user-speciﬁed probability, such as
90%. It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the
ﬁelds of computer vision, natural language processing, deep reinforcement learning, and so on.
This hands-on introduction is aimed to provide the reader a working understanding of conformal
prediction and related distribution-free uncertainty quantiﬁcation techniques with one self-contained
document. We lead the reader through practical theory for and examples of conformal prediction and
describe its extensions to complex machine learning tasks involving structured outputs, distribution
shift, time-series, outliers, models that abstain, and more. Throughout, there are many explanatory
illustrations, examples, and code samples in Python. With each code sample comes a Jupyter notebook
implementing the method on a real-data example; the notebooks can be accessed and easily run by
clicking on the following icons:
 .
1
arXiv:2107.07511v6  [cs.LG]  7 Dec 2022

=== PDF PAGE 2 ===
Contents
1 Conformal Prediction 4
1.1 Instructions for Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 Examples of Conformal Procedures 6
2.1 Classiﬁcation with Adaptive Prediction Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.2 Conformalized Quantile Regression . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.3 Conformalizing Scalar Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.1 The Estimated Standard Deviation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.2 Other 1-D Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.4 Conformalizing Bayes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Evaluating Conformal Prediction 11
3.1 Evaluating Adaptivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 The Eﬀect of the Size of the Calibration Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
3.3 Checking for Correct Coverage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
4 Extensions of Conformal Prediction 16
4.1 Group-Balanced Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Class-Conditional Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Conformal Risk Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Outlier Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
4.5 Conformal Prediction Under Covariate Shift . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
4.6 Conformal Prediction Under Distribution Drift . . . . . . . . . . . . . . . . . . . . . . . . . . 21
5 Worked Examples 23
5.1 Multilabel Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.2 Tumor Segmentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.3 Weather Prediction with Time-Series Distribution Shift . . . . . . . . . . . . . . . . . . . . . 24
5.4 Toxic Online Comment Identiﬁcation via Outlier Detection . . . . . . . . . . . . . . . . . . . 25
5.5 Selective Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
6 Full conformal prediction 27
6.1 Full Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.2 Cross-Conformal Prediction, CV+, and Jackknife+ . . . . . . . . . . . . . . . . . . . . . . . . 28
7 Historical Notes on Conformal Prediction 28
A Distribution-Free Control of General Risks 39
A.1 Instructions for Learn then Test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
2

=== PDF PAGE 3 ===
A.1.1 Crash Course on Generating p-values . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
A.1.2 Crash Course on Familywise-Error Rate Algorithms . . . . . . . . . . . . . . . . . . . 44
B Examples of Distribution-Free Risk Control 45
B.1 Multi-label Classiﬁcation with FDR Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
B.2 Simultaneous Guarantees on OOD Detection and Coverage . . . . . . . . . . . . . . . . . . . 46
C Concentration Properties of the Empirical Coverage 49
D Theorem and Proof: Coverage Property of Conformal Prediction 50
3

=== PDF PAGE 4 ===
Figure 1: Prediction set examples on Imagenet. We show three progressively more diﬃcult examples
of the class fox squirrel and the prediction sets (i.e., C(Xtest)) generated by conformal prediction.
1 Conformal Prediction
Conformal prediction [1–3] (a.k.a. conformal inference) is a straightforward way to generate prediction sets
for any model. We will introduce it with a short, pragmatic image classiﬁcation example, and follow up in
later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows.
First, we begin with a ﬁtted predicted model (such as a neural network classiﬁer) which we will call ˆf. Then,
we will create prediction sets (a set of possible labels) for this classiﬁer using a small amount of additional
calibration data—we will sometimes call this the calibration step.
Formally, suppose we have images as input and they each contain one of K classes. We begin with
a classiﬁer that outputs estimated probabilities (softmax scores) for each class: ˆf(x)∈ [0, 1]K. Then, we
reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training,
(X1,Y 1),..., (Xn,Yn), for use as calibration data. Using ˆf and the calibration data, we seek to construct a
prediction set of possible labels C(Xtest)⊂{ 1,...,K } that is valid in the following sense:
1−α≤ P(Ytest∈C (Xtest))≤ 1−α + 1n + 1, (1)
where (Xtest,Y test) is a fresh test point from the same distribution, and α∈ [0, 1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1 −α; we call
this property marginal coverage, since the probability is marginal (averaged) over the randomness in the
calibration and test points. See Figure 1 for examples of prediction sets on the Imagenet dataset.
To constructC from ˆf and the calibration data, we will perform a simple calibration step that requires
only a few lines of code; see the right panel of Figure 2. We now describe the calibration step in more detail,
introducing some terms that will be helpful later on. First, we set the conformal scoresi = 1− ˆf(Xi)Yi to be
one minus the softmax output of the true class. The score is high when the softmax output of the true class
is low, i.e., when the model is badly wrong. Next comes the critical step: deﬁne ˆq to be the⌈(n+1)(1−α)⌉/n
empirical quantile of s1,...,s n, where⌈·⌉ is the ceiling function (ˆq is essentially the 1−α quantile, but with
a small correction). Finally, for a new test data point (where Xtest is known but Ytest is not), create a
prediction setC(Xtest) ={y : ˆf(Xtest)y≥ 1− ˆq} that includes all classes with a high enough softmax output
(see Figure 2). Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy (1), no matter
what (possibly incorrect) model is used or what the (unknown) distribution of the data is.
true class
class
softmax output
#
scores,       class
softmax output
(1) compute scores
on holdout data
(2) get quantile (3) construct
prediction set
# 1: get conformal scores. n = calib_Y.shape[0]
cal_smx = model(calib_X).softmax(dim=1).numpy()
cal_scores = 1-cal_smx[np.arange(n),cal_labels]
# 2: get adjusted quantile
q_level = np.ceil((n+1)*(1-alpha))/n
qhat = np.quantile(cal_scores, q_level, method='higher')
val_smx = model(val_X).softmax(dim=1).numpy()
prediction_sets = val_smx &gt;= (1-qhat) # 3: form prediction sets
Figure 2: Illustration of conformal prediction with matching Python code.
4

=== PDF PAGE 5 ===
Remarks
Let us think about the interpretation of C. The function C is set-valued—it takes in an image, and it
outputs a set of classes as in Figure 1. The model’s softmax outputs help to generate the set. This method
constructs a diﬀerent output set adaptively to each particular input . The sets become larger when the model
is uncertain or the image is intrinsically hard. This is a property we want, because the size of the set gives you
an indicator of the model’s certainty. Furthermore, C(Xtest) can be interpreted as a set of plausible classes
that the image Xtest could be assigned to. Finally, C is valid, meaning it satisﬁes (1). 1 These properties of
C translate naturally to other machine learning problems, like regression, as we will see.
With an eye towards generalization, let us review in detail what happened in our classiﬁcation problem.
To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the
jth entry of the softmax vector estimated P(Y = j| X = x), the probability of class j conditionally on
an input image x. However, we had no guarantee that the softmax outputs were any good; they may have
been arbitrarily overﬁt or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face
value, we used the holdout set to adjust for their deﬁciencies.
The holdout set contained n≈ 500 fresh data points that the model never saw during training, which
allowed us to get an honest appraisal of its performance. The adjustment involved computing conformal
scores, which grow when the model is uncertain, but are not valid prediction intervals on their own. In our
case, the conformal score was one minus the softmax output of the true class, but in general, the score can
be any function of x and y. We then took ˆq to be roughly the 1−α quantile of the scores. In this case, the
quantile had a simple interpretation—when setting α = 0.1, at least 90% of ground truth softmax outputs
are guaranteed to be above the level 1 − ˆq (we prove this rigorously in Appendix D). Taking advantage of
this fact, at test-time, we got the softmax outputs of a new image Xtest and collected all classes with outputs
above 1− ˆq into a prediction setC(Xtest). Since the softmax output of the new true class Ytest is guaranteed
to be above 1− ˆq with probability at least 90%, we ﬁnally got the guarantee in Eq. (1).
1.1 Instructions for Conformal Prediction
As we said during the summary, conformal prediction is not speciﬁc to softmax outputs or classiﬁcation
problems. In fact, conformal prediction can be seen as a method for taking any heuristic notion of
uncertainty from any model and converting it to a rigorous one (see the diagram below). Conformal pre-
diction does not care if the underlying prediction problem is discrete/continuous or classiﬁcation/regression.
Heuristic
uncertainty
(per input)
Rigorous
uncertainty
(per input)
conformal
prediction
We next outline conformal prediction for a general input x and output y (not necessarily discrete).
1. Identify a heuristic notion of uncertainty using the pre-trained model.
2. Deﬁne the score function s(x,y )∈ R. (Larger scores encode worse agreement between x and y.)
3. Compute ˆq as the ⌈(n+1)(1−α)⌉n quantile of the calibration scores s1 =s(X1,Y 1),...,s n =s(Xn,Yn).
4. Use this quantile to form the prediction sets for new examples:
C(Xtest) ={y :s(Xtest,y )≤ ˆq}. (2)
As before, these sets satisfy the validity property in (1), for any (possibly uninformative) score function and
(possibly unknown) distribution of the data. We formally state the coverage guarantee next.
1Due to the discreteness of Y , a small modiﬁcation involving tie-breaking is needed to additionally satisfy the upper bound
(see [4] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
5

=== PDF PAGE 6 ===
Theorem 1 (Conformal coverage guarantee; Vovk, Gammerman, and Saunders [5]). Suppose (Xi,Yi)i=1,...,n
and (Xtest,Y test) are i.i.d. and deﬁne ˆq as in step 3 above andC(Xtest) as in step 4 above. Then the following
holds:
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
See Appendix D for a proof and a statement that includes the upper bound in (1). We note that the
above is only a special case of conformal prediction, called split conformal prediction . This is the most
widely-used version of conformal prediction, and it will be our primary focus. To complete the picture, we
describe conformal prediction in full generality later in Section 6 and give an overview of the literature in
Section 7.
Choice of score function
Upon ﬁrst glance, this seems too good to be true, and a skeptical reader might ask the following question:
How is it possible to construct a statistically valid prediction set even if the heuristic notion of uncertainty
of the underlying model is arbitrarily bad?
Let’s give some intuition to supplement the mathematical understanding from the proof in Appendix D.
Roughly, if the scoressi correctly rank the inputs from lowest to highest magnitude of model error, then the
resulting sets will be smaller for easy inputs and bigger for hard ones. If the scores are bad, in the sense that
they do not approximate this ranking, then the sets will be useless. For example, if the scores are random
noise, then the sets will contain a random sample of the label space, where that random sample is large
enough to provide valid marginal coverage. This illustrates an important underlying fact about conformal
prediction: although the guarantee always holds, the usefulness of the prediction sets is primarily
determined by the score function. This should be no surprise—the score function incorporates almost all
the information we know about our problem and data, including the underlying model itself. For example, the
main diﬀerence between applying conformal prediction on classiﬁcation problems versus regression problems
is the choice of score. There are also many possible score functions for a single underlying model, which have
diﬀerent properties. Therefore, constructing the right score function is an important engineering choice. We
will next show a few examples of good score functions.
2 Examples of Conformal Procedures
In this section we give examples of conformal prediction applied in many settings, with the goal of providing
the reader a bank of techniques to practically deploy. Note that we will focus only on one-dimensional Y in
this section, and smaller conformal scores will correspond to more model conﬁdence (such scores are called
nonconformity scores). Richer settings, such as high-dimensional Y , complicated (or multiple) notions of
error, or where diﬀerent mistakes cost diﬀerent amounts, often require the language of risk control, outlined
in Section A.
2.1 Classiﬁcation with Adaptive Prediction Sets
Let’s begin our sequence of examples with an improvement to the classiﬁcation example in Section 1.
The previous method produces prediction sets with the smallest average size [6], but it tends to undercover
hard subgroups and overcover easy ones. Here we develop a diﬀerent method called adaptive prediction sets
(APS) that avoids this problem. We will follow [7] and [4].
As motivation for this new procedure, note that if the softmax outputs ˆf(Xtest) were a perfect model
of Ytest|Xtest, we would greedily include the top-scoring classes until their total mass just exceeded 1 −α.
6

=== PDF PAGE 7 ===
# Get scores. calib_X.shape[0] == calib_Y.shape[0] == n
cal_pi = cal_smx.argsort(1)[:,::-1]; cal_srt = np.take_along_axis(cal_smx,cal_pi,axis=1).cumsum(axis=1)
cal_scores = np.take_along_axis(cal_srt,cal_pi.argsort(axis=1),axis=1)[range(n),cal_labels]
# Get the score quantile
qhat = np.quantile(cal_scores, np.ceil((n+1)*(1-alpha))/n, interpolation='higher')
# Deploy (output=list of length n, each element is tensor of classes)
val_pi = val_smx.argsort(1)[:,::-1]; val_srt = np.take_along_axis(val_smx,val_pi,axis=1).cumsum(axis=1)
prediction_sets = np.take_along_axis(val_srt &lt;= qhat,val_pi.argsort(axis=1),axis=1)
Figure 3: Python code for adaptive prediction sets.
Formally, we can describe this oracle algorithm as
{π1(x),...,π k(x)} , where k = sup


k′ :
k′∑
j=1
ˆf(Xtest)πj(x) &lt; 1−α</message>
<message type="ai">
  <tool_call id="call_fc73f494c8e845c7bf4148e267a144f5" name="read_file">{"file_path": "/work/literature/1904.06019_consulted.txt", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-300 of 1350 | next offset 300 @@
=== PDF PAGE 6 ===
●
●
●●
●
●
●
●
●●● ●
●
●
●
●
●
●
●
●●●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●
●●
●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●
●
●
● ●
●
●
●
●
●
●
●
●
●
●
●
●
●
●●
●
●●
●
●
●
●
●●
●
●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●●
●
●
●●
●
●
●
●
●
●
●●
● ●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●
●
●
●
●●
●
●
●●●
●
●●
●
●
●
●●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●●●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
● ●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
●●
●
●
●●
●
● ●●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●●
●●
●●
●●
●
●
●
●
●
● ●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●●●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●
●●
●
●
●
●
● ●
●
●
●
●
●
●
●●
●
●●
●
●
●
●
●
●
●
●
●● ●●
●
●●●
●
●
●
●</message>
<message type="ai">
  <content><reasoning>**Filtering page line noise**</reasoning></content>
  <tool_call id="call_28033841a20248dbb3d5b7228a9aefb2" name="read_file">{"file_path": "/work/literature/1904.06019.txt", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-300 of 2190 | next offset 300 @@
=== PDF PAGE 1 ===
Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the training and test data are not drawn from the same distribution.
We begin by reviewing the basics of conformal prediction, in this section. In Section 2, we describe an extension of
conformal prediction to the setting of covariate shift, and give supporting empirical results. In Section 3, we cover the
mathematical details behind our conformal extension. We conclude in Section 4, and discuss several other possible
applications of our new conformal methodology.
1.1 Quantile lemma
Before explaining the basic ideas behind conformal inference (i.e., conformal prediction, we will use these two terms
interchangeably), we introduce some notation. We denote by Quantile(β;F ) the levelβ quantile of a distributionF ,
i.e., forZ∼F ,
Quantile(β;F ) = inf
{
z : P{Z≤z}≥ β
}
.
In our use of quantiles, we will allow for distributionsF on the augmented real line, R∪{∞} . For valuesv1,...,v n,
we writev1:n ={v1,...,v n} to denote their multiset. Note that this is unordered, and allows for multiple instances the
same element; thus in the present case, ifvi =vj fori⁄=j, then this value appears twice inv1:n. To denote quantiles
of the empirical distribution of the valuesv1,...,v n, we abbreviate
Quantile(β;v1:n) = Quantile
(
β; 1n
n∑
i=1
δvi
)
,
1
arXiv:1904.06019v3  [stat.ME]  6 Jul 2020

=== PDF PAGE 2 ===
whereδa denotes a point mass ata (i.e., the distribution that places all mass at the valuea). The next result is a simple
but key component underlying conformal prediction.
Lemma 1. IfV1,...,V n+1 are exchangeable random variables, then for anyβ∈ (0, 1), we have
P
{
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)}
≥β.
Furthermore, if ties betweenV1,...,V n+1 occur with probability zero, then the above probability is upper bound by
β + 1/(n + 1).
Proof. Consider the following useful fact about quantiles of a discrete distributionF , with support pointsa1,...,a k∈
R: denotingq = Quantile(β;F ), if we reassign the pointsai &gt;q to arbitrary values strictly larger thanq, yielding a
new distribution ~F , then the levelβ quantile remains unchanged, Quantile(β;F ) = Quantile(β;~F ). Using this fact,
Vn+1 &gt; Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1 &gt; Quantile
(
β;V1:(n+1)
)
,
or equivalently,
Vn+1≤ Quantile
(
β;V1:n∪{∞}
)
⇐⇒ Vn+1≤ Quantile
(
β;V1:(n+1)
)
. (2)
Moreover, it is straightforward to check that
Vn+1≤ Quantile
(
β;V1:(n+1)
)
⇐⇒ Vn+1 is among the⌈β(n + 1)⌉ smallest ofV1,...,V n+1.
By exchangeability, the latter event occurs with probability at least⌈β(n + 1)⌉/(n + 1)≥β, which proves the lower
bound; when there are almost surely no ties, it holds with probability exactly⌈β(n + 1)⌉/(n + 1)≤β + 1/(n + 1),
which proves the upper bound.
1.2 Conformal prediction
We now return to the regression setting. DenoteZi = (Xi,Yi),i = 1,...,n , andZ1:n ={Z1,...,Z n}. We will use
the abbreviationZ−i =Z1:n\{Zi}. In what follows, we describe the construction of a prediction band satisfying (1),
using conformal inference, due to V ovk et al. (2005). We ﬁrst choose a score functionS, whose arguments consist of a
point (x,y ), and a multisetZ.1 Informally, a low value ofS((x,y ),Z ) indicates that the point (x,y ) “conforms” toZ,
whereas a high value indicates that (x,y ) is atypical relative to the points inZ. For example, we might choose to deﬁne
S by
S
(
(x,y ),Z
)
=|y−ˆµ(x)|, (3)
whereˆµ : Rd→ R is a regression function that was ﬁtted by running an algorithmA on (x,y ) andZ.
Next, at eachx∈ Rd, we deﬁne the conformal prediction interval2 ˆCn(x) by repeating the following procedure for
eachy∈ R. We calculate the nonconformity scores
V (x,y)i =S(Zi,Z−i∪{ (x,y )}), i= 1,...,n, and V (x,y)n+1 =S((x,y ),Z 1:n), (4)
and includey in our prediction interval ˆCn(x) if
V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞}),
whereV (x,y)1:n ={V (x,y)1 ,...,V (x,y)n }. Importantly, the symmetry in the construction of the nonconformity scores (4)
guarantees exact coverage in ﬁnite samples. The next theorem summarizes this coverage result. The lower bound is a
standard result in conformal inference, due to V ovk et al. (2005); the upper bound, as far as we know, was ﬁrst pointed
out by Lei et al. (2018).
1We emphasize that by deﬁningZ to be a multiset, we are treating its points as unordered. Hence, to be perfectly explicit, the score function S
cannot accept the points inZ in any particular order, and it must take them in as unordered. The same is true of the base algorithm A used to deﬁne
the ﬁtted regression function ˆµ, in the choice of absolute residual score function (3).
2For convenience, throughout, we will refer to ˆCn(x) as an “interval”, even though this may actually be a union of multiple nonoverlapping
intervals. Similarly, for simplicity, we will refer to ˆCn as a “band”.
2

=== PDF PAGE 3 ===
Theorem 1 (V ovk et al. 2005; Lei et al. 2018). Assume that (Xi,Yi)∈ Rd× R,i = 1,...,n + 1 are exchangeable.
For any score functionS, and anyα∈ (0, 1), deﬁne the conformal band (based on the ﬁrstn samples) atx∈ Rd by
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞})}, (5)
whereV (x,y)i ,i = 1,...,n + 1 are as deﬁned in (4). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Furthermore, if ties betweenV (Xn+1,Yn+1)1 ,...,V (Xn+1,Yn+1)n+1 occur with probability zero, then this probability is upper
bounded by 1−α + 1/(n + 1).
Proof. To lighten notation, abbreviateVi =V (Xn+1,Yn+1)i ,i = 1,...,n + 1. Observe
Yn+1∈ ˆCn(Xn+1) ⇐⇒ Vn+1≤ Quantile(1−α;V1:n∪{∞}).
By the symmetric construction of the nonconformity scores in (4),
(Z1,...,Z n+1)
d
= (Zσ(1),...,Z σ(n+1)) ⇐⇒ (V1,...,V n+1)
d
= (Vσ(1),...,V σ(n+1)),
for any permutationσ of the numbers 1,...,n + 1. Therefore, asZ1,...,Z n+1 are exchangeable, so areV1,...,V n+1,
and applying Lemma 1 gives the result.
Remark 1. Theorem 1 is stated for exchangeable samples (Xi,Yi),i = 1,...,n + 1, which is (signiﬁcantly) weaker
than assuming i.i.d. samples. As we will see in what follows, it is furthermore possible to relax the exchangeability
assumption, under an appropriate modiﬁcation to the conformal procedure.
Remark 2. If we use an appropriate random tie-breaking rule (to determine the rank ofVn+1 amongV1,...,V n+1),
then the upper bounds in Lemma 1 and Theorem 1 hold in general (without assuming there are no ties almost surely).
The result in Theorem 1, albeit very simple to prove, is quite remarkable. It gives us a recipe for distribution-free
prediction intervals, with nearly exact coverage, starting from an arbitrary score functionS; e.g., absolute residuals
with respect to a ﬁtted regression function from any base algorithmA, as in (3). For more discussion of conformal
prediction, its properties, and its variants, we refer to V ovk et al. (2005); Lei et al. (2018) and references therein.
2 Covariate shift
In this paper, we are concerned with settings in which the data (Xi,Yi),i = 1,...,n + 1 are no longer exchangeable.
Our primary focus will be a setting in which we observe data according to
(Xi,Yi)
i.i.d.
∼ P =PX×PY|X, i= 1,...,n,
(Xn+1,Yn+1)∼ ~P = ~PX×PY|X, independently. (6)
Notice that the conditional distribution ofY|X is assumed to be the same for both the training and test data. Such a
setting is often called covariate shift (e.g., see Shimodaira 2000; Quinonero-Candela et al. 2009; see also Remark 4
below for more discussion of this literature). The key realization is the following: if we know the ratio of test to training
covariate likelihoods, d~PX/dPX, then we can still perform a modiﬁed of version conformal inference, using a quantile
of a suitably weighted empirical distribution of nonconformity scores. The next subsection gives the details; following
this, we describe a more computationally efﬁcient conformal procedure, and give an empirical demonstration.
2.1 Weighted conformal prediction
In conformal prediction, we compare the value of a nonconformity score at a test point to the empirical distribution of
nonconformity scores at the training points. In the covariate shift case, where the covariate distributions PX,~PX in
our training and test sets differ, we will now weight each nonconformity scoreV (x,y)i (which measures how wellZi =
3

=== PDF PAGE 4 ===
(Xi,Yi) conforms to the other points) by a probability proportional to the likelihood ratiow(Xi) = d~PX (Xi)/dPX (Xi).
Therefore, we will no longer be interested in the empirical distribution
1
n + 1
n∑
i=1
δV (x,y)i + 1n + 1δ∞,
as in Theorem 1, but rather, a weighted version
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞,
where the weights are deﬁned by
pwi (x) = w(Xi)∑n
j=1w(Xj) +w(x), i= 1,...,n, and pwn+1(x) = w(x)∑nj=1w(Xj) +w(x). (7)
Due this careful weighting, draws from the discrete distribution in the second to last display resemble nonconformity
scores computed on the test population, and thus, they “look exchangeable” with the nonconformity score at our test
point. Our main result below formalizes these claims.
Corollary 1. Assume data from the model(6). Assume that ~PX is absolutely continuous with respect toPX, and denote
w = d~PX/dPX. For any score functionS, and anyα∈ (0, 1), deﬁne forx∈ Rd,
ˆCn(x) =
{
y∈ R :V (x,y)n+1 ≤ Quantile
(
1−α;
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞
)}
, (8)
whereV (x,y)i ,i = 1,...,n + 1 are as in (4), andpwi (x),i = 1,...,n + 1 are as in (7). Then ˆCn satisﬁes
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α.
Corollary 1 is a special case of a more general result that we present later in Theorem 2, which extends conformal
inference to a setting in which the data are what we call weighted exchangeable. The proof is given in Section 3.5.
Remark 3. The same result as in Corollary 1 holds ifw∝ d~PX/dPX, i.e., with an unknown normalization constant,
because this normalization constant cancels out in the calculation of probabilities in (7).
Remark 4. Though the basic premise of covariate shift—and certainly the techniques employed in addressing it—are
related to much older ideas in statistics, the speciﬁc setup (6) has recently generated great interest in machine learning:
e.g., see Sugiyama and Muller (2005); Sugiyama et al. (2007); Quinonero-Candela et al. (2009); Agarwal et al. (2011);
Wen et al. (2014); Reddi et al. (2015); Chen et al. (2016) and references therein). The focus is usually on correcting
estimators, model evaluation, or model selection approaches to account for covariate shift. Correcting distribution-free
prediction intervals, as we examine in this work, is (as far as we know) a new contribution. As one might expect, the
likelihood ratio d~PX/dPX, a key component of our conformal construction in Corollary 1, also plays a critical role in
much of the literature on covariate shift.
2.2 Weighted split conformal
In general, constructing a conformal prediction band can be computationally intensive, though this of course depends
on the choice of score function. Consider the use of absolute residuals as in (3). To compute the nonconformity scores
in (4), we must ﬁrst run our base algorithmA on the data setZ1:n∪{ (x,y )} to produce a ﬁtted regression functionˆµ,
and then calculate
V (x,y)i =|Yi−ˆµ(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−ˆµ(x)|.
As the formation of the conformal set in (5) (ordinary case) or (8) (covariate shift case) requires us to do this for each
x∈ Rd andy∈ R (which requires reﬁttingˆµ each time), this can clearly become computationally burdernsome.
A fast alternative, known as split conformal prediction (Papadopoulos et al., 2002; Lei et al., 2015), resolves this
issue by taking the score functionS to be deﬁned using absolute residuals with respect to a ﬁxed regression function,
4

=== PDF PAGE 5 ===
typically, one that has been trained on an preliminary data set. Denote by (X 01,Y 01 ),..., (X 0n0,Y 0n0 ) this preliminary
data set, used for ﬁtting the regression functionµ0, and consider the score function
S
(
(x,y ),Z
)
=|y−µ0(x)|.
Given data (X1,Y 1),..., (Xn,Yn), independent of (X 01,Y 01 ),..., (X 0n0,Y 0n0 ), we calculate
V (x,y)i =|Yi−µ0(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−µ0(x)|.
The conformal prediction interval (5), deﬁned at a pointx∈ Rd, reduces to
ˆCn(x) = µ0(x)± Quantile
(
1−α;
{
|Yi−µ0(Xi)|
}n
i=1∪{∞}
)
, (9)
and by Theorem 1 it has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ). This coverage result holds
because, when we treatµ0 as ﬁxed (meaning, condition on (X 01,Y 01 ),..., (X 0n0,Y 0n0 )), the scoresV (x,y)1 ,...,V (x,y)n+1
scores are exchangeable for (x,y ) = (Xn+1,Yn+1), as (X1,Y 1),..., (Xn+1,Yn+1) are.
As split conformal prediction can be seen as a special case of conformal prediction, in which the regression function
µ0 is treated as ﬁxed, Corollary 1 also applies to the split scenario, and guarantees that the band deﬁned forx∈ Rd by
ˆCn(x) = µ0(x)± Quantile
(
1−α;
n∑
i=1
pwi (x)δ|Yi−µ0(Xi)| +pwn+1(x)δ∞
)
, (10)
where the probabilities are as in (7), has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ).
2.3 Airfoil data example
We demonstrate the use of conformal prediction in the covariate shift setting in an empirical example. We consider the
airfoil data set from the UCI Machine Learning Repository (Dua and Graff, 2019), which hasN = 1503 observations of
a responseY (scaled sound pressure level of NASA airfoils), and a covariateX withd = 5 dimensions (log frequency,
angle of attack, chord length, free-stream velocity, and suction side log displacement thickness). For efﬁciency, we use
the split conformal prediction methods in (9) and (10) for the unweighted and weighted case, respectively. R code to
reproduce these simulation results can be found at http://www.github.com/ryantibs/conformal/.
Creating training data, test data, and covariate shift. We repeated an experiment for 5000 trials, where for each
trial we randomly partitioned the data{(Xi,Yi)}Ni=1 into three setsDpre,D train,D test, and also constructed a covariate
shift test setDshift, which have the following roles.
• Dpre, containing 25% of the data, is used to preﬁt a regression functionµ0 via linear regression, to be used in
constructing split conformal intervals.
• Dtrain, containing 25% of the data, is our training set, i.e., (Xi,Yi),i = 1,...,n , used to compute the residual
quantiles in the construction of the split conformal prediction intervals (9) and (10).
• Dtest, containing 50% of the data, is our test set (as these data points are exchangeable with those inDtrain, there
is no covariate shift in this test set).
• Dshift is a second test set, constructed to simulate covariate shift, by sampling 25% of the points fromDtest with
replacement, with probabilities proportional to
w(x) = exp(xTβ), where β = (−1, 0, 0, 0, 1). (11)
As the original data pointsDtrain∪Dtest can be seen as draws from the same underlying distribution, we can view
w(x) as the likelihood ratio of covariate distributions between the test setDshift and training setDtrain. Note that the test
covariate distribution~PX, which satisﬁes d~PX∝ exp(xTβ)dPX as we have deﬁned it here, is called an exponential
tilting of the training covariate distributionPX. Figure 1 visualizes the effect of this exponential tilting, in the airfoil
data set, with our choiceβ = (−1, 0, 0, 0, 1). Only the 1st and 5th dimensions of the covariate distribution are tilted;</message>
<message type="ai">
  <content><reasoning>**Using final text offset**</reasoning></content>
  <tool_call id="call_820393a326d5476395b96f61bccfb9d1" name="execute">{"command": "python -c 'from pypdf import PdfReader; from pathlib import Path; specs={\"1904.06019\":[7],\"2009.14193\":[6,7,8,9,10,14,15,16,17],\"2402.10723\":[7,8,9,13]}; [(Path(\"/work/literature/\"+i+\"_targeted.txt\").write_text(\"\\n\\n\".join(\"=== PDF PAGE \"+str(p)+\" ===\\n\"+\"\\n\".join(l for l in r.pages[p-1].extract_text().splitlines() if any(c.isalpha() for c in l) or len(l)&gt;25) for p in pages))) for i,pages in specs.items() for r in [PdfReader(\"/work/literature/\"+i+\".pdf\")]]'", "timeout": 120}</tool_call>
</message>
<message type="tool">&lt;no output&gt;
[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_2f36ee018a6348d1881eb8c87cc42749" name="read_file">{"file_path": "/work/literature/1904.06019_targeted.txt", "limit": 180, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-15 of 15 @@
=== PDF PAGE 7 ===
Coverage
Frequency
0 100 300 500 700 No covariate shift
Covariate shift
Coverage
Frequency
0 100 300 500 700 Oracle weights
No shift, fewer samples
Coverage
Frequency
0 100 300 500 700 Logistic regression weights
Random forest weights
Figure 2: Empirical coverages of conformal prediction intervals, computed using 5000 different random splits of the airfoil data set.
The averages of empirical coverages in each histogram are marked on the x-axis.</message>
<message type="ai">
  <content><reasoning>**Filtering page 6**</reasoning></content>
  <tool_call id="call_94f377cd9e0649d495849155f4e0ed9d" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/1904.06019.pdf\"); print(\"\\n\".join(l for l in r.pages[5].extract_text().splitlines() if any(c.isalpha() for c in l) or len(l)&gt;25)); print(\"PDF PAGE 8\\n\",r.pages[7].extract_text())'", "timeout": 30}</tool_call>
</message>
<message type="tool">x1
y
x1
Frequency
x5
y
0.0 0.1 0.2 0.3 0.4 0.5 0.6
x5
Frequency
Figure 1: The top row plots the response in (a randomly chosen half of) the airfoil data set, versus the 1st and 5th covariates. The
bottom row plots kernel density estimates for the 1st and 5th covariates, in black. Also displayed are kernel density estimates for the
1st and 5th covariates after exponential tilting (11), in blue.
Loss of coverage of ordinary conformal prediction under covariate shift. First, we examine the performance of
ordinary split conformal prediction (9). The nominal coverage level was set to be 90% (meaningα = 0.1), here and
throughout. The results are shown in the top row of Figure 2. In each of the 5000 trials, we computed the empirical
coverage from the split conformal intervals over points in the test sets, and the histograms show the distribution of these
empirical coverages over the trials. We see that for the original test dataDtest (no covariate shift, shown in red), split
conformal works as expected, with the average of the empirical coverages (over the 5000 trials) being 90.2%; but for
the nonuniformly subsampled test dataDshift (covariate shift, in blue), split conformal considerably undercovers, with
its average coverage being 82.2%.
Coverage of weighted conformal prediction with oracle weights. Next, displayed in the middle row of Figure 2,
we consider weighted split conformal prediction (10), to cover the points inDshift (shown in orange). At the moment,
we assume oracle knowledge of the true weight functionw in (11) needed to calculate the probabilities in (7). We see
that this brings the coverage back to the desired level, with the average coverage being 90.8%. However, the histogram
is more dispersed than it is when there is no covariate shift (compare to the top row, in red). This is because, by using a
quantile of the weighted empirical distribution of nonconformity scores, we are relying on a reduced “effective sample
size”. Given training pointsX1,...,X n, and a likelihood ratiow of test to training covariate distributions, a popular
heuristic formula from the covariate shift literature for the effective sample size ofX1,...,X n is (Gretton et al., 2009;
Reddi et al., 2015):
ˆn = [∑ni=1|w(Xi)|]2∑n
i=1|w(Xi)|2 =‖w(X1:n)‖21‖w(X1:n)‖22,
PDF PAGE 8
 where we abbreviatew(X1:n) = (w(X1),...,w (Xn))∈ Rn. To compare weighted conformal prediction against the
unweighted method at the same effective sample size, in each trial, we ran unweighted split conformal on the original
test setDtest, but we used onlyˆn subsampled points fromDtrain to compute the quantile of nonconformity scores, when
constructing the prediction interval (9). The results (the middle row of Figure 2, in purple) line up very closely with
those from weighted conformal, which demonstrates that apparent overdispersion in the coverage histogram from the
latter is fully explained by the reduced effective sample size.
Coverage of weighted conformal with estimated weights. Denote byX1,...,X n the covariate points inDtrain and
byXn+1,...,X n+m the covariate points inDshift. Here we describe how to estimatew = d~PX/dPX, the likelihood
ratio of interest, by applying logistic regression or random forests (more generally, any classiﬁer that outputs estimated
probabilities of class membership) to the feature-class pairs (Xi,Ci),i = 1,...,n +m, whereCi = 0 fori = 1,...,n
andCi = 1 fori =n + 1,...,n +m. Noting that
P(C = 1|X =x)
P(C = 0|X =x) = P(C = 1)P(C = 0) d~PXdPX (x),
we can take the conditional odds ratiow(x) = P(C = 1|X =x)/P(C = 0|X =x) as an equivalent representation
for the oracle weight function (since we only need to know the likelihood ratio up to a proportionality constant, recall
Remark 3). Therefore, ifˆp(x) is an estimate of P(C = 1|X =x) obtained by ﬁtting a classiﬁer to the data (Xi,Ci),
i = 1,...,n +m, then we can use
ˆw(x) = ˆp(x)1−ˆp(x) (12)
as our estimated weight function for the calculation of probabilities (7), needed for conformal (8) or split conformal
(10). There is in fact a sizeable literature on density ratio estimation, and the method just describe falls into a class
called probabilistic classiﬁcation approaches; two other classes are based on moment matching, and minimization of
φ-divergences (e.g., Kullblack-Leibler divergence). For a comprehensive review of these approaches, and supporting
theory, see Sugiyama et al. (2012).
The bottom row of Figure 2 shows the results from using weighted split conformal prediction to cover the points
inDshift, where the weight function ˆw has been estimated as in (12), using logistic regression (in gray) and random
forests3 (in green) to ﬁt the class probability functionˆp. Note that logistic regression is well-speciﬁed in this example,
because it assumes the log odds is a linear function ofx, which is exactly as in (11). Random forests, of course, allows
more ﬂexibility in the ﬁtted model. Both classiﬁcation approaches deliver weights that translate into good average
coverage, being 91.0% for each approach. Furthermore, their histograms are only a little more dispersed than that for
the oracle weights (middle row, in orange).
Lengths of weighted conformal intervals. Figure 3 conveys the same setup as Figure 2, but displays histograms of
the median lengths of prediction intervals rather than empirical coverages (meaning, in each of the 5000 trials, we ran
unweighted or weighted split conformal prediction to cover test points, and report the median length of the prediction
intervals over the test sets). We see no differences in the lengths of ordinary split conformal intervals (top row) when
there is or is not covariate shift, as expected since these two settings differ only in the distributions of their test sets,
but use the same procedure and have the same distribution of the training data. We see that the oracle-weighted split
conformal intervals are longer than the ordinary split conformal intervals that use an equivalent effective sample size
(middle row). This is also as expected, since in the former situation, the regression functionµ0 was ﬁt on training data
Dtrain of a different distribution thanDshift, andµ0 itself should ideally be adjusted to account for covariate shift (plenty
of methods for this are available from the covariate shift literature, but we left it unadjusted for simplicity). Lastly, we
see that the random forests-weighted split conformal intervals are more variable, and in some cases, much longer, than
the logistic regression-weighted split conformal intervals (bottom row, difﬁcult to conﬁrm visually because the bars in
the histogram lie so close to the x-axis).
3In the random forests approach, we clipped the estimated test class probability ˆp(x) to lie in between 0.01 and 0.99, to prevent the estimated
weight (likelihood ratio) ˆw(x) from being inﬁnite. Without clipping, the estimated probability of being in the test class was sometimes exactly 1 (this
occurred in about 2% of the cases encountered over all 5000 repetitions), resulting in an inﬁnite weight, and causing numerical issues.
8

[Command succeeded with exit code 0]</message>
<message type="ai">
  <tool_call id="call_a78905b44d4c4310aef1fa08a0fe6643" name="read_file">{"file_path": "/work/literature/2009.14193_targeted.txt", "limit": 430, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-397 of 397 @@
=== PDF PAGE 6 ===
Algorithm 2 RAPS Conformal Calibration
Input: α;s∈ [0, 1]n×K,I∈{ 1,...,K}n×K, andy∈{ 0, 1,...,K}n corresponding respectively to
the sorted scores, the associated permutation of indexes, and ground-truth labels for each of n
examples in the calibration set;kreg;λ; booleanrand
1: procedure RAPSC (α,s,I,y,λ)
2: fori∈{ 1,··· ,n} do
3: Li←j such thatIi,j =yi
4: Ei← ΣLij=1si,j +λ(Li−kreg)+
5: ifrand then
6: U∼ Unif(0, 1)
7: Ei←Ei−U∗si,Li
8: ˆτccal← the⌈(1−α)(1 +n)⌉ largest value in{Ei}ni=1
9: return ˆτccal
Output: The generalized quantile, ˆτccal ⊿ The value in Eq. (3)
Algorithm 3 RAPS Prediction Sets
Input: α, sorted scoress and the associated permutation of classesI for a test-time example, ˆτccal
from Algorithm 2,kreg,λ, booleanrand
1: procedure RAPS (α,s,I, ˆτccal,kreg,λ,rand )
2: L←|{ j∈Y : Σ ji=1si +λ(j−kreg)+≤ ˆτccal}| + 1
3: ifrand then
4: U← Unif(0, 1)
5: L←L− I
(ΣLi=1si +λ(L−kreg)+− ˆτccal)/(sL +λI(L&gt;k reg))≤U}
6: returnC =
I1,...IL
⊿ TheL most likely classes
Output: The 1−α conﬁdence set,C ⊿ The set in Eq. (4)
it is included in the predictive set. For example, if kreg = 5, then the sixth most likely value of y
has an extra penalty of size λ, so it will never be included until τ exceedsρx(y) + ˆπx(y)·u +λ,
whereas it enters whenτ exceedsρx(y) + ˆπx(y)·u in the nonregularized version. Our method has
the following coverage property:
Proposition 1 (RAPS coverage guarantee). Suppose (Xi,Yi,Ui)i=1,...,n and (Xn+1,Yn+1,Un+1)
are i.i.d. and letC∗(x,u,τ ) be deﬁned as in Eq. (4). Suppose further that ˆπx(y) &gt; 0 for allx and
y. Then for ˆτccal deﬁned as in Eq. (3), we have the following coverage guarantee:
1−α≤P
Yn+1∈C∗(Xn+1,Un+1, ˆτccal))≤ 1−α + 1n + 1.
Note that the ﬁrst inequality is a corollary of Theorem 1, and the second inequality is a special case
of the remark in Section 2.1. The restriction that ˆπx(y)&gt; 0 is not necessary for the ﬁrst inequality.
2.3 W HY REGULARIZE ?
In our experiments, the sets from APS are larger than necessary, because APS is sensitive to the
noisy probability estimates far down the list of classes. This noise leads to apermutation problem of
unlikely classes, where ordering of the classes with small probability estimates is determined mostly
by random chance. If 5% of the true classes from the calibration set are deep in the tail due to the
permutation problem, APS will choose large 95% predictive sets; see Figure 2. The inclusion of the
RAPS regularization causes the algorithm to avoid using the unreliable probabilities in the tail; see
Figure 4. We discuss how RAPS improves the adaptiveness of APS in Section 4 and Appendix E.
2.4 O PTIMALITY CONSIDERATIONS
To complement these experimental results, we now formally prove that RAPS with the correct reg-
ularization parameters will always dominate the simple procedure that returns a ﬁxed set size. (Sec-
tion 3.5 shows the parameters are easy to select and RAPS is not sensitive to their values). For a
feature vector x, let ˆy(j)(x) be the label with the jth highest predicted probability. We deﬁne the
top-k predictive sets to be{ˆy(1)(x),..., ˆy(k)(x)}.
Proposition 2 (RAPS dominates top-k sets). Suppose (Xi,Yi,Ui)i=1,...,n and (Xn+1,Yn+1,Un+1)
are i.i.d. draws. Let k∗ be the smallest k such that the top-k predictive sets have coverage at least

=== PDF PAGE 7 ===
Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.793 0.945 0.900 0.889 0.900 0.900 2.42 17.1 19.7 2.00
ResNet152 0.783 0.94 0.900 0.895 0.900 0.900 2.63 9.78 10.4 2.11
ResNet101 0.774 0.936 0.900 0.896 0.900 0.900 2.83 10.3 10.7 2.25
ResNet50 0.761 0.929 0.900 0.896 0.900 0.900 3.14 11.8 12.3 2.57
ResNet18 0.698 0.891 0.900 0.895 0.900 0.900 5.72 15.5 16.2 4.43
DenseNet161 0.771 0.936 0.900 0.894 0.900 0.900 2.84 11.2 12.1 2.29
VGG16 0.716 0.904 0.900 0.895 0.901 0.900 4.75 13.4 14.1 3.54
Inception 0.695 0.887 0.900 0.885 0.900 0.901 6.30 75.4 89.1 5.32
ShufﬂeNet 0.694 0.883 0.900 0.891 0.900 0.900 6.46 28.9 31.9 5.05
Table 1: Results on Imagenet-Val. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials. See Section 3.1 for full details.
⌈(n + 1)(1−α)⌉/n on the conformal calibration points (Xi,Yi)i=1,...,n. TakeC∗(x,u,τ ) as in Eq.
(4) with anykreg≤k∗ andλ = 1. Then with ˆτccal chosen as in Eq. (3), we have
C∗(Xn+1,Un+1, ˆτccal) ⊆ {ˆy(1)(x),..., ˆy(k∗)(x)}.
In words, the RAPS procedure with heavy regularization will be at least as good as the top-k proce-
dure in the sense that it has smaller or same average set size while maintaining the desired coverage
level. This is not true of either the naive baseline or the APS procedure; Table 2 shows that these
two procedures usually return predictive sets with size much larger thank∗.
3 E XPERIMENTS
In this section we report on experiments that study the performance of the predictive sets from
naive, APS, and RAPS, evaluating each based on the three desiderata above. We begin with a brief
preview of the experiments. In Experiment 1, we evaluate naive, APS, and RAPS on Imagenet-
Val. Both APS and RAPS provided almost exact coverage, while naive sets had coverage slightly
below the speciﬁed level. APS has larger sets on average than naive and RAPS. RAPS has a
much smaller average set size than APS and naive. In Experiment 2, we repeat Experiment 1 on
Imagenet-V2, and the conclusions still hold. In Experiment 3, we produce histograms of set sizes
for naive, APS, and RAPS for several different values ofλ, illustrating a simple tradeoff between
set size and adaptiveness. In Experiment 4, we compute histograms of RAPS sets stratiﬁed by
image difﬁculty, showing that RAPS sets are smaller for easier images than for difﬁcult ones. In
Experiment 5, we report the performance of RAPS with many values of the tuning parameters.
In our experiments, we use nine standard, pretrained Imagenet classiﬁers from the torchvision
repository (Paszke et al., 2019) with standard normalization, resize, and crop parameters. Before
applying naive, APS, or RAPS, we calibrated the classiﬁers using the standard temperature scal-
ing/Platt scaling procedure as in Guo et al. (2017) on the calibration set. Thereafter, naive, APS,
and RAPS were applied, with RAPS using a data-driven choice of parameters described in Ap-
pendix E. We use the randomized versions of these algorithms—see Appendix B for a discussion.
3.1 E XPERIMENT 1: COVERAGE VS SET SIZE ON IMAGENET
In this experiment, we calculated the coverage and mean set size of each procedure for two different
choices of α. Over 100 trials, we randomly sampled two subsets of Imagenet-Val: one conformal
calibration subset of size 20K and one evaluation subset of size 20K. The median-of-means over
trials for both coverage and set size are reported in Table 1. Figure 2 illustrates the performances of
naive, APS, and RAPS; RAPS has much smaller sets than both naive and APS, while achieving
coverage. We also report results from a conformalized ﬁxed-k procedure, which ﬁnds the smallest
ﬁxed set size achieving coverage on the holdout set, k∗, then predicts sets of size k∗− 1 ork∗ on
new examples in order to achieve exact coverage; see Algorithm 4 in Appendix E.

=== PDF PAGE 8 ===
Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.678 0.874 0.900 0.888 0.899 0.899 7.48 43.0 50.8 6.18
ResNet152 0.67 0.876 0.899 0.896 0.900 0.900 7.18 25.8 27.2 5.69
ResNet101 0.657 0.859 0.901 0.894 0.900 0.898 9.21 28.7 30.7 6.93
ResNet50 0.634 0.847 0.898 0.894 0.899 0.900 10.3 30.3 32.3 7.80
ResNet18 0.572 0.802 0.902 0.895 0.900 0.900 17.5 35.3 37.4 13.3
DenseNet161 0.653 0.862 0.902 0.895 0.901 0.901 8.6 29.9 32.4 6.93
VGG16 0.588 0.817 0.902 0.897 0.900 0.899 15.1 31.9 32.8 11.2
Inception 0.573 0.797 0.900 0.893 0.900 0.899 21.8 145.0 155.0 20.5
ShufﬂeNet 0.559 0.781 0.899 0.892 0.900 0.899 26.0 66.2 71.7 22.5
Table 2: Results on Imagenet-V2. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials at the 10% level. See Section 3.2 for full details.
size
frequency
size
size
 method
Naive
APS
RAPS
Figure 4: Set sizes produced with ResNet-152. See Section 3.3 for details.
3.2 E XPERIMENT 2: COVERAGE VS SET SIZE ON IMAGENET -V2
The same procedure as Experiment 1 was repeated on Imagenet-V2, with exactly the same normal-
ization, resize, and crop parameters. The size of the calibration and evaluation sets was 5K, since
Imagenet-V2 is a smaller dataset. The result shows that our method can still provide coverage even
for models trained on different distributions, as long as the conformal calibration set comes from the
new distribution. The variance of the coverage is higher due to having less data.
3.3 E XPERIMENT 3: S ET SIZES OF N A I V E, APS, AND RAPS ON IMAGENET
We investigate the effect of regularization in more detail. For three values ofλ, we collected the set
sizes produced by each of naive, APS, and RAPS and report their histograms in Figure 4.
3.4 E XPERIMENT 4: A DAPTIVENESS OF RAPS ON IMAGENET
We now show thatRAPS sets are smaller for easy images than hard ones, addressing the adaptiveness
desideratum.
Table 4 reports the size-stratiﬁed coverages of RAPS at the 90% level with kreg = 5 and different
choices ofλ. Whenλ is small, RAPS allows sets to be large. But whenλ = 1, RAPS clips sets to be
a maximum of size 5. Table 8 (in the Appendix) stratiﬁes by image difﬁculty, showing that RAPS
sets are small for easy examples and large for hard ones. Experiments 3 and 4 together illustrate
the tradeoff between adaptiveness and size: as the average set size decreases, the RAPS procedure
truncates sets larger than the smallest ﬁxed set that provides coverage, taming the heavy tail of the
APS procedure. Since RAPS with largeλ undercovers hard examples, it must compensate by taking
larger sets for easy examples to ensure the 1−α marginal coverage guarantee. However, the size
only increases slightly since easy images are more common than hard ones, and the total probability
mass can often exceed ˆτccal by including only one more class. If this behavior is not desired, we can
instead automatically pickλ to optimize the adaptiveness of RAPS; see Section 4.
3.5 E XPERIMENT 5: CHOICE OF TUNING PARAMETERS
While any value of the tuning parametersλ andkreg lead to coverage (Proposition 1), some values
will lead to smaller sets. In Experiments 1 and 2, we chose kreg andλ adaptively from data (see
Appendix E), achieving strong results for all models and choices of the coverage level. Table 3 gives
the performance of RAPS with many choices ofkreg andλ for ResNet-152.

=== PDF PAGE 9 ===
kreg|λ 0 1e-4 1e-3 0.01 0.02 0.05 0.2 0.5 0.7 1.0
1 11.2 10.2 7.0 3.6 2.9 2.3 2.1 2.3 2.2 2.2
2 11.2 10.2 7.1 3.7 3.0 2.4 2.1 2.3 2.2 2.2
5 11.2 10.2 7.2 3.9 3.4 2.9 2.6 2.5 2.5 2.5
10 11.2 10.2 7.4 4.5 4.0 3.6 3.4 3.4 3.4 3.4
50 11.2 10.6 8.7 7.2 7.0 6.9 6.9 6.9 6.9 6.9
Table 3: Set sizes of RAPS with parameterskreg andλ, a ResNet-152, and coverage level 90%.
λ = 0 λ = 0.001 λ = 0.01 λ = 0.1 λ = 1
size cnt cvg cnt cvg cnt cvg cnt cvg cnt cvg
0 to 1 11627 0.88 11539 0.88 11225 0.89 10476 0.92 10027 0.93
2 to 3 3687 0.91 3702 0.91 3741 0.92 3845 0.93 3922 0.94
4 to 6 1239 0.91 1290 0.91 1706 0.92 4221 0.89 6051 0.83
7 to 10 688 0.93 765 0.93 1314 0.91 1436 0.71 0
11 to 100 2207 0.94 2604 0.93 2014 0.86 22 0.59 0
101 to 1000 552 0.97 100 0.90 0 0 0
Table 4: Coverage conditional on set size. We report average coverage of images stratiﬁed by the size of the
set output by RAPS using a ResNet-152 for varyingλ. The marginal coverage rate is 90%.
4 A DAPTIVENESS AND CONDITIONAL COVERAGE
In this section, we point to a deﬁnition of adaptiveness that is more natural for the image classiﬁ-
cation setting than the existing notion of conditional coverage. We show that APS does not satisfy
conditional coverage, and that RAPS with smallλ outperforms it in terms of adaptiveness.
4.1 A METRIC OF CONDITIONAL COVERAGE
We say that a set-valued predictor C : Rd → 2Y satisﬁes exact conditional coverage if P (Y ∈
C(X)| X = x) = 1−α for eachx. Distribution-free guarantees on conditional coverage are im-
possible (V ovk, 2012; Lei &amp; Wasserman, 2014), but many algorithms try to satisfy it approximately
(Romano et al., 2019; 2020; Cauchois et al., 2020). In a similar spirit, Tibshirani et al. (2019) sug-
gest a notion of local conditional coverage, where one asks for coverage in a neighborhood of each
point, weighted according to a chosen kernel. Cauchois et al. (2020) introduce the worst-case slab
metric for measuring violations of the conditional coverage property. We present a different way of
measuring violations of conditional coverage based on the following result:
Proposition 3. SupposeP (Y ∈C (X)|X =x) = 1−α for eachx∈ Rd. Then,
P (Y ∈C (X)|{|C(X)|∈A} ) = 1−α for anyA⊂{ 0, 1, 2,... }.
In words, if conditional coverage holds, then coverage holds after stratifying by set size.
In Table 4, we report on the coverage of APS and RAPS, stratiﬁed by the size of the prediction set.
Turning our attention to theλ = 0 column, we see that when APS outputs a set of size 101− 1000,
APS has coverage 97%, substantially higher than 90% nominal rate. By Proposition 3, we conclude
that APS is not achieving exact conditional coverage, because the scores are far from the oracle
probabilities. The APS procedure still achieves marginal coverage by overcovering hard examples
and undercovering easy ones, an undesirable behavior. Alternatively,RAPS can be used to regularize
the set sizes—for λ = .001 to λ = .01 the coverage stratiﬁed by set size is more balanced. In
summary, even purely based on the adaptiveness desideratum, RAPS with light regularization is
preferable to APS. Note that as the size of the training data increases, as long as ˆπ is consistent,
naive and APS will become more stable, and so we expect less regularization will be needed.
We now describe a particular manifestation of our adaptiveness criterion that we will use to optimize
λ. Consider disjoint set-size strata{Si}i=si=1, where⋃j=sj=1Si ={1,..., |Y|}. Then deﬁne the indexes
of examples stratiﬁed by the prediction set size of each example from algorithm C asJj =
i :
|C(Xi,Yi,Ui)|∈ Sj
. Then we can deﬁne the size-stratiﬁed coverage violation of an algorithmC
on strata{S}i=si=1 as
SSCV
C,{S}j=sj=1) = supj
⏐⏐⏐⏐⏐|{i : Yi∈C (Xi, Yi, Ui), i∈J j}||Jj| − (1−α)⏐⏐⏐⏐⏐. (5)

=== PDF PAGE 10 ===
Violation atα = 10% Violation atα = 5%
Model APS RAPS APS RAPS
ResNeXt101 0.088 0.048 0.046 0.020
ResNet152 0.070 0.041 0.039 0.020
ResNet101 0.072 0.059 0.039 0.015
ResNet50 0.070 0.030 0.038 0.017
ResNet18 0.047 0.034 0.032 0.023
DenseNet161 0.076 0.040 0.039 0.017
VGG16 0.051 0.024 0.030 0.015
Inception 0.084 0.042 0.043 0.025
ShufﬂeNet 0.059 0.034 0.035 0.020
Table 5: Adaptiveness results after automatically tuning λ. We report the median size-stratiﬁed coverage
violations of APS and RAPS over 10 trials. See Section 4.2 for experimental details.
In words, Eq. (5) is the worst-case deviation of C from exact coverage when it outputs sets of a
certain size. Computing the size-stratiﬁed coverage violation thus only requires post-stratifying the
results ofC on a set of labeled examples. If conditional coverage held, the worst stratum coverage
violation would be 0 by Proposition 3.
4.2 O PTIMIZING ADAPTIVENESS WITH RAPS
Next, we show empirically that RAPS with an automatically chosen set of kreg and λ improves
the adaptiveness of APS, as measred by the SSCV criterion. After picking kreg as in described
Appendix E, we can chooseλ using the same tuning data to optimize this notion of adaptiveness.
To maximize adaptiveness, we’d like to chooseλ to minimize the size-stratiﬁed coverage violation
of RAPS. WriteCλ to mean the RAPS procedure for a ﬁxed choice of kreg andλ. Then we would
like to pick
λ = arg min
λ′
SSCV(Cλ′,{S}j=sj=1). (6)
In our experiments, we choose a relatively coarse partitioning of the possible set sizes: 0-1, 2-3, 4-
10, 11-100, and 101-1000. Then, we chose theλ∈{ 0.00001, 0.0001, 0.0008, 0.001, 0.0015, 0.002}
which minimized the size-stratiﬁed coverage violation on the tuning set. The results in Table 5
show RAPS always outperforms the adaptiveness of APS on the test set, even with this coarse,
automated choice of parameters. The table reports the median size-stratiﬁed coverage violation over
10 independent trials of APS and RAPS with automated parameter tuning.
4.3 A LTERNATIVES TO CONDITIONAL COVERAGE
Lastly, we argue that conditional coverage is a poor notion of adaptiveness when the best possible
model (i.e., one ﬁt on inﬁnite data) has high accuracy. Given such a model, the oracle procedure
from Romano et al. (2020) would return the correct label with probability 1−α and the empty set
with probabilityα. That is, having correct conditional coverage for high-signal problems whereY is
perfectly determined byX requires a perfect classiﬁer. In our experiments on ImageNet, APS does
not approximate this behavior. Therefore, conditional coverage isn’t the right goal for prediction sets
with realistic sample sizes. Proposition 3 and the SSCV criterion suggests a relaxation; we could
require that we have the right coverage, no matter the size of the prediction set: P (Y ∈C (X)|
{|C(x)|∈A} )≥ 1−α for anyA⊂{ 0, 1, 2,... }. We view this as a promising way to reason
about adaptiveness in high-signal problems such as image classiﬁcation.
5 D ISCUSSION
For classiﬁcation tasks with many possible labels, our method enables a researcher to take any base
classiﬁer and return predictive sets guaranteed to achieve a pre-speciﬁed error level, such as 90%,
while retaining small average size. It is simple to deploy, so it is an attractive, automatic way to
quantify the uncertainty of image classiﬁers—an essential task in such settings as medical diag-
nostics, self-driving vehicles, and ﬂagging dangerous internet content. Predictive sets in computer
vision (from RAPS and other conformal methods) have many further uses, since they systemati-
cally identify hard test-time examples. Finding such examples is useful in active learning where

=== PDF PAGE 14 ===
Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.794 0.945 0.905 0.938 0.950 0.950 5.64 36.4 46.3 4.21
ResNet152 0.783 0.940 0.950 0.943 0.950 0.950 6.36 19.6 22.5 4.40
ResNet101 0.774 0.936 0.950 0.944 0.950 0.950 6.79 20.6 23.2 4.79
ResNet50 0.762 0.929 0.951 0.943 0.950 0.950 8.12 22.9 26.2 5.57
ResNet18 0.698 0.891 0.950 0.943 0.950 0.950 16.0 28.9 33.2 11.7
DenseNet161 0.772 0.936 0.950 0.942 0.950 0.950 6.84 23.4 28.0 5.09
VGG16 0.716 0.904 0.950 0.943 0.950 0.950 12.9 24.6 27.8 8.98
Inception 0.695 0.887 0.950 0.937 0.950 0.950 20.3 142.0 168.0 18.5
ShufﬂeNet 0.694 0.883 0.950 0.940 0.950 0.950 19.3 58.7 71.6 16.3
Table 6: Results on Imagenet-Val. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials. See Section 3.1 for full details.
Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.678 0.875 0.950 0.937 0.950 0.950 21.7 86.2 107.0 18.5
ResNet152 0.670 0.876 0.951 0.944 0.950 0.950 21.3 51.0 56.6 16.2
ResNet101 0.656 0.86 0.95 0.944 0.950 0.949 25.7 55.8 63.1 19.1
ResNet50 0.634 0.847 0.949 0.944 0.949 0.950 29.5 58.6 65.9 21.5
ResNet18 0.572 0.802 0.950 0.942 0.950 0.949 48.3 65.0 74.0 35.3
DenseNet161 0.653 0.861 0.951 0.941 0.950 0.949 25.9 60.0 72.7 20.4
VGG16 0.588 0.816 0.950 0.943 0.950 0.949 38.5 57.8 63.9 26.4
Inception 0.573 0.797 0.950 0.943 0.949 0.950 73.1 253.0 275.0 70.2
ShufﬂeNet 0.560 0.781 0.950 0.941 0.949 0.949 80.0 125.0 140.0 67.4
Table 7: Results on Imagenet-V2. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials at the 5% level. See Section 3.2 for full details.
B R ANDOMIZED PREDICTORS
The reader may wonder why we choose to use a randomized procedure. The randomization is
needed to achieve 1−α coverage exactly, which we will explain via an example. Note that the
randomization is of little practical importance, since the predictive set output by the randomized
procedure will differ from the that of the non-randomized procedure by at most one element.
Turning to an example, assume for a particular input image we expect a set of size k to have 91%
coverage, and a set of sizek− 1 to have 89% coverage. In order to achieve our desired coverage of
90%, we randomly choose size k ork− 1 with equal probability. In general, the probabilities will
not be equal, but rather chosen so the weighted average of the two coverages is exactly 90%. If a
user of our method desires deterministic sets, it is easy to turn off this randomization with a single
ﬂag, resulting in slightly conservative sets.
C I MAGENET AND IMAGENET V2 RESULTS FOR α = 5%
We repeated Experiments 1 and 2 withα = 5%. See the results in Tables 6 and 7.
D C OVERAGE AND SIZE CONDITIONAL ON IMAGE DIFFICULTY
In order to probe the adaptiveness properties of APS and RAPS we stratiﬁed coverage and size by
image difﬁculty (the position of the true label in the list of most likely to least likely classes, based
on the classiﬁer predictions) in Table 8. With increasing λ, coverage decreases for more difﬁcult
images and increases for easier ones. In the most difﬁcult regime, even thoughAPS can output large
sets, those sets still rarely contain the true class. This suggests regularization is a sensible way to

=== PDF PAGE 15 ===
λ = 0 λ = 0.001 λ = 0.01 λ = 0.1 λ = 1
difﬁculty count cvg sz cvg sz cvg sz cvg sz cvg sz
1 15668 0.95 5.2 0.95 3.8 0.96 2.5 0.97 2.0 0.98 2.0
2 to 3 2578 0.78 15.7 0.78 10.5 0.80 6.0 0.84 3.9 0.86 3.6
4 to 6 717 0.68 31.7 0.68 19.7 0.70 9.7 0.71 5.3 0.64 4.4
7 to 10 334 0.63 41.0 0.63 24.9 0.60 11.6 0.22 5.7 0.00 4.5
11 to 100 622 0.55 57.8 0.51 34.1 0.26 14.7 0.00 6.4 0.00 4.6
101 to 1000 81 0.23 96.7 0.00 51.6 0.00 19.1 0.00 7.1 0.00 4.7
Table 8: Coverage and size conditional on difﬁculty.We report coverage and size ofRAPS sets using ResNet-
152 withkreg = 5 and varyingλ (recall thatλ = 0 is the APS procedure). The desired coverage level is 90%.
The ‘difﬁculty’ is the ranking of the true class’s estimated probability.
stabilize the sets. As a ﬁnal word on Table 8, notice that as λ increases, coverage improves for the
more common medium-difﬁculty examples, although not for very rare and difﬁcult ones.
E C HOOSING kreg AND λ TO OPTIMIZE SET SIZE
This section describes two procedures for picking kreg andλ that optimize for set size or adaptive-
ness, outperforming APS in both cases.
Algorithm 4 Adaptive Fixed-K
Input: α; I ∈{ 1,...,K}n×K, and y∈{ 0, 1,...,K}n corresponding respectively to the classes
from highest to lowest estimated probability mass, and labels for each of n examples in the
dataset
1: procedure GET-KSTAR (α,I,y)
2: fori∈{ 1,··· ,n} do
3: Li←j such thatIi,j =yi
4: ˆk∗← the⌈(1−α)(1 +n)⌉ largest value in{Li}ni=1
5: return ˆk∗
Output: The estimate of the smallest ﬁxed size set that achieves coverage, ˆk∗
To produce Tables 1, 6, 2, and 7, we chosekreg andλ adaptively. This required an extra data splitting
step, where a small amount of tuning data
xi,yi
}m
i=1 were used to estimatek∗, and thenkreg is settok∗. Takingm≈ 1000 was sufﬁcient, since the algorithm is fairly insensitive tokreg (see Table 3).
Then, ˆk∗ was calculated with Algorithm 4. We produced the Imagenet V2 tables with m = 1000
and the Imagenet tables withm = 10000.
After choosing ˆk∗, we choseλ to have small set size. We used the same tuning data to pickˆk∗ andλ
for simplicity (this does not invalidate our coverage guarantee since conformal calibration still uses
fresh data). A coarse grid search on λ sufﬁced, since small parameter variations have little impact
on RAPS. For example, we chose theλ∈{ 0.001, 0.01, 0.1, 0.2, 0.5} that achieved the smallest size
on the m holdout samples in order to produce Tables 1, 6, 2, and 7. We include a subroutine that
automatically chooses ˆk∗ andλ to optimize size in our GitHub codebase.
F C OMPARISON WITH LEAST AMBIGUOUS SET-VALUED CLASSIFIERS
In this section, we compare RAPS to the Least Ambiguous Set-valued Classiﬁer ( LAC) method
introduced in ?, an alternative conformal procedure that is designed to have small sets. The LAC
method provable gives the smallest possible average set size in the case where the input probabilities
are correct, with the idea that these sets should be small even when the estimated probabilities are
only approximately correct. In the notation of this paper, the LAC method considers nested sets of
the following form:
CLAC(x,τ ) :={y : ˆπx(y)≥ 1−τ},
which can be calibrated using as before in using ˆτccal from Eq. (3).

=== PDF PAGE 16 ===
We ﬁrst compare naive, APS, RAPS, and LAC in terms of power and coverage in Table 9. In this
experiment, we tuned RAPS to have small set size as described in Appendix E. We see thatLAC also
achieves correct coverage, as expected since it is a conformal method and satisﬁes the guarantee
from Theorem 1. We further see that it has systematically smaller sets that RAPS, although the
difference is slight compared to the gap between APS and RAPS or APS and LAC.
We next compare RAPS to LAC in terms of adaptiveness, tuning RAPS as in Section 4.2. First, in
Table 10, we report on the coverage of LAC for images of different difﬁculties, and see that LAC
has dramatically worse coverage for hard images than for easy ones. Comparing this to RAPS in
Table 8, we see that RAPS also has worse coverage for more difﬁcult images, although the gap is
much smaller for RAPS. Next, in Table 11, we report on the SSCV metric for of adaptiveness (and
conditional coverage) for APS, RAPS, and LAC. We ﬁnd that APS and RAPS have much better
adaptiveness than LAC, with RAPS being the overall winner. The results of all of these comparisons
are expected: LAC is not targetting adpativeness and instead trying to achieve the smallest possible
set size. It succeeds at its goal, sacriﬁcing adaptiveness to do so.

=== PDF PAGE 17 ===
Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS LAC Top K Naive APS RAPS LAC
ResNeXt101 0.793 0.945 0.900 0.889 0.900 0.900 0.900 2.42 17.2 19.9 2.01 1.65
ResNet152 0.783 0.941 0.900 0.894 0.900 0.900 0.900 2.64 9.68 10.4 2.09 1.76
ResNet101 0.774 0.936 0.900 0.895 0.900 0.900 0.900 2.83 10.0 10.8 2.25 1.87
ResNet50 0.761 0.929 0.899 0.896 0.900 0.900 0.900 3.13 11.7 12.3 2.55 2.05
ResNet18 0.698 0.891 0.900 0.895 0.900 0.900 0.900 5.74 15.3 16.1 4.38 3.64
DenseNet161 0.771 0.936 0.900 0.894 0.900 0.900 0.900 2.84 11.2 12.0 2.29 1.90
VGG16 0.716 0.904 0.900 0.896 0.901 0.900 0.900 4.75 13.4 14.1 3.54 3.00
Inception 0.695 0.886 0.899 0.884 0.900 0.899 0.900 6.27 74.8 88.8 5.24 4.06
ShufﬂeNet 0.694 0.883 0.900 0.892 0.900 0.899 0.900 6.45 28.8 32.1 5.01 4.14
Table 9: Results on Imagenet-Val. We report coverage and size of the optimal, randomized ﬁxed sets,naive, APS, RAPS , and the LAC sets for nine different Imagenet classiﬁers.
The median-of-means for each column is reported over 100 different trials at the 10% level. See Section 3.1 for full details.</message>
<message type="ai">
  <content><reasoning>**Verifying source-code URLs**</reasoning></content>
  <tool_call id="call_e5cc105d2d674d5cba2b0ef5ea6f19a8" name="read_file">{"file_path": "/work/literature/2009.14193.txt", "limit": 280, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-280 of 898 | next offset 280 @@
=== PDF PAGE 1 ===
UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in computer vision.
Formally, for a discrete responseY ∈Y ={1,...,K } and a feature vectorX∈ Rd, we desire an
uncertainty set function,C(X), mapping a feature vector to a subset of{1,...,K } such that
P (Y ∈C (X))≥ 1−α, (1)
for a pre-speciﬁed conﬁdence levelα such as 10%. Conformal predictors like our method can mod-
ify any black-box classiﬁer to output predictive sets that are rigorously guaranteed to satisfy the
∗equal contribution
†Project website here.
1
arXiv:2009.14193v5  [cs.CV]  3 Sep 2022

=== PDF PAGE 2 ===
Figure 1: Prediction set examples on Imagenet. We show three examples of the class fox squirrel and
the 95% prediction sets generated by RAPS to illustrate how the size of the set changes as a function of the
difﬁculty of a test-time image.
desired coverage property shown in Eq. (1). For evaluations, we focus on Imagenet classiﬁcation
using convolutional neural networks (CNNs) as the base classiﬁers, since this is a particularly chal-
lenging testbed. In this setting,X would be the image andY would be the class label. Note that the
guarantee in Eq. (1) is marginal overX andY —it holds on average, not for a particular imageX.
A ﬁrst approach toward this goal might be to assemble the set by including classes from highest to
lowest probability (e.g., after Platt scaling and a softmax function; see Platt et al., 1999; Guo et al.,
2017) until their sum just exceeds the threshold 1−α. We call this strategy naive and formulate
it precisely in Algorithm 1. There are two problems with naive: ﬁrst, the probabilities output by
CNNs are known to be incorrect (Nixon et al., 2019), so the sets from naive do not achieve cov-
erage. Second, image classiﬁcation models’ tail probabilities are often badly miscalibrated, leading
to large sets that do not faithfully articulate the uncertainty of the model; see Section 2.3. Moreover,
smaller sets that achieve the same coverage level can be generated with other methods.
The coverage problem can be solved by picking a new threshold using holdout samples. For exam-
ple, withα =10%, if choosing sets that contain 93% estimated probability achieves 90% coverage
on the holdout set, we use the 93% cutoff instead. We refer to this algorithm, introduced in Ro-
mano et al. (2020), as Adaptive Prediction Sets (APS). The APS procedure provides coverage but
still produces large sets. To ﬁx this, we introduce a regularization technique that tempers the in-
ﬂuence of these noisy estimates, leading to smaller, more stable sets. We describe our proposed
algorithm, Regularized Adaptive Prediction Sets (RAPS), in Algorithms 2 and 3 (with APS as a
special case). As we will see in Section 2, both APS and RAPS are always guaranteed to satisfy
Eq. (1)—regardless of model and dataset. Furthermore, we show that RAPS is guaranteed to have
better performance than choosing a ﬁxed-size set. Both methods impose negligible computational
requirements in both training and evaluation, and output useful estimates of the model’s uncertainty
on a new image given, say, 1000 held-out examples.
In Section 3 we conduct the most extensive evaluation of conformal prediction in deep learning to
date on Imagenet and Imagenet-V2. We ﬁnd that RAPS sets always have smaller average size than
naive and APSsets. For example, using a ResNeXt-101, naive does not achieve coverage, while
APS and RAPS achieve it almost exactly. However,APS sets have an average size of 19, whileRAPS
sets have an average size of 2 atα = 10% (Figure 2 and Table 1). We will provide an accompanying
codebase that implements our method as a wrapper for any PyTorch classiﬁer, along with code to
exactly reproduce all of our experiments.
1.1 R ELATED WORK
Reliably estimating predictive uncertainty for neural networks is an unsolved problem. Historically,
the standard approach has been to train a Bayesian neural network to learn a distribution over net-
work weights (Quinonero-Candela et al., 2005; MacKay, 1992; Neal, 2012; Kuleshov et al., 2018;
Gal, 2016). This approach requires computational and algorithmic modiﬁcations; other approaches
avoid these via ensembles (Lakshminarayanan et al., 2017; Jiang et al., 2018) or approximations of
Bayesian inference (Riquelme et al., 2018; Sensoy et al., 2018). These methods also have major
practical limitations; for example, ensembling requires training many copies of a neural network ad-
versarially. Therefore, the most widely used strategy is ad-hoctraditional calibration of the softmax
scores with Platt scaling (Platt et al., 1999; Guo et al., 2017; Nixon et al., 2019).
2

=== PDF PAGE 3 ===
0.9 0.95 0.99
desired coverage (1- )
0.85
0.90
0.95
1.00empirical coverage
Naive
APS
RAPS
0.9 0.95 0.99
desired coverage (1- )
0
20
40
60
80
100average size
Figure 2: Coverage and average set size on Imagenet for prediction sets from three methods.All methods
use a ResNet-152 as the base classiﬁer, and results are reported for 100 random splits of Imagenet-Val, each of
size 20K. See Section 3.1 for full details.
This work develops a method for uncertainty quantiﬁcation based onconformal prediction. Originat-
ing in the online learning literature, conformal prediction is an approach for generating predictive
sets that satisfy the coverage property in Eq. (1) (V ovk et al., 1999; 2005). We use a convenient
data-splitting version known as split conformal prediction that enables conformal prediction meth-
ods to be deployed for essentially any predictor (Papadopoulos et al., 2002; Lei et al., 2018). While
mechanically very different from traditional calibration as discussed above, we will refer to our
approach as conformal calibration to highlight that the two methodologies have overlapping but
different goals.
Conformal prediction is a general framework, not a speciﬁc algorithm—important design decisions
must be made to achieve the best performance for each context. To this end, Romano et al. (2020)
and Cauchois et al. (2020) introduce techniques aimed at achieving coverage that is similar across
regions of feature space, whereas ?Hechtlinger et al. (2018) and ? introduce techniques aimed at
achieving equal coverage for each class. While these methods have conceptual appeal, thus far
there has been limited empirical evaluation of this general approach for state-of-the-art CNNs. Con-
cretely, the only works that we are aware of that include some evaluation of conformal methods on
ImageNet—the gold standard for benchmarking computer vision methods—are Hechtlinger et al.
(2018), Park et al. (2019), Cauchois et al. (2020), and Messoudi et al. (2020), although in all four
cases further experiments are needed to more fully evaluate their operating characteristics for practi-
cal deployment. At the heart of conformal prediction is theconformal score: a measure of similarity
between labeled examples which is used to compare a new point to among those in a hold out set.
Our theoretical contribution can be summarized as a modiﬁcation of the conformal score from Ro-
mano et al. (2020) to have smaller, more stable sets. Lastly, there are alternative approaches to
returning prediction sets not based on conformal prediction (Pearce et al., 2018; Zhang et al., 2018).
These methods can be used as input to a conformal procedure to potentially improve performance,
but they do not have ﬁnite-sample coverage guarantees when used alone.
2 M ETHODS
In developing uncertainty set methods to improve upon naive, we are guided by three desiderata.
First and most importantly, the coverage desideratum says the sets must provide 1−α coverage, as
Algorithm 1 Naive Prediction Sets
Input: α, sorted scoress, associated permutation of classesI, booleanrand
1: procedure NAIVE (α,s,I,rand )
2: L← 1
3: while∑Li=1si &lt; 1−α do ⊿ Stop if 1−α probability exceeded
4: L←L + 1
5: ifrand then ⊿ Break ties randomly (explained in Appendix B)
6: U← Unif(0, 1)
7: V ← (∑Li=1si− (1−α))/sL
8: ifU≤V then
9: L←L− 1
10: return
{
I1,...,I L
}
Output: The 1−α prediction set,
{
I1,...,I L
}
3

=== PDF PAGE 4 ===
τ^ccal0
25%
50%
75%
1−α′
100%
τ: set size parameter
empirical coverage
(a) Conformal calibration
0.50.5
0.770.77
0.920.92
1.021.02
1.091.09 1.151.15
kreg τ^ccal
0.0
0.2
0.4
c d f b e a
class
penalized probability
penalty
probability (b) A RAPS prediction set
Figure 3: Visualizations of conformal calibration and RAPS sets. In the left panel, the y-axis shows the
empirical coverage on the conformal calibration set, and 1−α′ =⌈(n + 1)(1−α)⌉/n. In the right panel, the
printed numbers indicate the cumulative probability plus penalty mass. For the indicated value ˆτccal, the RAPS
prediction set is{c, d, f, b}.
discussed above. Secondly, the size desideratum says we want sets of small size, since these convey
more detailed information and may be more useful in practice. Lastly, the adaptiveness desidera-
tum says we want the sets to communicate instance-wise uncertainty: they should be smaller for
easy test-time examples than for hard ones; see Figure 1 for an illustration. Coverage and size
are obviously competing objectives, but size and adaptiveness are also often in tension. The size
desideratum seeks small sets, while the adaptiveness desideratum seeks larger sets when the classi-
ﬁer is uncertain. For example, always predicting a set of size ﬁve could achieve coverage, but it is
not adaptive. As noted above, both APSand RAPS achieve correct coverage, and we will show that
RAPS improves upon APS according to the other two desiderata.
We now turn to the speciﬁcs of our proposed method. We begin in Subsection 2.1 by describing an
abstract data-splitting procedure called conformal calibration that enables the near-automatic con-
struction of valid predictive sets (that is, sets satisfying Eq. (1)). Subsequently, in Subsection 2.2, we
provide a detailed presentation of our procedure, with commentary in Section 2.3. In Subsection 2.4
we discuss the optimality of our procedure, proving that it is at least as good as the procedure that
returns sets of a ﬁxed size, unlike alternative approaches.
2.1 C ONFORMAL CALIBRATION
We ﬁrst review a general technique for producing valid prediction sets, following the articulation
in Gupta et al. (2019). Consider a procedure that outputs a predictive set for each observation,
and further suppose that this procedure has a tuning parameter τ that controls the size of the sets.
(In RAPS, τ is the cumulative sum of the sorted, penalized classiﬁer scores.) We take a small
independent conformal calibration set of data, and then choose the tuning parameter τ such that
the predictive sets are large enough to achieve 1−α coverage on this set. See Figure 3 for an
illustration. This calibration step yields a choice ofτ, and the resulting set is formally guaranteed to
have coverage 1−α on a future test point from the same distribution; see Theorem 1 below.
Formally, let (Xi,Yi)i=1,...,n be an independent and identically distributed (i.i.d.) set of variables
that was not used for model training. Further, let C(x,u,τ ) : Rd× [0, 1]× R→ 2Y be a set-
valued function that takes a feature vectorx to a subset of the possible labels. The second argument
u is included to allow for randomized procedures; let U1,...,U n be i.i.d. uniform [0, 1] random
variables that will serve as the second argument for each data point. Suppose that the sets are
indexed byτ such that they are nested, meaning larger values ofτ lead to larger sets:
C(x,u,τ 1)⊆C (x,u,τ 2) if τ1≤τ2. (2)
To ﬁnd a function that will achieve 1−α coverage on test data, we select the smallest τ that gives
at least 1−α coverage on the conformal calibration set, with a slight correction to account for the
ﬁnite sample size:
ˆτccal = inf
{
τ :|{i :Yi∈C (Xi,Ui,τ )}|n ≥⌈(n + 1)(1−α)⌉n }. (3)
The set function C(x,u,τ ) with this data-driven choice of τ is guaranteed to have correct ﬁnite-
sample coverage on a fresh test observation, as stated formally next.
4

=== PDF PAGE 5 ===
Theorem 1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi,Ui)i=1,...,n and
(Xn+1,Yn+1,Un+1) are i.i.d. and letC(x,u,τ ) be a set-valued function satisfying the nesting prop-
erty in Eq. (2). Suppose further that the sets C(x,u,τ ) grow to include all labels for large enough
τ: for all x∈ Rd,C(x,u,τ ) = Y for some τ. Then for ˆτccal deﬁned as in Eq. (3), we have the
following coverage guarantee:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≥ 1−α.
This is the same coverage property as Eq. (1) in the introduction, written in a more explicit manner.
The result is not new—a special case of this result leveraging sample-splitting ﬁrst appears in the
regression setting in Papadopoulos et al. (2002), and the core idea of conformal prediction was
introduced even earlier; see V ovk et al. (2005).
As a technical remark, the theorem also holds if the observations to satisfy the weaker condition
of exchangeability; see V ovk et al. (2005). In addition, for most families of set-valued functions
C(x,u,τ ) there is a matching upper bound:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≤ 1−α + 1n + 1.
Roughly speaking, this will hold whenever the sets grow smoothly in τ. See Lei et al. (2018) for a
formal statement of the required conditions.
2.2 O UR METHOD
Conformal calibration is a powerful general idea, allowing one to achieve the coverage desideratum
for any choice of setsC(x,u,τ ). Nonetheless, this is not yet a full solution, since the quality of the
resulting prediction sets can vary dramatically depending on the design ofC(x,u,τ ). In particular,
we recall the size and adaptiveness desiderata from Section 1—we want our uncertainty sets to be
as small as possible while faithfully articulating the instance-wise uncertainty of each test point. In
this section, we explicitly give our algorithm, which can be viewed as a special case of conformal
calibration with the uncertainty setsC designed to extract information from CNNs.
Our algorithm has three main ingredients. First, for a feature vector x, the base model computes
class probabilities ˆπx∈ Rk, and we order the classes from most probable to least probable. Then,
we add a regularization term to promote small predictive sets. Finally, we conformally calibrate the
penalized prediction sets to guarantee coverage on future test points.
Formally, letρx(y) =∑Ky′=1 ˆπx(y′)I{ˆπx(y′)&gt;ˆπx(y)} be the total probability mass of the set of labels
that are more likely than y. These are all the labels that will be included before y is included. In
addition, letox(y) =|{y′∈Y : ˆπx(y′)≥ ˆπx(y)}| be the ranking ofy among the label based on the
probabilities ˆπ. For example, ify is the third most likely label, thenox(y) = 3.1 We take
C∗(x,u,τ ) :={y : ρx(y) + ˆπx(y)·u +λ· (ox(y)−kreg)+| {z }
regularization</message>
<message type="ai">
  <content><reasoning>**Preparing source hyperlink**</reasoning></content>
  <tool_call id="call_cb041d7f67f34a3a963e352ccd8288e2" name="execute">{"command": "python -c 'from pypdf import PdfReader; import json; from pathlib import Path; out={}; exec(\"for id in [\\\"2107.07511\\\",\\\"1904.06019\\\",\\\"2009.14193\\\",\\\"2402.10723\\\"]:\\n r=PdfReader(\\\"/work/literature/\\\"+id+\\\".pdf\\\"); links=[]\\n for pn,p in enumerate(r.pages):\\n  for a in p.get(\\\"/Annots\\\",[]):\\n   a=a.get_object(); action=a.get(\\\"/A\\\",{}); uri=action.get(\\\"/URI\\\")\\n   if uri and any(s in str(uri).lower() for s in [\\\"github\\\",\\\"code\\\",\\\"zenodo\\\"]): links.append({\\\"pdf_page\\\":pn+1,\\\"uri\\\":str(uri)})\\n out[id]=links\\n\"); print(json.dumps(out,indent=2)); Path(\"/work/literature/embedded_code_links.json\").write_text(json.dumps(out,indent=2))'", "timeout": 90}</tool_call>
</message>
<message type="tool">{
  "2107.07511": [
    {
      "pdf_page": 1,
      "uri": "https://github.com/aangelopoulos/conformal-prediction"
    },
    {
      "pdf_page": 4,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/imagenet-smallest-sets.ipynb"
    },
    {
      "pdf_page": 7,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/imagenet-aps.ipynb"
    },
    {
      "pdf_page": 7,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/imagenet-raps.ipynb"
    },
    {
      "pdf_page": 8,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/meps-cqr.ipynb"
    },
    {
      "pdf_page": 10,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/meps-uncertainty-scalar.ipynb"
    },
    {
      "pdf_page": 15,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/correctness_checks.ipynb"
    },
    {
      "pdf_page": 16,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/correctness_checks.ipynb"
    },
    {
      "pdf_page": 23,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/multilabel-classification-mscoco.ipynb"
    },
    {
      "pdf_page": 23,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/tumor-segmentation.ipynb"
    },
    {
      "pdf_page": 24,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/weather-time-series-distribution-shift.ipynb"
    },
    {
      "pdf_page": 25,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/toxic-text-outlier-detection.ipynb"
    },
    {
      "pdf_page": 26,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/imagenet-selective-classification.ipynb"
    },
    {
      "pdf_page": 32,
      "uri": "https://github.com/scikit-learn-contrib/MAPIE"
    },
    {
      "pdf_page": 32,
      "uri": "https://github.com/valeman/awesome-conformal-prediction"
    },
    {
      "pdf_page": 32,
      "uri": "https://github.com/valeman/awesome-conformal-prediction"
    },
    {
      "pdf_page": 50,
      "uri": "https://github.com/aangelopoulos/conformal-prediction/blob/main/notebooks/correctness_checks.ipynb"
    }
  ],
  "1904.06019": [
    {
      "pdf_page": 5,
      "uri": "http://www.github.com/ryantibs/conformal/"
    }
  ],
  "2009.14193": [
    {
      "pdf_page": 1,
      "uri": "https://github.com/aangelopoulos/conformal_classification/"
    }
  ],
  "2402.10723": [
    {
      "pdf_page": 6,
      "uri": "https://github.com/alireza-javanmardi/conformal-credal-sets"
    },
    {
      "pdf_page": 7,
      "uri": "https://huggingface.co/cross-encoder/nli-deberta-base"
    }
  ]
}

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking Theorem 4.2 proof**</reasoning></content>
  <tool_call id="call_411b24523922408a990b0221b390d24e" name="read_file">{"file_path": "/skills/evomath-tao/SKILL.md", "limit": 1000, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-336 of 336 @@
---
name: evomath-tao
description: "Use this skill whenever the user submits a non-trivial mathematical claim that needs a rigorous proof or audit. Trigger on IMO/Putnam/USAMO/Olympiad-style problems, ML/AI theoretical statements, research conjectures, suspected-false claims, multi-step proofs the user already failed on, proof drafts with possible hidden assumptions, or any request containing 'prove rigorously', 'verify this', 'is this true', 'find the gap', 'audit my proof', 'find a counterexample', or 'use EvoMath' that targets a mathematical claim. Activate also when the problem requires more than three reasoning steps. Do NOT use for single-step calculations, definition lookups, textbook exercises with a known recipe, code analysis tasks, literature survey questions, pure symbolic manipulation, or non-mathematical applications of those trigger phrases (e.g., 'is it true that GPT-4 can solve math?', 'verify this LaTeX syntax'); hand those back instead."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: EvoScientist
  version: '1.0.0'
  tags: [core, math, proof, olympiad, research]
---

# EvoMath (Tao-style)

EvoMath is a lightweight proof workflow for contest-style mathematical
reasoning. Its job is to produce a rigorous proof, a verified counterexample, a
useful partial result, or a clear handoff. Keep the process small; do not run a
heavy audit pipeline by default.

## Methodology Anchor — Terence Tao's Research-Math Practice

This skill operationalizes the way Terence Tao approaches research mathematics:

1. **Compute small cases first** (Kepler before Newton) — build intuition from data before reaching for theory.
2. **Try the standard toolbox broadly before going deep** — most hard problems crack to a standard technique; the few that don't only reveal which after several have failed.
3. **Hold rigor and intuition together** (post-rigorous mathematics) — trust intuition, but verify every step. "It feels right" is a hypothesis, not a proof.
4. **Atomize when stuck** — decompose into independently checkable sub-claims. A clean map of proved / conjectured / open beats a polished but shaky narrative.
5. **Stay honest about what isn't proved** — distinguish PROVED / VERIFIED_NUMERICALLY / CONJECTURED / HANDED_OFF. When blocked, name the precise gap.
6. **Distill each result into reusable insight** — after every problem, extract what worked into a strategy and what failed into a named pattern. Mathematical maturity is accumulated meta-insight.

Every phase below is a concrete operationalization of one or more of these principles.

## Operating Rules

- Use Markdown notes for handoff between steps. Do not require JSON/YAML unless
  a script explicitly asks for it.
- Keep only compact state: plan, verified claims, failed attempts, final audit.
  Do not pass long failed derivations into later prompts.
- Prefer a few independent proof attempts over one long derivation.
- **Numerical verification is NOT a proof step** (math-olympiad rule). Checking
  a claim on n=1..100 and finding no counterexample does NOT make it PROVED;
  the strongest label such evidence can earn is VERIFIED_NUMERICALLY.
- Exact arithmetic can refute; approximate numerics only suggest.
- A proof is final only after an adversarial check of the clean proof.
- **Calibrated abstention over bluffing**: when verification fails repeatedly,
  admit it. Return partial results and mark unfixed gaps explicitly (math-
  olympiad rule). Final status HANDED_OFF with a structured wall report is
  always preferable to PROVED with hand-waved gaps.
- Every final answer must include a visible `final-status: ...` line.
- Use TodoWrite to drive the workflow. Each step is one todo; you cannot mark a
  todo completed unless the corresponding `.md` file passes its validator.

If filesystem access is available, create a Markdown workspace with (script paths are relative to this skill's directory):

```bash
python scripts/evomath_workspace.py init --dir .evomath/current
```

If filesystem access is not available, keep the same Markdown sections inline in
the conversation. In that case run the validators by mentally checking the same
required fields the script checks — the discipline is the same.

## Fast Exit

Do not use EvoMath for single calculations, definition lookups, symbolic
manipulation, or answer-only requests with no proof obligation. Give the direct
answer instead. No TodoWrite list is needed for a Fast Exit.

If the statement has a blocking ambiguity that changes truth value, ask one
specific clarification question before solving.

## Execution Protocol (TodoWrite + Validation)

For any problem that passes the Fast Exit Gate, follow this protocol.

### 1. Create the 5-step todo list

Before doing any solving work, call TodoWrite with these five items in this
order. Each item names its primary reference file:

1. **Plan Briefly** — read `references/intake-checklist.md` for type
   classification, ambiguity handling, goal types.
2. **Try Candidates** — read `references/angles-by-type.md` for technique ideas
   if you are out of angles for this problem type.
3. **Assemble** — read `references/output-formats.md` if you need formatting
   conventions or LaTeX templates.
4. **Audit** — read `references/grading-taxonomy.md` for issue classes and
   severity rules. Read `references/phase-4-audit.md` only if the user requests
   strict multi-reviewer audit.
5. **Reflect** — read `references/claim-memory.md` only when deep reflection is
   triggered (see "Deep Reflection Triggers" below).

### 2. Per-step discipline

For each step in order:

1. Mark the todo `in_progress` before reading the reference or writing output.
2. Read the referenced file(s) if and only if you need them for this step.
3. Produce the corresponding `.md` output (plan.md, candidates.md, audit.md,
   final.md sections, etc.).
4. Run the validator before marking the todo completed:

   ```bash
   python scripts/evomath_workspace.py validate-phase &lt;N&gt; --dir .evomath/current
   ```

5. If validation FAILS, the todo stays `in_progress`. Revise the `.md` file
   based on the printed failure messages and re-run the validator. Do not mark
   completed until the validator exits 0.

### 3. PROVED gate

If your final-status is `PROVED`, you MUST additionally run:

```bash
python scripts/evomath_workspace.py validate-proved --dir .evomath/current
```

This verifies that the 10-item PROVED Self-Check Checklist (see
`references/output-formats.md`) is present in final.md with all boxes ticked.
If this fails, downgrade final-status to CONJECTURED or HANDED_OFF and revise
the answer.

### 4. Deep Reflection Triggers

Step 5 (Reflect) has two modes:

- **Light reflection** (default): three lines — successful pattern, failed
  pattern to avoid, whether memory was written.
- **Deep reflection** (triggered when any of the following hold):
  - Step 2 required 3+ revision rounds for any candidate
  - Step 4 identified a fatal flaw before the final repair
  - A new winning technique appeared that is not yet in any L2 strategy entry
  - The user explicitly asks for self-evolution or cross-problem learning
  - final-status is HANDED_OFF with a recurring failure-mode

  In deep reflection mode, run the full ESE/IVE protocols described in
  `references/claim-memory.md` and update L2/L3 memory in
  `.evomath/session-memory.md`.

### 5. Fallback when filesystem is unavailable

If you cannot run scripts, keep the same TodoWrite discipline:
- Still create the 5-item list and march through it.
- Still keep the same `.md` sections inline in the conversation.
- Substitute mental validation for the script call — check the same required
  fields the validator would check.

## Workflow

### 1. Plan Briefly

Write a short Markdown plan:

- Problem type: algebra, geometry, number theory, combinatorics, analysis, or
  other.
- Goal: prove, refute, find example, or audit proof.
- Strategy: one sentence.
- Subgoals: at most five bullets.

For "determine all" problems, include both:

- existence/construction
- impossibility/exclusion

For a simple problem, one root subgoal is enough.

### 2. Try Candidates

**Mode dispatch** (decide before generating):

- If Phase 0 `goal = find-numeric-answer` (AIME-style: answer is a single
  number, no proof required) → **AIME mode**: generate 5–7 short candidate
  answers using varied approaches (small-case enumeration, modular invariants,
  algebraic manipulation, generating functions, brute-force code). Take
  majority vote across candidates. Verify the top two by substitution into the
  original problem. Skip the rest of the proof workflow; output the numeric
  answer with `final-status: PROVED` only when both top candidates agree AND
  substitution checks pass.
- Otherwise → **Proof mode**: continue below.

**Proof mode — per-candidate 5-round internal loop**:

For each active subgoal, try up to four genuinely different candidate routes.
Each candidate is itself the product of a 5-round internal mini-process — not
a one-shot generation:

1. **Solve** — produce a proof attempt using reasoning only. **No tool use
   during this round** (no calculator, sympy, Lean, web). Pure pencil-and-paper.
2. **Self-improve** — refine the attempt for clarity, fix obvious gaps.
3. **Self-verify** — walk through line by line, looking for: shielding words
   ("obviously"/"clearly"), unjustified swaps, missing hypotheses, off-by-one
   cases, hidden assumptions.
4. **Correct** — fix issues found in step 3.
5. Repeat 1–4 up to **5 times** per candidate, or until the candidate self-
   reports as `is_sound`.

Each candidate's internal-rounds count is recorded so Phase 4 can see how much
self-revision was needed. A candidate that needs 5 rounds is more likely to be
borderline than one that's sound in 1.

Record candidates in this Markdown table:

| Candidate | Idea | Internal rounds | Verdict | Issue or reason |
|---|---|---|---|---|
| C1 |  | 1–5 | sound / repair / fail |  |

Judging a candidate:

- `sound`: enough to use as a verified claim.
- `repair`: promising but missing a local step; revise at most twice **outside**
  the 5-round internal loop (so total max revisions = 5 internal + 2 external).
- `fail`: wrong, circular, too weak, or repeats a known dead end.

**Computation discipline (math-olympiad VERBATIM rule)**: during the Solve
round, no tool calls. Computation is allowed in Phase 1 (Empirical) and in
Phase 5 Deep Mode, NEVER during Phase 2 Solve. This protects against
ritualized "I called sympy so it must be right" reasoning.

When a candidate is sound, add it to **Proof Artifact / Verified Claims** with
a one-paragraph proof summary. When a route fails, add one line to **Negative
Attempts** so it is not repeated.

Use `references/angles-by-type.md` only when you are out of ideas for a problem
type. Do not load it by default.

### 3. Assemble

Turn the accepted claims into a clean proof or refutation.

Rules:

- State the original claim.
- Present the final argument only; omit failed attempts.
- Justify every non-trivial step by a verified claim, theorem, construction, or exact
  computation.
- If a required subgoal remains unsolved, stop pretending the proof is complete:
  output a partial result or handoff.

### 4. Audit

Audit only the clean proof, not the exploration notes.

Check:

- The proof proves the original statement, not a weaker restatement.
- All cases, boundary values, degeneracies, and quantifiers are handled.
- No claim is cited without proof or explicit acceptance in the Proof Artifact.
- Refutations use an exactly verified counterexample.

**Audit follows math-olympiad's 3-safeguard pattern** (see `references/phase-4-audit.md`):
1. Verifier context isolation (strip thinking traces before review).
2. Asymmetric voting (4 HOLDS to confirm; 2 HOLE FOUND to refute).
3. Pigeonhole exit (stop launching reviewers after threshold).

Apply the named-pattern screen (P4 / P5 / P6 / P18 / P40 / P41 in `grading-taxonomy.md`) plus the counterexample-first rule before any PROVED award.

For ordinary use, one careful local audit is enough. Use the heavier
`references/phase-4-audit.md` protocol only when the user asks for strict
multi-reviewer audit or when the result is high-risk.

### 5. Reflect

After the final answer, add a short reflection note. It should be compact:

- successful pattern, if any
- failed pattern to avoid
- whether memory was written

Per-problem memory resets at the next problem. Cross-problem memory is optional:
write only compact strategy/failure summaries to `.evomath/session-memory.json`
when file access is available. If not written, say `memory-persisted: false`.

## Status Labels

Use exactly one:

| Status | Meaning |
|---|---|
| `PROVED` | Complete proof of the original statement passed Safeguards 1–3 audit. The strongest label EvoMath awards. |
| `REFUTED` | Exact counterexample or contradiction proof found |
| `VERIFIED_NUMERICALLY` | Finite exact checks only; no general proof. Numerical evidence is NOT a proof — this label exists to record empirical support honestly. |
| `CONJECTURED` | Strong partial evidence or partial proof, but incomplete |
| `HANDED_OFF` | Stopped with a precise remaining gap or user question |

Exactly one of these five labels must appear in every final answer. See `references/confidence-rules.md` for award conditions and promotion rules.

## Final Answer Shape

Use Markdown, not a rigid schema:

```markdown
final-status: PROVED

## Result
&lt;answer&gt;

## Proof / Report
&lt;clean proof, refutation, audit report, partial result, or handoff&gt;

## Audit
- audits-run:
- critical-issues:
- remaining-gaps:

## Proof Artifact
- verified claims:
- negative attempts:

## Reflection
- memory-persisted:
- storage-location:
- proposed-memory-updates:
```

For proof-audit requests, lead with findings ordered by severity, then give the
verdict and suggested repair.

## Optional Helpers

- `scripts/evomath_workspace.py`:
  - `init`         creates the five Markdown state files.
  - `check`        verifies `final.md` has a valid `final-status:` line.
  - `validate-phase N`  validates the .md output for step N (1..5). Use this
    before marking the corresponding todo completed. Add `--strict` to also
    re-validate all prior steps.
  - `validate-proved`  when final-status is PROVED, verifies the 10-item
    Self-Check Checklist is fully ticked.
- `references/angles-by-type.md`: technique ideas by problem type.
- `references/grading-taxonomy.md`: detailed flaw taxonomy for audits.
- `references/phase-4-audit.md`: heavier independent-review protocol.
- `references/output-formats.md`: optional Markdown/LaTeX formatting details +
  the PROVED Self-Check Checklist template.
- `references/claim-memory.md`: three-layer memory architecture and ESE/IVE
  reflection protocols. Read only in deep-reflection mode.
- `references/model-tier.md`: per-tier parameter table (Haiku / Sonnet /
  Opus). Read once at the start of Phase 0 to set K, internal-rounds, audit
  passes, and abstain thresholds for the active model.</message>
<message type="ai">
  <content><reasoning>**Locating the exact theorem**</reasoning></content>
  <tool_call id="call_c280f60efaae4a588c3ec86a870317e1" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2402.10723.pdf\"); print(\"PDF PAGE 11\\n\",r.pages[10].extract_text()); print(\"PDF PAGE 12\\n\",r.pages[11].extract_text())'", "timeout": 30}</tool_call>
</message>
<message type="tool">PDF PAGE 11
 Conformalized Credal Set Predictors A PREPRINT
Alex Kendall and Yarin Gal. What uncertainties do we need in bayesian deep learning for computer vision? Advances
in neural information processing systems, 30, 2017.
George Klir and Mark Wierman.Uncertainty-based information: elements of generalized information theory, volume 15.
Springer Science &amp; Business Media, 1999.
Adriana Kovashka, Olga Russakovsky, Li Fei-Fei, Kristen Grauman, et al. Crowdsourcing in computer vision.
Foundations and Trends® in computer graphics and Vision, 10, 2016.
Henrik Linusson, Ulf Johansson, and Henrik Bostr¨om. Efficient conformal predictor ensembles. Neurocomputing, 397,
2020.
Yixin Nie, Xiang Zhou, and Mohit Bansal. What can we learn from collective human opinions on natural language
inference data? In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing
(EMNLP). Association for Computational Linguistics, 2020.
Harris Papadopoulos, Kostas Proedrou, V olodya V ovk, and Alex Gammerman. Inductive confidence machines for
regression. In Machine Learning: ECML 2002: 13th European Conference on Machine Learning. Springer, 2002.
Ellie Pavlick and Tom Kwiatkowski. Inherent disagreements in human textual inferences. Transactions of the
Association for Computational Linguistics, 7, 2019.
Dennis Reidsma and Rieks op den Akker. Exploiting ‘subjective’annotations. In Coling 2008: Proceedings of the
workshop on Human Judgements in Computational Linguistics, pages 8–16, 2008.
Yaniv Romano, Evan Patterson, and Emmanuel Candes. Conformalized quantile regression. Advances in neural
information processing systems, 32, 2019.
Yaniv Romano, Matteo Sesia, and Emmanuel Candes. Classification with valid and adaptive coverage. Advances in
Neural Information Processing Systems, 2020.
Paul R¨ottger, Bertie Vidgen, Dirk Hovy, and Janet Pierrehumbert. Two contrasting data annotation paradigms for
subjective nlp tasks. In Proceedings of the 2022 Conference of the North American Chapter of the Association for
Computational Linguistics: Human Language Technologies, 2022.
Mauricio Sadinle, Jing Lei, and Larry Wasserman. Least ambiguous set-valued classifiers with bounded error levels.
Journal of the American Statistical Association, 2019.
Yusuf Sale, Michele Caprio, and Eyke H ¨ollermeier. Is the volume of a credal set a good measure for epistemic
uncertainty? In Uncertainty in Artificial Intelligence. PMLR, 2023.
Mike Schaekermann, Edith Law, Alex C Williams, and William Callaghan. Resolvable vs. irresolvable ambiguity:
A new hybrid framework for dealing with uncertain ground truth. In 1st Workshop on Human-Centered Machine
Learning at SIGCHI, volume 2016, 2016.
Murat Sensoy, Lance Kaplan, and Melih Kandemir. Evidential deep learning to quantify classification uncertainty.
Advances in neural information processing systems, 31, 2018.
Matteo Sesia and Yaniv Romano. Conformal prediction using conditional histograms. Advances in Neural Information
Processing Systems, 34, 2021.
Mohammad Hossein Shaker and Eyke H ¨ullermeier. Aleatoric and epistemic uncertainty with random forests. In
International Symposium on Intelligent Data Analysis. Springer, 2020.
Rion Snow, Brendan O’connor, Dan Jurafsky, and Andrew Y Ng. Cheap and fast–but is it good? evaluating non-expert
annotations for natural language tasks. In Proceedings of the 2008 conference on empirical methods in natural
language processing, 2008.
Alexander Sorokin and David Forsyth. Utility data annotation with amazon mechanical turk. In 2008 IEEE computer
society conference on computer vision and pattern recognition workshops. IEEE, 2008.
Lukas Steinberger and Hannes Leeb. Leave-one-out prediction intervals in linear regression models with many variables.
arXiv preprint arXiv:1602.05801, 2016.
David Stutz, Krishnamurthy Dj Dvijotham, Ali Taylan Cemgil, and Arnaud Doucet. Learning optimal conformal
classifiers. In International Conference on Learning Representations, 2021.
David Stutz, Ali Taylan Cemgil, Abhijit Guha Roy, Tatiana Matejovicova, Melih Barsbey, Patricia Strachan, Mike
Schaekermann, Jan Freyberg, Rajeev Rikhye, Beverly Freeman, et al. Evaluating ai systems under uncertain ground
truth: a case study in dermatology. arXiv preprint arXiv:2307.02191, 2023a.
David Stutz, Abhijit Guha Roy, Tatiana Matejovicova, Patricia Strachan, Ali Taylan Cemgil, and Arnaud Doucet.
Conformal prediction under ambiguous ground truth. Transactions on Machine Learning Research, 2023b.
11
PDF PAGE 12
 Conformalized Credal Set Predictors A PREPRINT
Alexandra Uma, Dina Almanea, and Massimo Poesio. Scaling and disagreements: Bias, noise, and ambiguity. Frontiers
in Artificial Intelligence, 2022.
Alexandra N Uma, Tommaso Fornaciari, Dirk Hovy, Silviu Paun, Barbara Plank, and Massimo Poesio. Learning from
disagreement: A survey. Journal of Artificial Intelligence Research, 72, 2021.
Vladimir V ovk. Cross-conformal predictors.Annals of Mathematics and Artificial Intelligence, 74, 2015.
Vladimir V ovk, Ilia Nouretdinov, Valentina Fedorova, Ivan Petej, and Alex Gammerman. Criteria of efficiency for
set-valued classification. Annals of Mathematics and Artificial Intelligence, 81, 2017.
Vladimir V ovk, Alexander Gammerman, and Glenn Shafer.Algorithmic Learning in a Random World. Springer Nature,
2022.
Peter Walley. Statistical reasoning with imprecise probabilities, volume 42. Springer, 1991.
Peter Walley. Inferences from multinomial data: learning about a bag of marbles. Journal of the Royal Statistical
Society Series B: Statistical Methodology, 1996.
Adina Williams, Nikita Nangia, and Samuel Bowman. A broad-coverage challenge corpus for sentence understanding
through inference. In Proceedings of the 2018 Conference of the North American Chapter of the Association for
Computational Linguistics: Human Language Technologies, Volume 1 (Long Papers). Association for Computational
Linguistics, 2018.
Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chaumond, Clement Delangue, Anthony Moi, Pierric Cistac, Tim
Rault, R´emi Louf, Morgan Funtowicz, et al. Huggingface’s transformers: State-of-the-art natural language processing.
arXiv preprint arXiv:1910.03771, 2019.
Marco Zaffalon. The naive credal classifier. Journal of statistical planning and inference, 2002.
12

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking page 13 amounts**</reasoning></content>
  <tool_call id="call_2d26ce55831f4696ac0aad3f41d2f046" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2402.10723.pdf\"); print(\"PDF PAGE 13\\n\",r.pages[12].extract_text()); print(\"PDF PAGE 14\\n\",r.pages[13].extract_text())'", "timeout": 30}</tool_call>
</message>
<message type="tool">PDF PAGE 13
 Conformalized Credal Set Predictors A PREPRINT
Appendix A. Proof of Theorem 4.2
Proof. Let A denote the event f (xnew, λxnew) &lt; q+ ϵ and ˜A the event f (xnew, ˜λxnew) &lt; q. We have
P (A) ≥ P (A ∧ ˜A)
= P ( ˜A) · P (A | ˜A)
= P ( ˜A) · (1 − P (¬A | ˜A))
Since ¬A means that f (xnew, λxnew) ≥ q + ϵ, the conditional event ¬A | B implies a violation of the closeness
condition in (11), wherefore the probability P (¬A | B) is upper-bounded by δ according to (11). Therefore, noting that
P ( ˜A) ≥ 1 − ˜α is the standard guarantee by CP,
P (A) ≥ P ( ˜A) · (1 − P (¬A | ˜A))
≥ (1 − ˜α) · (1 − δ)
= 1 − α .
Appendix B. More Results for the Synthetic Data
Figure 6 depicts the overall coverage and quantile comparison between four different nonconformity functions TV,
KL, WS, and Inner. In Figure 7, we illustrate the evolution of the credal sets as m changes from 1 to 100 for different
nonconformity functions when K = 3. For this case, the full comparison of efficiency and coverage across various
nonconformity functions is provided in Figure 8.
13
PDF PAGE 14
 Conformalized Credal Set Predictors A PREPRINT
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH
(a) TV
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH





$YHUDJH4XDQWLOH
(b) KL
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH





$YHUDJH4XDQWLOH
(c) WS
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH
(d) Inner
Figure 6: Coverage and quantile results for synthetic data, where the ground truth distributions are approximated by
observing m samples from them. The horizontal dashed lines indicate the nominal coverage levels 1 − α = 0.9.
14

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Verifying PDF title metadata**</reasoning></content>
  <tool_call id="call_4461781cf47441a89d030892984c3841" name="execute">{"command": "python -c 'from pypdf import PdfReader; ids=[\"2107.07511\",\"1904.06019\",\"2402.10723\"]; exec(\"for id in ids:\\n r=PdfReader(\\\"/work/literature/\\\"+id+\\\".pdf\\\"); print(\\\"\\\\n====\\\",id,\\\"PAGE 1 ====\\\\n\\\",r.pages[0].extract_text())\")'", "timeout": 60}</tool_call>
</message>
<message type="tool">
==== 2107.07511 PAGE 1 ====
 A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantiﬁcation
Anastasios N. Angelopoulos and Stephen Bates
December 8, 2022
Abstract
Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-
tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-
tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty
sets/intervals for the predictions of such models. Critically, the sets are valid in a distribution-free sense:
they possess explicit, non-asymptotic guarantees even without distributional assumptions or model as-
sumptions. One can use conformal prediction with any pre-trained model, such as a neural network, to
produce sets that are guaranteed to contain the ground truth with a user-speciﬁed probability, such as
90%. It is easy-to-understand, easy-to-use, and general, applying naturally to problems arising in the
ﬁelds of computer vision, natural language processing, deep reinforcement learning, and so on.
This hands-on introduction is aimed to provide the reader a working understanding of conformal
prediction and related distribution-free uncertainty quantiﬁcation techniques with one self-contained
document. We lead the reader through practical theory for and examples of conformal prediction and
describe its extensions to complex machine learning tasks involving structured outputs, distribution
shift, time-series, outliers, models that abstain, and more. Throughout, there are many explanatory
illustrations, examples, and code samples in Python. With each code sample comes a Jupyter notebook
implementing the method on a real-data example; the notebooks can be accessed and easily run by
clicking on the following icons:
 .
1
arXiv:2107.07511v6  [cs.LG]  7 Dec 2022

==== 1904.06019 PAGE 1 ====
 Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the training and test data are not drawn from the same distribution.
We begin by reviewing the basics of conformal prediction, in this section. In Section 2, we describe an extension of
conformal prediction to the setting of covariate shift, and give supporting empirical results. In Section 3, we cover the
mathematical details behind our conformal extension. We conclude in Section 4, and discuss several other possible
applications of our new conformal methodology.
1.1 Quantile lemma
Before explaining the basic ideas behind conformal inference (i.e., conformal prediction, we will use these two terms
interchangeably), we introduce some notation. We denote by Quantile(β;F ) the levelβ quantile of a distributionF ,
i.e., forZ∼F ,
Quantile(β;F ) = inf
{
z : P{Z≤z}≥ β
}
.
In our use of quantiles, we will allow for distributionsF on the augmented real line, R∪{∞} . For valuesv1,...,v n,
we writev1:n ={v1,...,v n} to denote their multiset. Note that this is unordered, and allows for multiple instances the
same element; thus in the present case, ifvi =vj fori⁄=j, then this value appears twice inv1:n. To denote quantiles
of the empirical distribution of the valuesv1,...,v n, we abbreviate
Quantile(β;v1:n) = Quantile
(
β; 1n
n∑
i=1
δvi
)
,
1
arXiv:1904.06019v3  [stat.ME]  6 Jul 2020

==== 2402.10723 PAGE 1 ====
 CONFORMALIZED CREDAL SET PREDICTORS
A PREPRINT
Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2
1Institute of Informatics, LMU Munich, Germany
2Munich Center for Machine Learning (MCML), Germany
3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany
alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de
ABSTRACT
Credal sets are sets of probability distributions that are considered as candidates for an imprecisely
known ground-truth distribution. In machine learning, they have recently attracted attention as an
appealing formalism for uncertainty representation, in particular due to their ability to represent
both the aleatoric and epistemic uncertainty in a prediction. However, the design of methods for
learning credal set predictors remains a challenging problem. In this paper, we make use of conformal
prediction for this purpose. More specifically, we propose a method for predicting credal sets in the
classification task, given training data labeled by probability distributions. Since our method inherits
the coverage guarantees of conformal prediction, our conformal credal sets are guaranteed to be
valid with high probability (without any assumptions on model or distribution). We demonstrate the
applicability of our method to natural language inference, a highly ambiguous natural language task
where it is common to obtain multiple annotations per example.
Keywords Conformal Prediction · Uncertainty Representation · Credal Sets
1 Introduction
Representing and quantifying uncertainty is becoming increasingly important in machine learning (ML), particularly
as ML models are employed in safety-critical application domains such as medicine or autonomous driving. In such
domains, a distinction between so-called aleatoric uncertainty and epistemic uncertainty is often useful [Hora, 1996].
Broadly speaking, aleatoric uncertainty is due to the inherent randomness of the data-generating process, whereas
epistemic uncertainty stems from the learner’s lack of knowledge about the best predictive model. Thus, while the
former is irreducible, the latter can in principle be reduced through additional information, e.g., by gathering additional
data to learn from.
Representation of aleatoric and epistemic uncertainty requires formalism more expressive than standard probability
distributions [H¨ullermeier and Waegeman, 2021]. One such formalism which prevails in the recent ML literature is
second-order probability distributions. Essentially, in a classification setting, these are distributions over distributions
over classes. Models producing second-order distributions as predictions can be learned in a classical Bayesian way
[Kendall and Gal, 2017, Depeweg et al., 2018] or using more recent approaches such as evidential deep learning [Sensoy
et al., 2018]. Yet, approaches of that kind are not unproblematic and have been subject to criticism [Bengs et al., 2022,
2023]. Another formalism suitable for representing both types of uncertainty is the concept of a credal set, which is
well-established in the field of imprecise probability theory [Walley, 1991] and meanwhile also attracted attention in ML
[Shaker and H¨ullermeier, 2020, H¨ullermeier et al., 2022]. Credal sets are (convex) sets of probability distributions that
can be considered as candidates for an imprecisely known ground-truth distribution. Figure 1 shows examples of credal
sets in a three-class scenario, where the space of distributions can be visualized by the two-dimensional probability
simplex. Broadly speaking, the larger the credal set, the higher the epistemic uncertainty, and the more “in the middle”
the set is located, i.e., the closer it is to the uniform distribution, the higher the aleatoric uncertainty.
arXiv:2402.10723v1  [stat.ML]  16 Feb 2024

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Locating page 1 details**</reasoning></content>
  <tool_call id="call_217aac5442c64f719c0a971aad931c07" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2009.14193.pdf\"); print(r.pages[0].extract_text()); print(\"==== CREDAL PAGES 4-8 ====\"); r=PdfReader(\"/work/literature/2402.10723.pdf\"); [print(\"=== PDF PAGE\",p,\"===\\n\",r.pages[p-1].extract_text()) for p in [4,5,6,7,8]]'", "timeout": 90}</tool_call>
</message>
<message type="tool">UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in computer vision.
Formally, for a discrete responseY ∈Y ={1,...,K } and a feature vectorX∈ Rd, we desire an
uncertainty set function,C(X), mapping a feature vector to a subset of{1,...,K } such that
P (Y ∈C (X))≥ 1−α, (1)
for a pre-speciﬁed conﬁdence levelα such as 10%. Conformal predictors like our method can mod-
ify any black-box classiﬁer to output predictive sets that are rigorously guaranteed to satisfy the
∗equal contribution
†Project website here.
1
arXiv:2009.14193v5  [cs.CV]  3 Sep 2022
==== CREDAL PAGES 4-8 ====
=== PDF PAGE 4 ===
 Conformalized Credal Set Predictors A PREPRINT
Instead of assuming λx to be known, suppose now that only a prediction ˆλx of this distribution is available. Epistemic
uncertainty refers to the uncertainty about how well the latter approximates the former, and hence to the additional
uncertainty in the prediction of outcome Y that is caused by the discrepancy between ˆλx and the ground-truth λx. We
seek to capture this discrepancy by means of credal sets
Q ∈ QK ⊂ ∆K ,
with the idea that Q ∋ λx holds with high probability. Typically, credal sets are assumed to be convex, and further
restrictions might be imposed on QK for practical and computational reasons, for example, a restriction to convex
polygons (with a finite number of extreme points).
3.2 Conformal Prediction
Conformal prediction provides a general framework for producing set-valued predictions with a certain guarantee of
validity. In a supervised setting, consider data points of the form Z = (X, U) ∈ X × U, and the task is to predict U
given X = x. We assume the space Z to be equipped with a nonconformity measure f : Z − →R that quantifies the
“strangeness” of z, i.e., the higher f (z), the less normal or expected the data point. Let Dcalib ⊂ Zbe a (randomly
generated) set of data points, called calibration data, and Z another data point that remains unobserved. Under
the assumption of exchangeability, i.e., that the calibration data and the query point Z have been generated by an
exchangeable process, we want to construct a so-called confidence set C ⊆ Uthat guarantees coverage:
P(U ∈ C) ≥ 1 − α. (1)
By a simple combinatorial argument [V ovk et al., 2022], the confidence setC can be constructed as
C(x) :=

u ∈ U |f (x, u) &lt; q(E, α′) 	 , (2)
where α′ = |E| −1⌈(1 + |E|)(1 − α)⌉, and q(E; α′) denotes the α′-quantile of E.
Importantly, the guarantee (2) holds regardless of the nonconformity function f (·), which, however, has an influence
on the efficiency of the prediction: The more appropriate the function, the smaller the prediction set C tends to be.
Normally, f (·) is not predefined but constructed in a data-driven way using training data Dtrain. For example, a common
approach is to train a predictor π : X − → Uand then define f (x, u) in terms of d(u, π(x)), where d(·, ·) is an
appropriate distance function on U. Replacing the point-prediction π(x) ∈ Uby the prediction set C(x) ⊂ Ucan then
be seen as “conformalizing” the predictor π: Using the calibration data, CP estimates a high-probability upper bound
on the distance between point-predictions and actual outcomes, and corrects the former correspondingly.
4 Conformal Credal Set Prediction
Recall the setting and notation from Section 3.1. Our goal is to learn a credal set predictor h : X − → QK, that is, a
model that makes predictions in the form of credal sets, thereby representing both aleatoric and epistemic uncertainty.
To this end, we assume probabilistic training data of the form
D =
 
x1, λx1 , . . . , xN , λxN 	 ⊂ X ×∆K . (3)
The model h should be able to predict the (probabilistic) outcomes for new query instances in a reliable way. More
specifically, suppose that xnew is a new query instance (following the same distribution as the training data) for which a
prediction is sought. The credal prediction Q = h(xnew) should then be valid in the sense that Q ∋ λxnew with high
probability. At the same time, the prediction should be informative in the sense that the (epistemic) uncertainty reflected
by Q is as small as possible. Again, various measures for quantifying the latter can be found in the literature [Klir and
Wierman, 1999, Sale et al., 2023].
We aim to construct the credal set predictor h by means of (inductive) conformal prediction. Following the confor-
malization recipe outlined in Section 3.2, we partition D into Dtrain and Dcalib, using the former for model training and
the latter for calibration. Regarding the training step, we explore two learning strategies, connected with two ways of
defining a nonconformity function, which is pivotal in the calibration step.
The first approach is based on training a standard ( first-order) probability predictor, i.e., a probabilistic classifier
g : X − →∆K that maps instances to the (first-order) probability distribution on Y. This can be achieved, for example,
by minimizing the cross-entropy loss between the ground truth and the predicted distributions, i.e.,
g = argmin
¯g∈H
X
(xi,λxi )∈Dtrain
−
KX
k=1
λxik log(¯g(xi)k),
4
=== PDF PAGE 5 ===
 Conformalized Credal Set Predictors A PREPRINT
Algorithm 1 Conformal Credal Set Prediction
Input:
Data D; error rate α; query instance xnew.
Process:
Partition D into Dtrain and Dcalib.
Train a first-order (i = 1) or a second-order (i = 2) predictor using Dtrain.
Choose a nonconformity function fi as in (4) or (6) that suits the trained predictor to obtain the set of scores
Ei.
Set α′ = |Ei|−1⌈(1 + |Ei|)(1 − α)⌉.
Output:
hi(xnew) =

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 .
where H is a hypothesis space. Given a predictor g(·) of this kind, nonconformity is naturally defined in terms of
distance:
f1(x, λx) := d(λx, g(x)) , (4)
where d(·, ·) is a suitable distance function on ∆K, such as total variation, Wasserstein distance, etc.
An alternative approach is motivated by recent work on (epistemic) uncertainty representation via second-order
probability distributions. A second-order learner G : X − →P(∆K) maps each input x to a distribution over ∆K.
Given the training data, meaningful learning in this context can be accomplished, for instance, by parameterizing the
second-order distributions using Dirichlet distributions. Specifically, one can assume that each x is associated with a
Dirichlet distribution characterized by the parameter vector θx ∈ RK+ with the probability density function
P (λ | θx) = 1B(θx)
KY
k=1
λθxk −1k , (5)
where B(·) is the multivariate beta function. This way, λx can be thought of as a sample from that distribution,
i.e., λx ∼ Dir(θx). Our model then essentially yields a prediction ˆθx of the true parameter θx for every x, and its
optimization involves minimizing the negative log-likelihood loss
X
(xi,λxi )∈Dtrain

log(B(ˆθxi )) − KX
k=1
(ˆθxik − 1) log(λxik )

.
Given a second-order predictor ˆθx, nonconformity can be defined as a decreasing function of likelihood, e.g., as 1
minus relative likelihood:
f2(x, λx) = 1 − P (λx | ˆθx)maxλ∈∆K P (λ | ˆθx) . (6)
Using the nonconformity function fi(·) (i ∈ {1, 2}), we obtain the set of nonconformity scores by
Ei :=
n
fi(xj, λxj ) | (xj, λxj ) ∈ Dcalib
o
. (7)
Accordingly, the credal set can be defined as
hi(xnew) :=

λ ∈ ∆K | fi(xnew, λ) &lt; q(Ei, α′) 	 . (8)
Algorithm 1 outlines a summary of the proposed methods. In the following theorem, we state the validity of the
predicted set, that is, the restatement of the conformal coverage guarantee [V ovk et al., 2022] adjusted to our setting.
Theorem 4.1. Let P denote the joint probability distribution on (X, Λ) ∈ X ×∆K. If data points in Dcalib and
(xnew, λxnew) are drawn i.i.d. (exchangeably) from P, then the conformal credal sets in (8) are valid, i.e.,
P
 
λxnew ∈ hi(xnew) ≥ 1 − α , for i ∈ {1, 2}.
5
=== PDF PAGE 6 ===
 Conformalized Credal Set Predictors A PREPRINT
4.1 Noisy Observations
So far, we (implicitly) assumed that ground-truth probability distributions λxi will be provided as training (and
calibration) data. Needless to say, this assumption will rarely hold true in practice. Instead, observations will rather be
noisy versions ˜λxi of the true probabilities, i.e., the data will be of the form
D =
n 
x1, ˜λx1 , . . . , xN , ˜λxN o ⊂ X ×∆K . (9)
Notably, such datasets emerge in scenarios where each data instance x is annotated by multiple human experts, which
recently have attracted a lot of attention in the context of machine learning and also conformal prediction [Stutz
et al., 2023b, Javanmardi et al., 2023]. In this context, ˜λx denotes the distribution derived from aggregating annotator
disagreements concerning the label of instance x. Of course, conformal prediction can still be applied to noisy data of
that kind, but the coverage guarantee will then only hold for the noisy labeling:
P

˜λxnew ∈ h(xnew) ≥ 1 − ˜α. (10)
Practically, one may expect that the guarantees will hold for the ground-truth as well, simply because calibration on
noisy instead of clean data will tend to make prediction regions larger and hence more conservative. Moreover, since
nonconformity is derived from a predictive model g(·) that seeks to recover ground-truth probabilities, the latter should
conform at least as well as noisy distributions. Of course, this intuition is not a formal guarantee. In order to provide
such a guarantee for the ground-truth probabilities, one obviously needs to make some assumptions. Concretely, let us
make the following bounded noise assumption for the labeling process: The labeling noise is (stochastically) bounded
in the sense that, given the nonconformity function f and a (small) probability δ &gt;0, there exists a tolerance ϵ &gt;0
such that
P

|f (x, λx) − f (x, ˜λx)| &lt; ϵ ≥ 1 − δ (11)
all x ∈ X.
Theorem 4.2. Let α &gt;0 be any miscoverage rate, and suppose the bounded noise assumption holds. Let q = q(E, ˜α)
be the critical threshold on the noisy calibration data Dcalib for miscoverage rate
˜α = α − δ1 − δ .
Then, for any new query xnew ∈ X,
P
 
f (xnew, λxnew) &lt; q+ ϵ ≥ 1 − α .
The proof is deferred to Appendix A.. As a consequence of this result, a conformal predictor learned on the noisy data
with modified miscoverage rate ˜α can be turned into a valid predictor (with miscoverage rate α) for the ground-truth
data by increasing the learned rejection threshold by ϵ, provided the bounded noise property (11) can be ascertained.
Thus, if we denote the corresponding credal set predictor by hϵ, we can guarantee that
P
 
λxnew ∈ hϵ(xnew) ≥ 1 − α . (12)
5 Experiments
In this section, we evaluate the performance of our proposed methods using both synthetic and real datasets. In vanilla
conformal prediction, the performance of a method is usually assessed based on the average prediction set size, aka
efficiency, and the average coverage on the test set. It is more appealing to have the promised coverage with smaller
sets. In our scenario, the analytical calculation of credal sets is not feasible. Therefore, for the sake of illustration as
well as other analyses, such as efficiency calculation, we resort to approximations. We discretize the simplex with a
resolution of 0.005, yielding M = 19969 distributions. This enables the straightforward construction of credal sets, as
defined in (8). The efficiency is gauged by considering the fraction of all M distributions that lie within the predicted
credal sets. All implementations and experiments can be found in the technical supplement of this work.1
5.1 Learning Model
In our experiments, we employ a deep neural network as the learner. Specifically, the model consists of three hidden
layers with 256, 64, and 16 units, utilizing ReLU as the activation function. Prior to the output layer, a dropout
1The link to the code: https://github.com/alireza-javanmardi/conformal-credal-sets
6
=== PDF PAGE 7 ===
 Conformalized Credal Set Predictors A PREPRINT
Table 1: Summary of the nonconformity functions used in experiments.
Name Formulation Predictor
TV 12 PKk=1 |λxk − g(x)k| first-order
WS - first-order
KL PKk=1 λxk log( λxkg(x)k ) first-order
Inner 1 − PKk=1 λxk g(x)k first-order
SO as in (6) second-order
layer with a rate of 0.3 is incorporated. The same model architecture serves both first- and second-order predictors,
differing only in the activation functions of the output layers. For the first-order predictor, softmax is used, while for
the second-order predictor, ReLU is employed. Learning is facilitated using the Adam optimizer with a learning rate
of 10−4, utilizing cross-entropy as the loss function for the first-order predictor and negative log-likelihood for the
second-order predictor.
5.2 Nonconformity Functions
CP should work regardless of the choice of nonconformity score function, while this choice can affect the efficiency
and geometry of the prediction set. For the sake of comparison, we examine different nonconformity functions in our
experiments. When utilizing a first-order predictor, besides total variation (TV) and the First Wasserstein (WS) distance,
we also investigate the Kullback–Leibler (KL) divergence and 1 minus the inner product (Inner) as nonconformity
functions. For the second-order predictor, we consider 1 minus the relative likelihood (SO) as defined in (6). Table 1
offers a summary of all five nonconformity functions employed in our experiments.
5.3 Real Data
We focus on the ChaosNLI dataset [Nie et al., 2020], an English Natural Language Inference (NLI) dataset that captures
the inherent variability in human judgments of textual entailment. Here, the classes are entailment, neutral, and
contradiction for each premise-hypothesis pair. Instances in this dataset are selected from the development sets of SNLI
[Bowman et al., 2015], MNLI [Williams et al., 2018], and AbductiveNLI [Bhagavatula et al., 2019], for which the
majority vote was less than three among the five human annotators. These instances were then given to100 independent
humans for annotation, given strict annotation guidelines.
We combine the chaos-SNLI and chaos-MNLI subsets, resulting in a dataset of 3113 datapoints. For model training,
we leverage a language model from the Hugging Face transformers library [Wolf et al., 2019], initially trained on
SNLI and MultiNLI datasets for classification tasks2. We utilize the last hidden layer output of this model to embed the
premise-hypothesis pairs from our 3113 instances, serving as inputs for our deep neural network. To split the data, we
randomly select 500 instances for calibration, 500 for testing, and the remaining for training. This process is repeated
ten times with different random seeds. In Figure 3, we compare the resulting credal sets of different nonconformity
functions for three specific instances. Figure 4 summarizes the overall performance of the proposed methods on this
data under different miscoverage rates (α). Notably, the mean of the average coverage over the test data across various
random seeds aligns with or exceeds the nominal value, consistent with the conformal prediction guarantee.
5.4 Synthetic Data
The primary objective of conducting experiments with synthetic data is to illustrate the impact of noisy observations,
particularly to showcase the behavior of the proposed credal sets when we only have access to an approximation of the
ground truth distributions. Our experiment revolves around a K-class classification task with K ∈ {3, 4, 6, 8, 10}. For
each K, we consider 10-dimensional features X ∈ R10, where each X1, . . . , X10 are independent standard normal
random variables. Subsequently, we generate a random matrix β ∈ R10×K, with its elements drawn independently
from the standard normal distribution. To define the ground truth probability over the classes for object X, we use the
following formulation:
λxk := P(Y = k|x) = Zj(x)P
j Zj(x) ,
2The model can be found at https://huggingface.co/cross-encoder/nli-deberta-base
7
=== PDF PAGE 8 ===
 Conformalized Credal Set Predictors A PREPRINT
Premise-Hypothesis pair TV KL WS Inner SO
Premise: A man in a bar drinks from
a pitcher while a man in a green hat
looks on and a woman in a black
shirt drink from a glass.
Hypothesis: The women is drinking
water.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.24 0 .18 0 .28 0 .36 0 .06
Premise: The streets are busy and
people contemplate their futures.
Hypothesis: People are screaming
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.33 0 .20 0 .33 0 .41 0 .47
Premise: A photographer snaps a
midair action shot of a snowboarder.
Hypothesis: The midair shot snaps
at a boarder of snow.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.31 0 .27 0 .26 0 .34 0 .08
Figure 3: Various credal sets obtained for three instances from ChaosNLI dataset [Nie et al., 2020]. The ground
truth distributions are denoted by orange squares. Black circles indicate model predictions in cases employing a
first-order learner (first four columns). For the last column, utilizing a second-order learner, the predicted second-order
distributions are represented through contour plots. The miscoverage rate is α = 0.2, and the efficiency of each credal
set is written below it.
79 ./ :6 ,QQHU 62
              
0 LVFRYHUDJHUDWH 





$YHUDJH&amp;RYHUDJH






$YHUDJH(IILFLHQF\$YHUDJH&amp;RYHUDJH
$YHUDJH(IILFLHQF\
Figure 4: Coverage and efficiency results of different nonconformity functions applied on the ChaosNLI dataset [Nie
et al., 2020]. The horizontal dashed lines indicate the nominal coverage levels.
where Z(x) := exp(x⊤β). Employing this data-generating process, we generate N = 1500 samples to construct the
dataset DK = {(xi, λxi )}Ni=1.
To obtain noisy versions of DK, we employ a sampling approach. Specifically, we independently sample each
distribution λxi m times and utilize relative frequencies to create its noisy counterpart ˜λxim . We represent the resulting
dataset as DKm = {(xi, ˜λxim )}Ni=1. We repeat this process four times with m ∈ {1, 5, 10, 100}.
Given each dataset DKm, we randomly partition data points equally into training, calibration, and test sets and perform
the proposed methodologies accordingly. Again, we repeat this process ten times with different random seeds for each
dataset DKm. Due to the computational complexity in calculating efficiency for cases with K &gt;3, we utilize the quantile
of the calibration nonconformity scores as an efficiency metric. In Figure 5, we represent the overall result for TV
under different K and m values. It can be observed that the coverage is fulfilled across almost all scenarios, including
m = 1 with degenerate distributions. This observed behavior is somewhat intuitive. The model endeavors to learn the
underlying probabilistic relationship between X and Y , even given the noisy data 3. Consequently, during calibration
3Of course, this holds under some reasonable assumptions on noise.
8

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking page 9 conclusion**</reasoning></content>
  <tool_call id="call_0051fea3e37c421aad72718bde840599" name="execute">{"command": "python -c 'from pypdf import PdfReader; specs={\"2402.10723\":[9],\"2009.14193\":[2,3,4,6,7,8,9,17],\"1904.06019\":[3,4,5,6,8]}; exec(\"for id,pages in specs.items():\\n r=PdfReader(\\\"/work/literature/\\\"+id+\\\".pdf\\\")\\n for p in pages:\\n  txt=r.pages[p-1].extract_text(); print(\\\"\\\\n===\\\",id,\\\"PDF PAGE\\\",p,\\\"===\\\\n\\\",\\\"\\\\n\\\".join(l for l in txt.splitlines() if any(c.isalpha() for c in l) or len(l)&gt;25))\")'", "timeout": 90}</tool_call>
</message>
<message type="tool">
=== 2402.10723 PDF PAGE 9 ===
 Conformalized Credal Set Predictors A PREPRINT
.  .  .  .  . 
                   
P
QXPEHURIVDPSOHV
$YHUDJH&amp;RYHUDJH
$YHUDJH4XDQWLOH$YHUDJH&amp;RYHUDJH
$YHUDJH4XDQWLOH
Figure 5: Coverage and quantile results for synthetic data, where the ground truth distributions are approximated by
observing m samples from them. The horizontal dashed line indicates the nominal coverage levels 1 − α = 0.9.
with noisy instances, the nonconformity scores of noise-free instances are mostly upper-bounded by the scores of their
noisy counterparts, resulting in more conservative sets that effectively cover the ground-truth distributions. It can also
be seen that the quantile of the nonconformity scores shrinks as m increases. Results for other nonconformity functions,
along with some visualizations for the specific case of K = 3, can be found in Appendix B..
6 Limitations
The methods we proposed are promising but still subject to certain limitations. One challenge, for example, lies in the
representation of credal sets as subsets of the probability simplex. For the nonconformity functions we used in this
work, there are no closed-form equations for the resulting credal sets. Instead, the sets are only represented implicitly
(through the nonconformity threshold). Numerical approximation is feasible but essentially limited to scenarios with a
small number of classes.
The issue of representation is also connected to the computation of uncertainty measures, i.e., numerical measures
quantifying the total, aleatoric, and epistemic uncertainty associated with a credal set [Klir and Wierman, 1999].
Computation of these measures involves the computation of specific characteristics of the set, such as its distance from
the center of the simplex or its volume [Sale et al., 2023].
Our generalization to the case of noisy training data, i.e., labelings˜λ that only approximate the ground-truth probabilities
λ, provides guarantees under the bounded noise assumption. While this assumption is plausible, and in a sense always
achievable with a sufficiently large ϵ, its practical use requires a meaningful choice of ϵ and δ, which leads to inference
that is both valid and efficient. This will be difficult in cases of limited knowledge about the labeling noise. If labels are
constructed from relative frequencies (like in the case of multiple annotators), classical statistical methods might be
applicable. In general, however, an appropriate choice of ϵ and δ for practical problems is still an open problem.
7 Conclusion and Future Work
Conformal credal set prediction connects machine learning with imprecise probability theory and offers a novel data-
driven approach to constructing predictions that effectively capture both aleatoric and epistemic uncertainty. Thereby, it
provides the basis of a new approach to reliable, uncertainty-aware machine learning. Leveraging the inherent validity
of the conformal prediction framework, our conformalized credal sets are assured to cover the ground truth distributions
with high probability. We have explored different nonconformity functions within this novel setting and evaluated their
performance through numerical experiments.
A natural next step is to explore alternative approaches for defining nonconformity functions, with the goal of devising
formulations amenable to closed-form solutions for credal sets. Besides, the nonconformity has a strong influence on
the efficiency and hence the uncertainty of credal set predictions. Obviously, there is a preference for nonconformity
functions leading to higher efficiency and lower uncertainty.
Another interesting direction is to extend the learning of credal set predictors to standard (zero-order) training data.
As already mentioned, learning a second-order predictor from data of that kind turns out to be difficult in the case of
second-order probability distributions. Broadly speaking, this is due to the inherent ambiguity of the missing first-order
information, which cannot be resolved due to certain averaging effects [Bengs et al., 2022, 2023]. For the case of credal
predictors, the situation is still less clear.

=== 2009.14193 PDF PAGE 2 ===
 Figure 1: Prediction set examples on Imagenet. We show three examples of the class fox squirrel and
the 95% prediction sets generated by RAPS to illustrate how the size of the set changes as a function of the
difﬁculty of a test-time image.
desired coverage property shown in Eq. (1). For evaluations, we focus on Imagenet classiﬁcation
using convolutional neural networks (CNNs) as the base classiﬁers, since this is a particularly chal-
lenging testbed. In this setting,X would be the image andY would be the class label. Note that the
guarantee in Eq. (1) is marginal overX andY —it holds on average, not for a particular imageX.
A ﬁrst approach toward this goal might be to assemble the set by including classes from highest to
lowest probability (e.g., after Platt scaling and a softmax function; see Platt et al., 1999; Guo et al.,
2017) until their sum just exceeds the threshold 1−α. We call this strategy naive and formulate
it precisely in Algorithm 1. There are two problems with naive: ﬁrst, the probabilities output by
CNNs are known to be incorrect (Nixon et al., 2019), so the sets from naive do not achieve cov-
erage. Second, image classiﬁcation models’ tail probabilities are often badly miscalibrated, leading
to large sets that do not faithfully articulate the uncertainty of the model; see Section 2.3. Moreover,
smaller sets that achieve the same coverage level can be generated with other methods.
The coverage problem can be solved by picking a new threshold using holdout samples. For exam-
ple, withα =10%, if choosing sets that contain 93% estimated probability achieves 90% coverage
on the holdout set, we use the 93% cutoff instead. We refer to this algorithm, introduced in Ro-
mano et al. (2020), as Adaptive Prediction Sets (APS). The APS procedure provides coverage but
still produces large sets. To ﬁx this, we introduce a regularization technique that tempers the in-
ﬂuence of these noisy estimates, leading to smaller, more stable sets. We describe our proposed
algorithm, Regularized Adaptive Prediction Sets (RAPS), in Algorithms 2 and 3 (with APS as a
special case). As we will see in Section 2, both APS and RAPS are always guaranteed to satisfy
Eq. (1)—regardless of model and dataset. Furthermore, we show that RAPS is guaranteed to have
better performance than choosing a ﬁxed-size set. Both methods impose negligible computational
requirements in both training and evaluation, and output useful estimates of the model’s uncertainty
on a new image given, say, 1000 held-out examples.
In Section 3 we conduct the most extensive evaluation of conformal prediction in deep learning to
date on Imagenet and Imagenet-V2. We ﬁnd that RAPS sets always have smaller average size than
naive and APSsets. For example, using a ResNeXt-101, naive does not achieve coverage, while
APS and RAPS achieve it almost exactly. However,APS sets have an average size of 19, whileRAPS
sets have an average size of 2 atα = 10% (Figure 2 and Table 1). We will provide an accompanying
codebase that implements our method as a wrapper for any PyTorch classiﬁer, along with code to
exactly reproduce all of our experiments.
1.1 R ELATED WORK
Reliably estimating predictive uncertainty for neural networks is an unsolved problem. Historically,
the standard approach has been to train a Bayesian neural network to learn a distribution over net-
work weights (Quinonero-Candela et al., 2005; MacKay, 1992; Neal, 2012; Kuleshov et al., 2018;
Gal, 2016). This approach requires computational and algorithmic modiﬁcations; other approaches
avoid these via ensembles (Lakshminarayanan et al., 2017; Jiang et al., 2018) or approximations of
Bayesian inference (Riquelme et al., 2018; Sensoy et al., 2018). These methods also have major
practical limitations; for example, ensembling requires training many copies of a neural network ad-
versarially. Therefore, the most widely used strategy is ad-hoctraditional calibration of the softmax
scores with Platt scaling (Platt et al., 1999; Guo et al., 2017; Nixon et al., 2019).

=== 2009.14193 PDF PAGE 3 ===
 desired coverage (1- )
1.00empirical coverage
Naive
APS
RAPS
desired coverage (1- )
100average size
Figure 2: Coverage and average set size on Imagenet for prediction sets from three methods.All methods
use a ResNet-152 as the base classiﬁer, and results are reported for 100 random splits of Imagenet-Val, each of
size 20K. See Section 3.1 for full details.
This work develops a method for uncertainty quantiﬁcation based onconformal prediction. Originat-
ing in the online learning literature, conformal prediction is an approach for generating predictive
sets that satisfy the coverage property in Eq. (1) (V ovk et al., 1999; 2005). We use a convenient
data-splitting version known as split conformal prediction that enables conformal prediction meth-
ods to be deployed for essentially any predictor (Papadopoulos et al., 2002; Lei et al., 2018). While
mechanically very different from traditional calibration as discussed above, we will refer to our
approach as conformal calibration to highlight that the two methodologies have overlapping but
different goals.
Conformal prediction is a general framework, not a speciﬁc algorithm—important design decisions
must be made to achieve the best performance for each context. To this end, Romano et al. (2020)
and Cauchois et al. (2020) introduce techniques aimed at achieving coverage that is similar across
regions of feature space, whereas ?Hechtlinger et al. (2018) and ? introduce techniques aimed at
achieving equal coverage for each class. While these methods have conceptual appeal, thus far
there has been limited empirical evaluation of this general approach for state-of-the-art CNNs. Con-
cretely, the only works that we are aware of that include some evaluation of conformal methods on
ImageNet—the gold standard for benchmarking computer vision methods—are Hechtlinger et al.
(2018), Park et al. (2019), Cauchois et al. (2020), and Messoudi et al. (2020), although in all four
cases further experiments are needed to more fully evaluate their operating characteristics for practi-
cal deployment. At the heart of conformal prediction is theconformal score: a measure of similarity
between labeled examples which is used to compare a new point to among those in a hold out set.
Our theoretical contribution can be summarized as a modiﬁcation of the conformal score from Ro-
mano et al. (2020) to have smaller, more stable sets. Lastly, there are alternative approaches to
returning prediction sets not based on conformal prediction (Pearce et al., 2018; Zhang et al., 2018).
These methods can be used as input to a conformal procedure to potentially improve performance,
but they do not have ﬁnite-sample coverage guarantees when used alone.
2 M ETHODS
In developing uncertainty set methods to improve upon naive, we are guided by three desiderata.
First and most importantly, the coverage desideratum says the sets must provide 1−α coverage, as
Algorithm 1 Naive Prediction Sets
Input: α, sorted scoress, associated permutation of classesI, booleanrand
1: procedure NAIVE (α,s,I,rand )
2: L← 1
3: while∑Li=1si &lt; 1−α do ⊿ Stop if 1−α probability exceeded
4: L←L + 1
5: ifrand then ⊿ Break ties randomly (explained in Appendix B)
6: U← Unif(0, 1)
7: V ← (∑Li=1si− (1−α))/sL
8: ifU≤V then
9: L←L− 1
10: return
I1,...,I L
Output: The 1−α prediction set,
I1,...,I L

=== 2009.14193 PDF PAGE 4 ===
 τ^ccal0
1−α′
τ: set size parameter
empirical coverage
(a) Conformal calibration
kreg τ^ccal
c d f b e a
class
penalized probability
penalty
probability (b) A RAPS prediction set
Figure 3: Visualizations of conformal calibration and RAPS sets. In the left panel, the y-axis shows the
empirical coverage on the conformal calibration set, and 1−α′ =⌈(n + 1)(1−α)⌉/n. In the right panel, the
printed numbers indicate the cumulative probability plus penalty mass. For the indicated value ˆτccal, the RAPS
prediction set is{c, d, f, b}.
discussed above. Secondly, the size desideratum says we want sets of small size, since these convey
more detailed information and may be more useful in practice. Lastly, the adaptiveness desidera-
tum says we want the sets to communicate instance-wise uncertainty: they should be smaller for
easy test-time examples than for hard ones; see Figure 1 for an illustration. Coverage and size
are obviously competing objectives, but size and adaptiveness are also often in tension. The size
desideratum seeks small sets, while the adaptiveness desideratum seeks larger sets when the classi-
ﬁer is uncertain. For example, always predicting a set of size ﬁve could achieve coverage, but it is
not adaptive. As noted above, both APSand RAPS achieve correct coverage, and we will show that
RAPS improves upon APS according to the other two desiderata.
We now turn to the speciﬁcs of our proposed method. We begin in Subsection 2.1 by describing an
abstract data-splitting procedure called conformal calibration that enables the near-automatic con-
struction of valid predictive sets (that is, sets satisfying Eq. (1)). Subsequently, in Subsection 2.2, we
provide a detailed presentation of our procedure, with commentary in Section 2.3. In Subsection 2.4
we discuss the optimality of our procedure, proving that it is at least as good as the procedure that
returns sets of a ﬁxed size, unlike alternative approaches.
2.1 C ONFORMAL CALIBRATION
We ﬁrst review a general technique for producing valid prediction sets, following the articulation
in Gupta et al. (2019). Consider a procedure that outputs a predictive set for each observation,
and further suppose that this procedure has a tuning parameter τ that controls the size of the sets.
(In RAPS, τ is the cumulative sum of the sorted, penalized classiﬁer scores.) We take a small
independent conformal calibration set of data, and then choose the tuning parameter τ such that
the predictive sets are large enough to achieve 1−α coverage on this set. See Figure 3 for an
illustration. This calibration step yields a choice ofτ, and the resulting set is formally guaranteed to
have coverage 1−α on a future test point from the same distribution; see Theorem 1 below.
Formally, let (Xi,Yi)i=1,...,n be an independent and identically distributed (i.i.d.) set of variables
that was not used for model training. Further, let C(x,u,τ ) : Rd× [0, 1]× R→ 2Y be a set-
valued function that takes a feature vectorx to a subset of the possible labels. The second argument
u is included to allow for randomized procedures; let U1,...,U n be i.i.d. uniform [0, 1] random
variables that will serve as the second argument for each data point. Suppose that the sets are
indexed byτ such that they are nested, meaning larger values ofτ lead to larger sets:
C(x,u,τ 1)⊆C (x,u,τ 2) if τ1≤τ2. (2)
To ﬁnd a function that will achieve 1−α coverage on test data, we select the smallest τ that gives
at least 1−α coverage on the conformal calibration set, with a slight correction to account for the
ﬁnite sample size:
ˆτccal = inf
τ :|{i :Yi∈C (Xi,Ui,τ )}|n ≥⌈(n + 1)(1−α)⌉n }. (3)
The set function C(x,u,τ ) with this data-driven choice of τ is guaranteed to have correct ﬁnite-
sample coverage on a fresh test observation, as stated formally next.

=== 2009.14193 PDF PAGE 6 ===
 Algorithm 2 RAPS Conformal Calibration
Input: α;s∈ [0, 1]n×K,I∈{ 1,...,K}n×K, andy∈{ 0, 1,...,K}n corresponding respectively to
the sorted scores, the associated permutation of indexes, and ground-truth labels for each of n
examples in the calibration set;kreg;λ; booleanrand
1: procedure RAPSC (α,s,I,y,λ)
2: fori∈{ 1,··· ,n} do
3: Li←j such thatIi,j =yi
4: Ei← ΣLij=1si,j +λ(Li−kreg)+
5: ifrand then
6: U∼ Unif(0, 1)
7: Ei←Ei−U∗si,Li
8: ˆτccal← the⌈(1−α)(1 +n)⌉ largest value in{Ei}ni=1
9: return ˆτccal
Output: The generalized quantile, ˆτccal ⊿ The value in Eq. (3)
Algorithm 3 RAPS Prediction Sets
Input: α, sorted scoress and the associated permutation of classesI for a test-time example, ˆτccal
from Algorithm 2,kreg,λ, booleanrand
1: procedure RAPS (α,s,I, ˆτccal,kreg,λ,rand )
2: L←|{ j∈Y : Σ ji=1si +λ(j−kreg)+≤ ˆτccal}| + 1
3: ifrand then
4: U← Unif(0, 1)
5: L←L− I
(ΣLi=1si +λ(L−kreg)+− ˆτccal)/(sL +λI(L&gt;k reg))≤U}
6: returnC =
I1,...IL
⊿ TheL most likely classes
Output: The 1−α conﬁdence set,C ⊿ The set in Eq. (4)
it is included in the predictive set. For example, if kreg = 5, then the sixth most likely value of y
has an extra penalty of size λ, so it will never be included until τ exceedsρx(y) + ˆπx(y)·u +λ,
whereas it enters whenτ exceedsρx(y) + ˆπx(y)·u in the nonregularized version. Our method has
the following coverage property:
Proposition 1 (RAPS coverage guarantee). Suppose (Xi,Yi,Ui)i=1,...,n and (Xn+1,Yn+1,Un+1)
are i.i.d. and letC∗(x,u,τ ) be deﬁned as in Eq. (4). Suppose further that ˆπx(y) &gt; 0 for allx and
y. Then for ˆτccal deﬁned as in Eq. (3), we have the following coverage guarantee:
1−α≤P
Yn+1∈C∗(Xn+1,Un+1, ˆτccal))≤ 1−α + 1n + 1.
Note that the ﬁrst inequality is a corollary of Theorem 1, and the second inequality is a special case
of the remark in Section 2.1. The restriction that ˆπx(y)&gt; 0 is not necessary for the ﬁrst inequality.
2.3 W HY REGULARIZE ?
In our experiments, the sets from APS are larger than necessary, because APS is sensitive to the
noisy probability estimates far down the list of classes. This noise leads to apermutation problem of
unlikely classes, where ordering of the classes with small probability estimates is determined mostly
by random chance. If 5% of the true classes from the calibration set are deep in the tail due to the
permutation problem, APS will choose large 95% predictive sets; see Figure 2. The inclusion of the
RAPS regularization causes the algorithm to avoid using the unreliable probabilities in the tail; see
Figure 4. We discuss how RAPS improves the adaptiveness of APS in Section 4 and Appendix E.
2.4 O PTIMALITY CONSIDERATIONS
To complement these experimental results, we now formally prove that RAPS with the correct reg-
ularization parameters will always dominate the simple procedure that returns a ﬁxed set size. (Sec-
tion 3.5 shows the parameters are easy to select and RAPS is not sensitive to their values). For a
feature vector x, let ˆy(j)(x) be the label with the jth highest predicted probability. We deﬁne the
top-k predictive sets to be{ˆy(1)(x),..., ˆy(k)(x)}.
Proposition 2 (RAPS dominates top-k sets). Suppose (Xi,Yi,Ui)i=1,...,n and (Xn+1,Yn+1,Un+1)
are i.i.d. draws. Let k∗ be the smallest k such that the top-k predictive sets have coverage at least

=== 2009.14193 PDF PAGE 7 ===
 Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.793 0.945 0.900 0.889 0.900 0.900 2.42 17.1 19.7 2.00
ResNet152 0.783 0.94 0.900 0.895 0.900 0.900 2.63 9.78 10.4 2.11
ResNet101 0.774 0.936 0.900 0.896 0.900 0.900 2.83 10.3 10.7 2.25
ResNet50 0.761 0.929 0.900 0.896 0.900 0.900 3.14 11.8 12.3 2.57
ResNet18 0.698 0.891 0.900 0.895 0.900 0.900 5.72 15.5 16.2 4.43
DenseNet161 0.771 0.936 0.900 0.894 0.900 0.900 2.84 11.2 12.1 2.29
VGG16 0.716 0.904 0.900 0.895 0.901 0.900 4.75 13.4 14.1 3.54
Inception 0.695 0.887 0.900 0.885 0.900 0.901 6.30 75.4 89.1 5.32
ShufﬂeNet 0.694 0.883 0.900 0.891 0.900 0.900 6.46 28.9 31.9 5.05
Table 1: Results on Imagenet-Val. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials. See Section 3.1 for full details.
⌈(n + 1)(1−α)⌉/n on the conformal calibration points (Xi,Yi)i=1,...,n. TakeC∗(x,u,τ ) as in Eq.
(4) with anykreg≤k∗ andλ = 1. Then with ˆτccal chosen as in Eq. (3), we have
C∗(Xn+1,Un+1, ˆτccal) ⊆ {ˆy(1)(x),..., ˆy(k∗)(x)}.
In words, the RAPS procedure with heavy regularization will be at least as good as the top-k proce-
dure in the sense that it has smaller or same average set size while maintaining the desired coverage
level. This is not true of either the naive baseline or the APS procedure; Table 2 shows that these
two procedures usually return predictive sets with size much larger thank∗.
3 E XPERIMENTS
In this section we report on experiments that study the performance of the predictive sets from
naive, APS, and RAPS, evaluating each based on the three desiderata above. We begin with a brief
preview of the experiments. In Experiment 1, we evaluate naive, APS, and RAPS on Imagenet-
Val. Both APS and RAPS provided almost exact coverage, while naive sets had coverage slightly
below the speciﬁed level. APS has larger sets on average than naive and RAPS. RAPS has a
much smaller average set size than APS and naive. In Experiment 2, we repeat Experiment 1 on
Imagenet-V2, and the conclusions still hold. In Experiment 3, we produce histograms of set sizes
for naive, APS, and RAPS for several different values ofλ, illustrating a simple tradeoff between
set size and adaptiveness. In Experiment 4, we compute histograms of RAPS sets stratiﬁed by
image difﬁculty, showing that RAPS sets are smaller for easier images than for difﬁcult ones. In
Experiment 5, we report the performance of RAPS with many values of the tuning parameters.
In our experiments, we use nine standard, pretrained Imagenet classiﬁers from the torchvision
repository (Paszke et al., 2019) with standard normalization, resize, and crop parameters. Before
applying naive, APS, or RAPS, we calibrated the classiﬁers using the standard temperature scal-
ing/Platt scaling procedure as in Guo et al. (2017) on the calibration set. Thereafter, naive, APS,
and RAPS were applied, with RAPS using a data-driven choice of parameters described in Ap-
pendix E. We use the randomized versions of these algorithms—see Appendix B for a discussion.
3.1 E XPERIMENT 1: COVERAGE VS SET SIZE ON IMAGENET
In this experiment, we calculated the coverage and mean set size of each procedure for two different
choices of α. Over 100 trials, we randomly sampled two subsets of Imagenet-Val: one conformal
calibration subset of size 20K and one evaluation subset of size 20K. The median-of-means over
trials for both coverage and set size are reported in Table 1. Figure 2 illustrates the performances of
naive, APS, and RAPS; RAPS has much smaller sets than both naive and APS, while achieving
coverage. We also report results from a conformalized ﬁxed-k procedure, which ﬁnds the smallest
ﬁxed set size achieving coverage on the holdout set, k∗, then predicts sets of size k∗− 1 ork∗ on
new examples in order to achieve exact coverage; see Algorithm 4 in Appendix E.

=== 2009.14193 PDF PAGE 8 ===
 Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS Top K Naive APS RAPS
ResNeXt101 0.678 0.874 0.900 0.888 0.899 0.899 7.48 43.0 50.8 6.18
ResNet152 0.67 0.876 0.899 0.896 0.900 0.900 7.18 25.8 27.2 5.69
ResNet101 0.657 0.859 0.901 0.894 0.900 0.898 9.21 28.7 30.7 6.93
ResNet50 0.634 0.847 0.898 0.894 0.899 0.900 10.3 30.3 32.3 7.80
ResNet18 0.572 0.802 0.902 0.895 0.900 0.900 17.5 35.3 37.4 13.3
DenseNet161 0.653 0.862 0.902 0.895 0.901 0.901 8.6 29.9 32.4 6.93
VGG16 0.588 0.817 0.902 0.897 0.900 0.899 15.1 31.9 32.8 11.2
Inception 0.573 0.797 0.900 0.893 0.900 0.899 21.8 145.0 155.0 20.5
ShufﬂeNet 0.559 0.781 0.899 0.892 0.900 0.899 26.0 66.2 71.7 22.5
Table 2: Results on Imagenet-V2. We report coverage and size of the optimal, randomized ﬁxed sets,naive,
APS, and RAPS sets for nine different Imagenet classiﬁers. The median-of-means for each column is reported
over 100 different trials at the 10% level. See Section 3.2 for full details.
size
frequency
size
size
 method
Naive
APS
RAPS
Figure 4: Set sizes produced with ResNet-152. See Section 3.3 for details.
3.2 E XPERIMENT 2: COVERAGE VS SET SIZE ON IMAGENET -V2
The same procedure as Experiment 1 was repeated on Imagenet-V2, with exactly the same normal-
ization, resize, and crop parameters. The size of the calibration and evaluation sets was 5K, since
Imagenet-V2 is a smaller dataset. The result shows that our method can still provide coverage even
for models trained on different distributions, as long as the conformal calibration set comes from the
new distribution. The variance of the coverage is higher due to having less data.
3.3 E XPERIMENT 3: S ET SIZES OF N A I V E, APS, AND RAPS ON IMAGENET
We investigate the effect of regularization in more detail. For three values ofλ, we collected the set
sizes produced by each of naive, APS, and RAPS and report their histograms in Figure 4.
3.4 E XPERIMENT 4: A DAPTIVENESS OF RAPS ON IMAGENET
We now show thatRAPS sets are smaller for easy images than hard ones, addressing the adaptiveness
desideratum.
Table 4 reports the size-stratiﬁed coverages of RAPS at the 90% level with kreg = 5 and different
choices ofλ. Whenλ is small, RAPS allows sets to be large. But whenλ = 1, RAPS clips sets to be
a maximum of size 5. Table 8 (in the Appendix) stratiﬁes by image difﬁculty, showing that RAPS
sets are small for easy examples and large for hard ones. Experiments 3 and 4 together illustrate
the tradeoff between adaptiveness and size: as the average set size decreases, the RAPS procedure
truncates sets larger than the smallest ﬁxed set that provides coverage, taming the heavy tail of the
APS procedure. Since RAPS with largeλ undercovers hard examples, it must compensate by taking
larger sets for easy examples to ensure the 1−α marginal coverage guarantee. However, the size
only increases slightly since easy images are more common than hard ones, and the total probability
mass can often exceed ˆτccal by including only one more class. If this behavior is not desired, we can
instead automatically pickλ to optimize the adaptiveness of RAPS; see Section 4.
3.5 E XPERIMENT 5: CHOICE OF TUNING PARAMETERS
While any value of the tuning parametersλ andkreg lead to coverage (Proposition 1), some values
will lead to smaller sets. In Experiments 1 and 2, we chose kreg andλ adaptively from data (see
Appendix E), achieving strong results for all models and choices of the coverage level. Table 3 gives
the performance of RAPS with many choices ofkreg andλ for ResNet-152.

=== 2009.14193 PDF PAGE 9 ===
 kreg|λ 0 1e-4 1e-3 0.01 0.02 0.05 0.2 0.5 0.7 1.0
1 11.2 10.2 7.0 3.6 2.9 2.3 2.1 2.3 2.2 2.2
2 11.2 10.2 7.1 3.7 3.0 2.4 2.1 2.3 2.2 2.2
5 11.2 10.2 7.2 3.9 3.4 2.9 2.6 2.5 2.5 2.5
10 11.2 10.2 7.4 4.5 4.0 3.6 3.4 3.4 3.4 3.4
50 11.2 10.6 8.7 7.2 7.0 6.9 6.9 6.9 6.9 6.9
Table 3: Set sizes of RAPS with parameterskreg andλ, a ResNet-152, and coverage level 90%.
λ = 0 λ = 0.001 λ = 0.01 λ = 0.1 λ = 1
size cnt cvg cnt cvg cnt cvg cnt cvg cnt cvg
0 to 1 11627 0.88 11539 0.88 11225 0.89 10476 0.92 10027 0.93
2 to 3 3687 0.91 3702 0.91 3741 0.92 3845 0.93 3922 0.94
4 to 6 1239 0.91 1290 0.91 1706 0.92 4221 0.89 6051 0.83
7 to 10 688 0.93 765 0.93 1314 0.91 1436 0.71 0
11 to 100 2207 0.94 2604 0.93 2014 0.86 22 0.59 0
101 to 1000 552 0.97 100 0.90 0 0 0
Table 4: Coverage conditional on set size. We report average coverage of images stratiﬁed by the size of the
set output by RAPS using a ResNet-152 for varyingλ. The marginal coverage rate is 90%.
4 A DAPTIVENESS AND CONDITIONAL COVERAGE
In this section, we point to a deﬁnition of adaptiveness that is more natural for the image classiﬁ-
cation setting than the existing notion of conditional coverage. We show that APS does not satisfy
conditional coverage, and that RAPS with smallλ outperforms it in terms of adaptiveness.
4.1 A METRIC OF CONDITIONAL COVERAGE
We say that a set-valued predictor C : Rd → 2Y satisﬁes exact conditional coverage if P (Y ∈
C(X)| X = x) = 1−α for eachx. Distribution-free guarantees on conditional coverage are im-
possible (V ovk, 2012; Lei &amp; Wasserman, 2014), but many algorithms try to satisfy it approximately
(Romano et al., 2019; 2020; Cauchois et al., 2020). In a similar spirit, Tibshirani et al. (2019) sug-
gest a notion of local conditional coverage, where one asks for coverage in a neighborhood of each
point, weighted according to a chosen kernel. Cauchois et al. (2020) introduce the worst-case slab
metric for measuring violations of the conditional coverage property. We present a different way of
measuring violations of conditional coverage based on the following result:
Proposition 3. SupposeP (Y ∈C (X)|X =x) = 1−α for eachx∈ Rd. Then,
P (Y ∈C (X)|{|C(X)|∈A} ) = 1−α for anyA⊂{ 0, 1, 2,... }.
In words, if conditional coverage holds, then coverage holds after stratifying by set size.
In Table 4, we report on the coverage of APS and RAPS, stratiﬁed by the size of the prediction set.
Turning our attention to theλ = 0 column, we see that when APS outputs a set of size 101− 1000,
APS has coverage 97%, substantially higher than 90% nominal rate. By Proposition 3, we conclude
that APS is not achieving exact conditional coverage, because the scores are far from the oracle
probabilities. The APS procedure still achieves marginal coverage by overcovering hard examples
and undercovering easy ones, an undesirable behavior. Alternatively,RAPS can be used to regularize
the set sizes—for λ = .001 to λ = .01 the coverage stratiﬁed by set size is more balanced. In
summary, even purely based on the adaptiveness desideratum, RAPS with light regularization is
preferable to APS. Note that as the size of the training data increases, as long as ˆπ is consistent,
naive and APS will become more stable, and so we expect less regularization will be needed.
We now describe a particular manifestation of our adaptiveness criterion that we will use to optimize
λ. Consider disjoint set-size strata{Si}i=si=1, where⋃j=sj=1Si ={1,..., |Y|}. Then deﬁne the indexes
of examples stratiﬁed by the prediction set size of each example from algorithm C asJj =
i :
|C(Xi,Yi,Ui)|∈ Sj
. Then we can deﬁne the size-stratiﬁed coverage violation of an algorithmC
on strata{S}i=si=1 as
SSCV
C,{S}j=sj=1) = supj
⏐⏐⏐⏐⏐|{i : Yi∈C (Xi, Yi, Ui), i∈J j}||Jj| − (1−α)⏐⏐⏐⏐⏐. (5)

=== 2009.14193 PDF PAGE 17 ===
 Accuracy Coverage Size
Model Top-1 Top-5 Top K Naive APS RAPS LAC Top K Naive APS RAPS LAC
ResNeXt101 0.793 0.945 0.900 0.889 0.900 0.900 0.900 2.42 17.2 19.9 2.01 1.65
ResNet152 0.783 0.941 0.900 0.894 0.900 0.900 0.900 2.64 9.68 10.4 2.09 1.76
ResNet101 0.774 0.936 0.900 0.895 0.900 0.900 0.900 2.83 10.0 10.8 2.25 1.87
ResNet50 0.761 0.929 0.899 0.896 0.900 0.900 0.900 3.13 11.7 12.3 2.55 2.05
ResNet18 0.698 0.891 0.900 0.895 0.900 0.900 0.900 5.74 15.3 16.1 4.38 3.64
DenseNet161 0.771 0.936 0.900 0.894 0.900 0.900 0.900 2.84 11.2 12.0 2.29 1.90
VGG16 0.716 0.904 0.900 0.896 0.901 0.900 0.900 4.75 13.4 14.1 3.54 3.00
Inception 0.695 0.886 0.899 0.884 0.900 0.899 0.900 6.27 74.8 88.8 5.24 4.06
ShufﬂeNet 0.694 0.883 0.900 0.892 0.900 0.899 0.900 6.45 28.8 32.1 5.01 4.14
Table 9: Results on Imagenet-Val. We report coverage and size of the optimal, randomized ﬁxed sets,naive, APS, RAPS , and the LAC sets for nine different Imagenet classiﬁers.
The median-of-means for each column is reported over 100 different trials at the 10% level. See Section 3.1 for full details.

=== 1904.06019 PDF PAGE 3 ===
 Theorem 1 (V ovk et al. 2005; Lei et al. 2018). Assume that (Xi,Yi)∈ Rd× R,i = 1,...,n + 1 are exchangeable.
For any score functionS, and anyα∈ (0, 1), deﬁne the conformal band (based on the ﬁrstn samples) atx∈ Rd by
ˆCn(x) =
y∈ R :V (x,y)n+1 ≤ Quantile(1−α;V (x,y)1:n ∪{∞})}, (5)
whereV (x,y)i ,i = 1,...,n + 1 are as deﬁned in (4). Then ˆCn satisﬁes
P
Yn+1∈ ˆCn(Xn+1)
≥ 1−α.
Furthermore, if ties betweenV (Xn+1,Yn+1)1 ,...,V (Xn+1,Yn+1)n+1 occur with probability zero, then this probability is upper
bounded by 1−α + 1/(n + 1).
Proof. To lighten notation, abbreviateVi =V (Xn+1,Yn+1)i ,i = 1,...,n + 1. Observe
Yn+1∈ ˆCn(Xn+1) ⇐⇒ Vn+1≤ Quantile(1−α;V1:n∪{∞}).
By the symmetric construction of the nonconformity scores in (4),
(Z1,...,Z n+1)
d
= (Zσ(1),...,Z σ(n+1)) ⇐⇒ (V1,...,V n+1)
d
= (Vσ(1),...,V σ(n+1)),
for any permutationσ of the numbers 1,...,n + 1. Therefore, asZ1,...,Z n+1 are exchangeable, so areV1,...,V n+1,
and applying Lemma 1 gives the result.
Remark 1. Theorem 1 is stated for exchangeable samples (Xi,Yi),i = 1,...,n + 1, which is (signiﬁcantly) weaker
than assuming i.i.d. samples. As we will see in what follows, it is furthermore possible to relax the exchangeability
assumption, under an appropriate modiﬁcation to the conformal procedure.
Remark 2. If we use an appropriate random tie-breaking rule (to determine the rank ofVn+1 amongV1,...,V n+1),
then the upper bounds in Lemma 1 and Theorem 1 hold in general (without assuming there are no ties almost surely).
The result in Theorem 1, albeit very simple to prove, is quite remarkable. It gives us a recipe for distribution-free
prediction intervals, with nearly exact coverage, starting from an arbitrary score functionS; e.g., absolute residuals
with respect to a ﬁtted regression function from any base algorithmA, as in (3). For more discussion of conformal
prediction, its properties, and its variants, we refer to V ovk et al. (2005); Lei et al. (2018) and references therein.
2 Covariate shift
In this paper, we are concerned with settings in which the data (Xi,Yi),i = 1,...,n + 1 are no longer exchangeable.
Our primary focus will be a setting in which we observe data according to
(Xi,Yi)
i.i.d.
∼ P =PX×PY|X, i= 1,...,n,
(Xn+1,Yn+1)∼ ~P = ~PX×PY|X, independently. (6)
Notice that the conditional distribution ofY|X is assumed to be the same for both the training and test data. Such a
setting is often called covariate shift (e.g., see Shimodaira 2000; Quinonero-Candela et al. 2009; see also Remark 4
below for more discussion of this literature). The key realization is the following: if we know the ratio of test to training
covariate likelihoods, d~PX/dPX, then we can still perform a modiﬁed of version conformal inference, using a quantile
of a suitably weighted empirical distribution of nonconformity scores. The next subsection gives the details; following
this, we describe a more computationally efﬁcient conformal procedure, and give an empirical demonstration.
2.1 Weighted conformal prediction
In conformal prediction, we compare the value of a nonconformity score at a test point to the empirical distribution of
nonconformity scores at the training points. In the covariate shift case, where the covariate distributions PX,~PX in
our training and test sets differ, we will now weight each nonconformity scoreV (x,y)i (which measures how wellZi =

=== 1904.06019 PDF PAGE 4 ===
 (Xi,Yi) conforms to the other points) by a probability proportional to the likelihood ratiow(Xi) = d~PX (Xi)/dPX (Xi).
Therefore, we will no longer be interested in the empirical distribution
n + 1
n∑
i=1
δV (x,y)i + 1n + 1δ∞,
as in Theorem 1, but rather, a weighted version
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞,
where the weights are deﬁned by
pwi (x) = w(Xi)∑n
j=1w(Xj) +w(x), i= 1,...,n, and pwn+1(x) = w(x)∑nj=1w(Xj) +w(x). (7)
Due this careful weighting, draws from the discrete distribution in the second to last display resemble nonconformity
scores computed on the test population, and thus, they “look exchangeable” with the nonconformity score at our test
point. Our main result below formalizes these claims.
Corollary 1. Assume data from the model(6). Assume that ~PX is absolutely continuous with respect toPX, and denote
w = d~PX/dPX. For any score functionS, and anyα∈ (0, 1), deﬁne forx∈ Rd,
ˆCn(x) =
y∈ R :V (x,y)n+1 ≤ Quantile
1−α;
n∑
i=1
pwi (x)δV (x,y)i +pwn+1(x)δ∞
whereV (x,y)i ,i = 1,...,n + 1 are as in (4), andpwi (x),i = 1,...,n + 1 are as in (7). Then ˆCn satisﬁes
P
Yn+1∈ ˆCn(Xn+1)
≥ 1−α.
Corollary 1 is a special case of a more general result that we present later in Theorem 2, which extends conformal
inference to a setting in which the data are what we call weighted exchangeable. The proof is given in Section 3.5.
Remark 3. The same result as in Corollary 1 holds ifw∝ d~PX/dPX, i.e., with an unknown normalization constant,
because this normalization constant cancels out in the calculation of probabilities in (7).
Remark 4. Though the basic premise of covariate shift—and certainly the techniques employed in addressing it—are
related to much older ideas in statistics, the speciﬁc setup (6) has recently generated great interest in machine learning:
e.g., see Sugiyama and Muller (2005); Sugiyama et al. (2007); Quinonero-Candela et al. (2009); Agarwal et al. (2011);
Wen et al. (2014); Reddi et al. (2015); Chen et al. (2016) and references therein). The focus is usually on correcting
estimators, model evaluation, or model selection approaches to account for covariate shift. Correcting distribution-free
prediction intervals, as we examine in this work, is (as far as we know) a new contribution. As one might expect, the
likelihood ratio d~PX/dPX, a key component of our conformal construction in Corollary 1, also plays a critical role in
much of the literature on covariate shift.
2.2 Weighted split conformal
In general, constructing a conformal prediction band can be computationally intensive, though this of course depends
on the choice of score function. Consider the use of absolute residuals as in (3). To compute the nonconformity scores
in (4), we must ﬁrst run our base algorithmA on the data setZ1:n∪{ (x,y )} to produce a ﬁtted regression functionˆµ,
and then calculate
V (x,y)i =|Yi−ˆµ(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−ˆµ(x)|.
As the formation of the conformal set in (5) (ordinary case) or (8) (covariate shift case) requires us to do this for each
x∈ Rd andy∈ R (which requires reﬁttingˆµ each time), this can clearly become computationally burdernsome.
A fast alternative, known as split conformal prediction (Papadopoulos et al., 2002; Lei et al., 2015), resolves this
issue by taking the score functionS to be deﬁned using absolute residuals with respect to a ﬁxed regression function,

=== 1904.06019 PDF PAGE 5 ===
 typically, one that has been trained on an preliminary data set. Denote by (X 01,Y 01 ),..., (X 0n0,Y 0n0 ) this preliminary
data set, used for ﬁtting the regression functionµ0, and consider the score function
S
(x,y ),Z
=|y−µ0(x)|.
Given data (X1,Y 1),..., (Xn,Yn), independent of (X 01,Y 01 ),..., (X 0n0,Y 0n0 ), we calculate
V (x,y)i =|Yi−µ0(Xi)|, i= 1,...,n, and V (x,y)n+1 =|y−µ0(x)|.
The conformal prediction interval (5), deﬁned at a pointx∈ Rd, reduces to
ˆCn(x) = µ0(x)± Quantile
1−α;
|Yi−µ0(Xi)|
}n
i=1∪{∞}
and by Theorem 1 it has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ). This coverage result holds
because, when we treatµ0 as ﬁxed (meaning, condition on (X 01,Y 01 ),..., (X 0n0,Y 0n0 )), the scoresV (x,y)1 ,...,V (x,y)n+1
scores are exchangeable for (x,y ) = (Xn+1,Yn+1), as (X1,Y 1),..., (Xn+1,Yn+1) are.
As split conformal prediction can be seen as a special case of conformal prediction, in which the regression function
µ0 is treated as ﬁxed, Corollary 1 also applies to the split scenario, and guarantees that the band deﬁned forx∈ Rd by
ˆCn(x) = µ0(x)± Quantile
1−α;
n∑
i=1
pwi (x)δ|Yi−µ0(Xi)| +pwn+1(x)δ∞
where the probabilities are as in (7), has coverage at least 1−α, conditional on (X 01,Y 01 ),..., (X 0n0,Y 0n0 ).
2.3 Airfoil data example
We demonstrate the use of conformal prediction in the covariate shift setting in an empirical example. We consider the
airfoil data set from the UCI Machine Learning Repository (Dua and Graff, 2019), which hasN = 1503 observations of
a responseY (scaled sound pressure level of NASA airfoils), and a covariateX withd = 5 dimensions (log frequency,
angle of attack, chord length, free-stream velocity, and suction side log displacement thickness). For efﬁciency, we use
the split conformal prediction methods in (9) and (10) for the unweighted and weighted case, respectively. R code to
reproduce these simulation results can be found at http://www.github.com/ryantibs/conformal/.
Creating training data, test data, and covariate shift. We repeated an experiment for 5000 trials, where for each
trial we randomly partitioned the data{(Xi,Yi)}Ni=1 into three setsDpre,D train,D test, and also constructed a covariate
shift test setDshift, which have the following roles.
• Dpre, containing 25% of the data, is used to preﬁt a regression functionµ0 via linear regression, to be used in
constructing split conformal intervals.
• Dtrain, containing 25% of the data, is our training set, i.e., (Xi,Yi),i = 1,...,n , used to compute the residual
quantiles in the construction of the split conformal prediction intervals (9) and (10).
• Dtest, containing 50% of the data, is our test set (as these data points are exchangeable with those inDtrain, there
is no covariate shift in this test set).
• Dshift is a second test set, constructed to simulate covariate shift, by sampling 25% of the points fromDtest with
replacement, with probabilities proportional to
w(x) = exp(xTβ), where β = (−1, 0, 0, 0, 1). (11)
As the original data pointsDtrain∪Dtest can be seen as draws from the same underlying distribution, we can view
w(x) as the likelihood ratio of covariate distributions between the test setDshift and training setDtrain. Note that the test
covariate distribution~PX, which satisﬁes d~PX∝ exp(xTβ)dPX as we have deﬁned it here, is called an exponential
tilting of the training covariate distributionPX. Figure 1 visualizes the effect of this exponential tilting, in the airfoil
data set, with our choiceβ = (−1, 0, 0, 0, 1). Only the 1st and 5th dimensions of the covariate distribution are tilted;
the bottom row of Figure 1 plots the marginal densities of the 1st and 5th covariates (estimated via kernel smoothing)
before and after the tilt. The top row plots the response versus the 1st and 5th covariates, simply to highlight the fact
that there is heteroskedasticity, and thus we might expect the shift in the covariate distribution to have some effect on
the validity of the ordinary conformal prediction intervals.

=== 1904.06019 PDF PAGE 6 ===
 x1
y
x1
Frequency
x5
y
0.0 0.1 0.2 0.3 0.4 0.5 0.6
x5
Frequency
Figure 1: The top row plots the response in (a randomly chosen half of) the airfoil data set, versus the 1st and 5th covariates. The
bottom row plots kernel density estimates for the 1st and 5th covariates, in black. Also displayed are kernel density estimates for the
1st and 5th covariates after exponential tilting (11), in blue.
Loss of coverage of ordinary conformal prediction under covariate shift. First, we examine the performance of
ordinary split conformal prediction (9). The nominal coverage level was set to be 90% (meaningα = 0.1), here and
throughout. The results are shown in the top row of Figure 2. In each of the 5000 trials, we computed the empirical
coverage from the split conformal intervals over points in the test sets, and the histograms show the distribution of these
empirical coverages over the trials. We see that for the original test dataDtest (no covariate shift, shown in red), split
conformal works as expected, with the average of the empirical coverages (over the 5000 trials) being 90.2%; but for
the nonuniformly subsampled test dataDshift (covariate shift, in blue), split conformal considerably undercovers, with
its average coverage being 82.2%.
Coverage of weighted conformal prediction with oracle weights. Next, displayed in the middle row of Figure 2,
we consider weighted split conformal prediction (10), to cover the points inDshift (shown in orange). At the moment,
we assume oracle knowledge of the true weight functionw in (11) needed to calculate the probabilities in (7). We see
that this brings the coverage back to the desired level, with the average coverage being 90.8%. However, the histogram
is more dispersed than it is when there is no covariate shift (compare to the top row, in red). This is because, by using a
quantile of the weighted empirical distribution of nonconformity scores, we are relying on a reduced “effective sample
size”. Given training pointsX1,...,X n, and a likelihood ratiow of test to training covariate distributions, a popular
heuristic formula from the covariate shift literature for the effective sample size ofX1,...,X n is (Gretton et al., 2009;
Reddi et al., 2015):
ˆn = [∑ni=1|w(Xi)|]2∑n
i=1|w(Xi)|2 =‖w(X1:n)‖21‖w(X1:n)‖22,

=== 1904.06019 PDF PAGE 8 ===
 where we abbreviatew(X1:n) = (w(X1),...,w (Xn))∈ Rn. To compare weighted conformal prediction against the
unweighted method at the same effective sample size, in each trial, we ran unweighted split conformal on the original
test setDtest, but we used onlyˆn subsampled points fromDtrain to compute the quantile of nonconformity scores, when
constructing the prediction interval (9). The results (the middle row of Figure 2, in purple) line up very closely with
those from weighted conformal, which demonstrates that apparent overdispersion in the coverage histogram from the
latter is fully explained by the reduced effective sample size.
Coverage of weighted conformal with estimated weights. Denote byX1,...,X n the covariate points inDtrain and
byXn+1,...,X n+m the covariate points inDshift. Here we describe how to estimatew = d~PX/dPX, the likelihood
ratio of interest, by applying logistic regression or random forests (more generally, any classiﬁer that outputs estimated
probabilities of class membership) to the feature-class pairs (Xi,Ci),i = 1,...,n +m, whereCi = 0 fori = 1,...,n
andCi = 1 fori =n + 1,...,n +m. Noting that
P(C = 1|X =x)
P(C = 0|X =x) = P(C = 1)P(C = 0) d~PXdPX (x),
we can take the conditional odds ratiow(x) = P(C = 1|X =x)/P(C = 0|X =x) as an equivalent representation
for the oracle weight function (since we only need to know the likelihood ratio up to a proportionality constant, recall
Remark 3). Therefore, ifˆp(x) is an estimate of P(C = 1|X =x) obtained by ﬁtting a classiﬁer to the data (Xi,Ci),
i = 1,...,n +m, then we can use
ˆw(x) = ˆp(x)1−ˆp(x) (12)
as our estimated weight function for the calculation of probabilities (7), needed for conformal (8) or split conformal
(10). There is in fact a sizeable literature on density ratio estimation, and the method just describe falls into a class
called probabilistic classiﬁcation approaches; two other classes are based on moment matching, and minimization of
φ-divergences (e.g., Kullblack-Leibler divergence). For a comprehensive review of these approaches, and supporting
theory, see Sugiyama et al. (2012).
The bottom row of Figure 2 shows the results from using weighted split conformal prediction to cover the points
inDshift, where the weight function ˆw has been estimated as in (12), using logistic regression (in gray) and random
forests3 (in green) to ﬁt the class probability functionˆp. Note that logistic regression is well-speciﬁed in this example,
because it assumes the log odds is a linear function ofx, which is exactly as in (11). Random forests, of course, allows
more ﬂexibility in the ﬁtted model. Both classiﬁcation approaches deliver weights that translate into good average
coverage, being 91.0% for each approach. Furthermore, their histograms are only a little more dispersed than that for
the oracle weights (middle row, in orange).
Lengths of weighted conformal intervals. Figure 3 conveys the same setup as Figure 2, but displays histograms of
the median lengths of prediction intervals rather than empirical coverages (meaning, in each of the 5000 trials, we ran
unweighted or weighted split conformal prediction to cover test points, and report the median length of the prediction
intervals over the test sets). We see no differences in the lengths of ordinary split conformal intervals (top row) when
there is or is not covariate shift, as expected since these two settings differ only in the distributions of their test sets,
but use the same procedure and have the same distribution of the training data. We see that the oracle-weighted split
conformal intervals are longer than the ordinary split conformal intervals that use an equivalent effective sample size
(middle row). This is also as expected, since in the former situation, the regression functionµ0 was ﬁt on training data
Dtrain of a different distribution thanDshift, andµ0 itself should ideally be adjusted to account for covariate shift (plenty
of methods for this are available from the covariate shift literature, but we left it unadjusted for simplicity). Lastly, we
see that the random forests-weighted split conformal intervals are more variable, and in some cases, much longer, than
the logistic regression-weighted split conformal intervals (bottom row, difﬁcult to conﬁrm visually because the bars in
the histogram lie so close to the x-axis).
3In the random forests approach, we clipped the estimated test class probability ˆp(x) to lie in between 0.01 and 0.99, to prevent the estimated
weight (likelihood ratio) ˆw(x) from being inﬁnite. Without clipping, the estimated probability of being in the test class was sometimes exactly 1 (this
occurred in about 2% of the cases encountered over all 5000 repetitions), resulting in an inﬁnite weight, and causing numerical issues.

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking archive commit provenance**</reasoning></content>
  <tool_call id="call_347cab6a69b14f689bf432cc4b8d98a9" name="read_file">{"file_path": "/work/template/iclr2027/iclr2027_conference.sty", "limit": 300, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-246 of 246 @@
%%%% ICLR Macros (LaTex)
%%%% Adapted by Hugo Larochelle from the NIPS stylefile Macros
%%%% Style File
%%%% Dec 12, 1990   Rev Aug 14, 1991; Sept, 1995; April, 1997; April, 1999; October 2014

% This file can be used with Latex2e whether running in main mode, or
% 2.09 compatibility mode.
%
% If using main mode, you need to include the commands
%             \documentclass{article}
%             \usepackage{iclr14submit_e,times}
%

% Change the overall width of the page.  If these parameters are
%       changed, they will require corresponding changes in the
%       maketitle section.
%
\usepackage{eso-pic} % used by \AddToShipoutPicture
\RequirePackage{fancyhdr}
\RequirePackage{natbib}

% modification to natbib citations
\setcitestyle{authoryear,round,citesep={;},aysep={,},yysep={;}}

\renewcommand{\topfraction}{0.95}   % let figure take up nearly whole page
\renewcommand{\textfraction}{0.05}  % let figure take up nearly whole page

% Define iclrfinal, set to true if iclrfinalcopy is defined
\newif\ificlrfinal
\iclrfinalfalse
\def\iclrfinalcopy{\iclrfinaltrue}
\font\iclrtenhv  = phvb at 8pt

% Specify the dimensions of each page

\setlength{\paperheight}{11in}
\setlength{\paperwidth}{8.5in}


\oddsidemargin .5in    %   Note \oddsidemargin = \evensidemargin
\evensidemargin .5in
\marginparwidth 0.07 true in
%\marginparwidth 0.75 true in
%\topmargin 0 true pt           % Nominal distance from top of page to top of
%\topmargin 0.125in
\topmargin -0.625in
\addtolength{\headsep}{0.25in}
\textheight 9.0 true in       % Height of text (including footnotes &amp; figures)
\textwidth 5.5 true in        % Width of text line.
\widowpenalty=10000
\clubpenalty=10000

% \thispagestyle{empty}        \pagestyle{empty}
\flushbottom \sloppy

% We're never going to need a table of contents, so just flush it to
% save space --- suggested by drstrip@sandia-2
\def\addcontentsline#1#2#3{}

% Title stuff, taken from deproc.
\def\maketitle{\par
\begingroup
   \def\thefootnote{\fnsymbol{footnote}}
   \def\@makefnmark{\hbox to 0pt{$^{\@thefnmark}$\hss}} % for perfect author
                                                        % name centering
%   The footnote-mark was overlapping the footnote-text,
%   added the following to fix this problem               (MK)
   \long\def\@makefntext##1{\parindent 1em\noindent
                            \hbox to1.8em{\hss $\m@th ^{\@thefnmark}$}##1}
   \@maketitle \@thanks
\endgroup
\setcounter{footnote}{0}
\let\maketitle\relax \let\@maketitle\relax
\gdef\@thanks{}\gdef\@author{}\gdef\@title{}\let\thanks\relax}

% The toptitlebar has been raised to top-justify the first page

\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead{}

% Title (includes both anonimized and non-anonimized versions)
\def\@maketitle{\vbox{\hsize\textwidth
%\linewidth\hsize \vskip 0.1in \toptitlebar \centering
{\LARGE\sc \@title\par}
%\bottomtitlebar % \vskip 0.1in %  minus
\ificlrfinal
    \lhead{Published as a conference paper at ICLR 2027}
    \def\And{\end{tabular}\hfil\linebreak[0]\hfil
            \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}\ignorespaces}%
  \def\AND{\end{tabular}\hfil\linebreak[4]\hfil
            \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}\ignorespaces}%
    \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}\@author\end{tabular}%
\else
       \lhead{Under review as a conference paper at ICLR 2027}
   \def\And{\end{tabular}\hfil\linebreak[0]\hfil
            \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}\ignorespaces}%
  \def\AND{\end{tabular}\hfil\linebreak[4]\hfil
            \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}\ignorespaces}%
    \begin{tabular}[t]{l}\bf\rule{\z@}{24pt}Anonymous authors\\Paper under double-blind review\end{tabular}%
\fi
\vskip 0.3in minus 0.1in}}

\renewenvironment{abstract}{\vskip.075in\centerline{\large\sc
Abstract}\vspace{0.5ex}\begin{quote}}{\par\end{quote}\vskip 1ex}

% sections with less space
\def\section{\@startsection {section}{1}{\z@}{-2.0ex plus
    -0.5ex minus -.2ex}{1.5ex plus 0.3ex
minus0.2ex}{\large\sc\raggedright}}

\def\subsection{\@startsection{subsection}{2}{\z@}{-1.8ex plus
-0.5ex minus -.2ex}{0.8ex plus .2ex}{\normalsize\sc\raggedright}}
\def\subsubsection{\@startsection{subsubsection}{3}{\z@}{-1.5ex
plus      -0.5ex minus -.2ex}{0.5ex plus
.2ex}{\normalsize\sc\raggedright}}
\def\paragraph{\@startsection{paragraph}{4}{\z@}{1.5ex plus
0.5ex minus .2ex}{-1em}{\normalsize\bf}}
\def\subparagraph{\@startsection{subparagraph}{5}{\z@}{1.5ex plus
  0.5ex minus .2ex}{-1em}{\normalsize\sc}}
\def\subsubsubsection{\vskip
5pt{\noindent\normalsize\rm\raggedright}}


% Footnotes
\footnotesep 6.65pt %
\skip\footins 9pt plus 4pt minus 2pt
\def\footnoterule{\kern-3pt \hrule width 12pc \kern 2.6pt }
\setcounter{footnote}{0}

% Lists and paragraphs
\parindent 0pt
\topsep 4pt plus 1pt minus 2pt
\partopsep 1pt plus 0.5pt minus 0.5pt
\itemsep 2pt plus 1pt minus 0.5pt
\parsep 2pt plus 1pt minus 0.5pt
\parskip .5pc


%\leftmargin2em
\leftmargin3pc
\leftmargini\leftmargin \leftmarginii 2em
\leftmarginiii 1.5em \leftmarginiv 1.0em \leftmarginv .5em

%\labelsep \labelsep 5pt

\def\@listi{\leftmargin\leftmargini}
\def\@listii{\leftmargin\leftmarginii
   \labelwidth\leftmarginii\advance\labelwidth-\labelsep
   \topsep 2pt plus 1pt minus 0.5pt
   \parsep 1pt plus 0.5pt minus 0.5pt
   \itemsep \parsep}
\def\@listiii{\leftmargin\leftmarginiii
    \labelwidth\leftmarginiii\advance\labelwidth-\labelsep
    \topsep 1pt plus 0.5pt minus 0.5pt
    \parsep \z@ \partopsep 0.5pt plus 0pt minus 0.5pt
    \itemsep \topsep}
\def\@listiv{\leftmargin\leftmarginiv
     \labelwidth\leftmarginiv\advance\labelwidth-\labelsep}
\def\@listv{\leftmargin\leftmarginv
     \labelwidth\leftmarginv\advance\labelwidth-\labelsep}
\def\@listvi{\leftmargin\leftmarginvi
     \labelwidth\leftmarginvi\advance\labelwidth-\labelsep}

\abovedisplayskip 7pt plus2pt minus5pt%
\belowdisplayskip \abovedisplayskip
\abovedisplayshortskip  0pt plus3pt%
\belowdisplayshortskip  4pt plus3pt minus3pt%

% Less leading in most fonts (due to the narrow columns)
% The choices were between 1-pt and 1.5-pt leading
%\def\@normalsize{\@setsize\normalsize{11pt}\xpt\@xpt} % got rid of @ (MK)
\def\normalsize{\@setsize\normalsize{11pt}\xpt\@xpt}
\def\small{\@setsize\small{10pt}\ixpt\@ixpt}
\def\footnotesize{\@setsize\footnotesize{10pt}\ixpt\@ixpt}
\def\scriptsize{\@setsize\scriptsize{8pt}\viipt\@viipt}
\def\tiny{\@setsize\tiny{7pt}\vipt\@vipt}
\def\large{\@setsize\large{14pt}\xiipt\@xiipt}
\def\Large{\@setsize\Large{16pt}\xivpt\@xivpt}
\def\LARGE{\@setsize\LARGE{20pt}\xviipt\@xviipt}
\def\huge{\@setsize\huge{23pt}\xxpt\@xxpt}
\def\Huge{\@setsize\Huge{28pt}\xxvpt\@xxvpt}

\def\toptitlebar{\hrule height4pt\vskip .25in\vskip-\parskip}

\def\bottomtitlebar{\vskip .29in\vskip-\parskip\hrule height1pt\vskip
.09in} %
%Reduced second vskip to compensate for adding the strut in \@author



%% % Vertical Ruler
%% % This code is, largely, from the CVPR 2010 conference style file
%% % ----- define vruler
\makeatletter
\newbox\iclrrulerbox
\newcount\iclrrulercount
\newdimen\iclrruleroffset
\newdimen\cv@lineheight
\newdimen\cv@boxheight
\newbox\cv@tmpbox
\newcount\cv@refno
\newcount\cv@tot
% NUMBER with left flushed zeros  \fillzeros[&lt;WIDTH&gt;]&lt;NUMBER&gt;
\newcount\cv@tmpc@ \newcount\cv@tmpc
\def\fillzeros[#1]#2{\cv@tmpc@=#2\relax\ifnum\cv@tmpc@&lt;0\cv@tmpc@=-\cv@tmpc@\fi
\cv@tmpc=1 %
\loop\ifnum\cv@tmpc@&lt;10 \else \divide\cv@tmpc@ by 10 \advance\cv@tmpc by 1 \fi
   \ifnum\cv@tmpc@=10\relax\cv@tmpc@=11\relax\fi \ifnum\cv@tmpc@&gt;10 \repeat
\ifnum#2&lt;0\advance\cv@tmpc1\relax-\fi
\loop\ifnum\cv@tmpc&lt;#1\relax0\advance\cv@tmpc1\relax\fi \ifnum\cv@tmpc&lt;#1 \repeat
\cv@tmpc@=#2\relax\ifnum\cv@tmpc@&lt;0\cv@tmpc@=-\cv@tmpc@\fi \relax\the\cv@tmpc@}%
% \makevruler[&lt;SCALE&gt;][&lt;INITIAL_COUNT&gt;][&lt;STEP&gt;][&lt;DIGITS&gt;][&lt;HEIGHT&gt;]
\def\makevruler[#1][#2][#3][#4][#5]{\begingroup\offinterlineskip
\textheight=#5\vbadness=10000\vfuzz=120ex\overfullrule=0pt%
\global\setbox\iclrrulerbox=\vbox to \textheight{%
{\parskip=0pt\hfuzz=150em\cv@boxheight=\textheight
\cv@lineheight=#1\global\iclrrulercount=#2%
\cv@tot\cv@boxheight\divide\cv@tot\cv@lineheight\advance\cv@tot2%
\cv@refno1\vskip-\cv@lineheight\vskip1ex%
\loop\setbox\cv@tmpbox=\hbox to0cm{{\iclrtenhv\hfil\fillzeros[#4]\iclrrulercount}}%
\ht\cv@tmpbox\cv@lineheight\dp\cv@tmpbox0pt\box\cv@tmpbox\break
\advance\cv@refno1\global\advance\iclrrulercount#3\relax
\ifnum\cv@refno&lt;\cv@tot\repeat}}\endgroup}%
\makeatother
% ----- end of vruler

% \makevruler[&lt;SCALE&gt;][&lt;INITIAL_COUNT&gt;][&lt;STEP&gt;][&lt;DIGITS&gt;][&lt;HEIGHT&gt;]
\def\iclrruler#1{\makevruler[12pt][#1][1][3][0.993\textheight]\usebox{\iclrrulerbox}}
\AddToShipoutPicture{%
\ificlrfinal\else
\iclrruleroffset=\textheight
\advance\iclrruleroffset by -3.7pt
  \color[rgb]{.7,.7,.7}
  \AtTextUpperLeft{%
    \put(\LenToUnit{-35pt},\LenToUnit{-\iclrruleroffset}){%left ruler
      \iclrruler{\iclrrulercount}}
  }
\fi
}
% %% To add a vertical bar on the side
% \AddToShipoutPicture{
% \AtTextLowerLeft{
% \hspace*{-1.8cm}
% \colorbox[rgb]{0.7,0.7,0.7}{\small \parbox[b][\textheight]{0.1cm}{}}}
% }</message>
<message type="ai">
  <content><reasoning>**Archiving PDF evidence text**</reasoning></content>
  <tool_call id="call_7033a277114d4da78783e3992f44b461" name="ls">{"path": "/work/template/iclr2027"}</tool_call>
</message>
<message type="tool">['/template/iclr2027/fancyhdr.sty', '/template/iclr2027/iclr2027_conference.bib', '/template/iclr2027/iclr2027_conference.bst', '/template/iclr2027/iclr2027_conference.sty', '/template/iclr2027/iclr2027_conference.tex', '/template/iclr2027/math_commands.tex', '/template/iclr2027/natbib.sty']</message>
<message type="ai">
  <content><reasoning>**Checking root item type**</reasoning></content>
  <tool_call id="call_f6e39696deb3479880623298decb4538" name="read_file">{"file_path": "/work/template/iclr2027_contents.json", "limit": 330, "offset": 0}</tool_call>
</message>
<message type="tool">@@ lines 1-1 of 1 @@
[{"name":"fancyhdr.sty","path":"iclr2027/fancyhdr.sty","sha":"77ed4e3012d822c7cca5c17efcae308b32b8cc2b","size":20521,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/fancyhdr.sty?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/fancyhdr.sty","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/77ed4e3012d822c7cca5c17efcae308b32b8cc2b","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/fancyhdr.sty","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/fancyhdr.sty?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/77ed4e3012d822c7cca5c17efcae308b32b8cc2b","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/fancyhdr.sty"}},{"name":"iclr2027_conference.bib","path":"iclr2027/iclr2027_conference.bib","sha":"dbc773bf20f6a5e04306a5f7c8c4c759abf44baf","size":629,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.bib?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.bib","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/dbc773bf20f6a5e04306a5f7c8c4c759abf44baf","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.bib","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.bib?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/dbc773bf20f6a5e04306a5f7c8c4c759abf44baf","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.bib"}},{"name":"iclr2027_conference.bst","path":"iclr2027/iclr2027_conference.bst","sha":"a85a0087d13bb3d19ba2ca53cae3a9db47119853","size":26973,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.bst?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.bst","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/a85a0087d13bb3d19ba2ca53cae3a9db47119853","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.bst","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.bst?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/a85a0087d13bb3d19ba2ca53cae3a9db47119853","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.bst"}},{"name":"iclr2027_conference.sty","path":"iclr2027/iclr2027_conference.sty","sha":"f61ad7efce0855557694078c0945e6c33feb8236","size":9025,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.sty?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.sty","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/f61ad7efce0855557694078c0945e6c33feb8236","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.sty","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.sty?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/f61ad7efce0855557694078c0945e6c33feb8236","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.sty"}},{"name":"iclr2027_conference.tex","path":"iclr2027/iclr2027_conference.tex","sha":"c088c541a69898bbb329f86ba3a532254b31816b","size":19740,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.tex?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.tex","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/c088c541a69898bbb329f86ba3a532254b31816b","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.tex","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/iclr2027_conference.tex?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/c088c541a69898bbb329f86ba3a532254b31816b","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.tex"}},{"name":"math_commands.tex","path":"iclr2027/math_commands.tex","sha":"0668f931945175ca8535db25cc27fa603920cc3c","size":12284,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/math_commands.tex?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/math_commands.tex","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/0668f931945175ca8535db25cc27fa603920cc3c","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/math_commands.tex","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/math_commands.tex?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/0668f931945175ca8535db25cc27fa603920cc3c","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/math_commands.tex"}},{"name":"natbib.sty","path":"iclr2027/natbib.sty","sha":"ff0d0b91b6ef41468c593a0ca40a81f9a183b055","size":45154,"url":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/natbib.sty?ref=master","html_url":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/natbib.sty","git_url":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/ff0d0b91b6ef41468c593a0ca40a81f9a183b055","download_url":"https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/natbib.sty","type":"file","_links":{"self":"https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027/natbib.sty?ref=master","git":"https://api.github.com/repos/ICLR/Master-Template/git/blobs/ff0d0b91b6ef41468c593a0ca40a81f9a183b055","html":"https://github.com/ICLR/Master-Template/blob/master/iclr2027/natbib.sty"}}]</message>
<message type="ai">
  <content><reasoning>**Checking template placement**</reasoning> <reasoning>**Clarifying composition guarantees**</reasoning></content>
  <tool_call id="call_c47c8607ee1a4cafa9431555a34027cb" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2009.14193.pdf\"); print(\"PDF PAGE 5\\n\",r.pages[4].extract_text()); print(\"PDF PAGE 15\\n\",r.pages[14].extract_text()); print(\"PDF PAGE 16\\n\",r.pages[15].extract_text()); r=PdfReader(\"/work/literature/2107.07511.pdf\"); print(\"TUTORIAL PAGE 2\\n\",r.pages[1].extract_text()); print(\"TUTORIAL PAGE 12\\n\",r.pages[11].extract_text())'", "timeout": 60}</tool_call>
</message>
<message type="tool">PDF PAGE 5
 Theorem 1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi,Ui)i=1,...,n and
(Xn+1,Yn+1,Un+1) are i.i.d. and letC(x,u,τ ) be a set-valued function satisfying the nesting prop-
erty in Eq. (2). Suppose further that the sets C(x,u,τ ) grow to include all labels for large enough
τ: for all x∈ Rd,C(x,u,τ ) = Y for some τ. Then for ˆτccal deﬁned as in Eq. (3), we have the
following coverage guarantee:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≥ 1−α.
This is the same coverage property as Eq. (1) in the introduction, written in a more explicit manner.
The result is not new—a special case of this result leveraging sample-splitting ﬁrst appears in the
regression setting in Papadopoulos et al. (2002), and the core idea of conformal prediction was
introduced even earlier; see V ovk et al. (2005).
As a technical remark, the theorem also holds if the observations to satisfy the weaker condition
of exchangeability; see V ovk et al. (2005). In addition, for most families of set-valued functions
C(x,u,τ ) there is a matching upper bound:
P
(
Yn+1∈C (Xn+1,Un+1, ˆτccal)
)
≤ 1−α + 1n + 1.
Roughly speaking, this will hold whenever the sets grow smoothly in τ. See Lei et al. (2018) for a
formal statement of the required conditions.
2.2 O UR METHOD
Conformal calibration is a powerful general idea, allowing one to achieve the coverage desideratum
for any choice of setsC(x,u,τ ). Nonetheless, this is not yet a full solution, since the quality of the
resulting prediction sets can vary dramatically depending on the design ofC(x,u,τ ). In particular,
we recall the size and adaptiveness desiderata from Section 1—we want our uncertainty sets to be
as small as possible while faithfully articulating the instance-wise uncertainty of each test point. In
this section, we explicitly give our algorithm, which can be viewed as a special case of conformal
calibration with the uncertainty setsC designed to extract information from CNNs.
Our algorithm has three main ingredients. First, for a feature vector x, the base model computes
class probabilities ˆπx∈ Rk, and we order the classes from most probable to least probable. Then,
we add a regularization term to promote small predictive sets. Finally, we conformally calibrate the
penalized prediction sets to guarantee coverage on future test points.
Formally, letρx(y) =∑Ky′=1 ˆπx(y′)I{ˆπx(y′)&gt;ˆπx(y)} be the total probability mass of the set of labels
that are more likely than y. These are all the labels that will be included before y is included. In
addition, letox(y) =|{y′∈Y : ˆπx(y′)≥ ˆπx(y)}| be the ranking ofy among the label based on the
probabilities ˆπ. For example, ify is the third most likely label, thenox(y) = 3.1 We take
C∗(x,u,τ ) :={y : ρx(y) + ˆπx(y)·u +λ· (ox(y)−kreg)+| {z }
regularization
≤τ
}
, (4)
where (z)+ denotes the positive part of z andλ,kreg≥ 0 are regularization hyperparameters that
are introduced to encourage small set sizes. See Figure 3 for a visualization of a RAPS predictive
set and Appendix E for a discussion of how to selectkreg andλ.
Since this is the heart of our proposal, we carefully parse each term. First, the ρx(y) term increases
asy ranges from the most probable to least probable label, so our sets will prefer to include they that
are predicted to be the most probable. The second term, ˆπx(y)·u, is a randomized term to handle
the fact that the value will jump discretely with the inclusion of each newy. The randomization term
can never impact more than one value of y: there is at most one value of y such thaty∈C (x, 0,τ )
buty /∈C (x, 1,τ ). These ﬁrst two terms can be viewed as the CDF transform after arranging the
classes from most likely to least likely, randomized in the usual way to result in a continuous uniform
random variable (cf. Romano et al., 2020). We discuss randomization further in Appendix B.
Lastly, the regularization promotes small set sizes: for values ofy that occur farther down the ordered
list of classes, the termλ· (ox(y)−kreg)+ makes that value ofy require a higher value ofτ before
1For ease of notation, we assume distinct probabilities. Else, label-ordering ties should be broken randomly.
5
PDF PAGE 15
 λ = 0 λ = 0.001 λ = 0.01 λ = 0.1 λ = 1
difﬁculty count cvg sz cvg sz cvg sz cvg sz cvg sz
1 15668 0.95 5.2 0.95 3.8 0.96 2.5 0.97 2.0 0.98 2.0
2 to 3 2578 0.78 15.7 0.78 10.5 0.80 6.0 0.84 3.9 0.86 3.6
4 to 6 717 0.68 31.7 0.68 19.7 0.70 9.7 0.71 5.3 0.64 4.4
7 to 10 334 0.63 41.0 0.63 24.9 0.60 11.6 0.22 5.7 0.00 4.5
11 to 100 622 0.55 57.8 0.51 34.1 0.26 14.7 0.00 6.4 0.00 4.6
101 to 1000 81 0.23 96.7 0.00 51.6 0.00 19.1 0.00 7.1 0.00 4.7
Table 8: Coverage and size conditional on difﬁculty.We report coverage and size ofRAPS sets using ResNet-
152 withkreg = 5 and varyingλ (recall thatλ = 0 is the APS procedure). The desired coverage level is 90%.
The ‘difﬁculty’ is the ranking of the true class’s estimated probability.
stabilize the sets. As a ﬁnal word on Table 8, notice that as λ increases, coverage improves for the
more common medium-difﬁculty examples, although not for very rare and difﬁcult ones.
E C HOOSING kreg AND λ TO OPTIMIZE SET SIZE
This section describes two procedures for picking kreg andλ that optimize for set size or adaptive-
ness, outperforming APS in both cases.
Algorithm 4 Adaptive Fixed-K
Input: α; I ∈{ 1,...,K}n×K, and y∈{ 0, 1,...,K}n corresponding respectively to the classes
from highest to lowest estimated probability mass, and labels for each of n examples in the
dataset
1: procedure GET-KSTAR (α,I,y)
2: fori∈{ 1,··· ,n} do
3: Li←j such thatIi,j =yi
4: ˆk∗← the⌈(1−α)(1 +n)⌉ largest value in{Li}ni=1
5: return ˆk∗
Output: The estimate of the smallest ﬁxed size set that achieves coverage, ˆk∗
To produce Tables 1, 6, 2, and 7, we chosekreg andλ adaptively. This required an extra data splitting
step, where a small amount of tuning data
{
xi,yi
}m
i=1 were used to estimatek∗, and thenkreg is settok∗. Takingm≈ 1000 was sufﬁcient, since the algorithm is fairly insensitive tokreg (see Table 3).
Then, ˆk∗ was calculated with Algorithm 4. We produced the Imagenet V2 tables with m = 1000
and the Imagenet tables withm = 10000.
After choosing ˆk∗, we choseλ to have small set size. We used the same tuning data to pickˆk∗ andλ
for simplicity (this does not invalidate our coverage guarantee since conformal calibration still uses
fresh data). A coarse grid search on λ sufﬁced, since small parameter variations have little impact
on RAPS. For example, we chose theλ∈{ 0.001, 0.01, 0.1, 0.2, 0.5} that achieved the smallest size
on the m holdout samples in order to produce Tables 1, 6, 2, and 7. We include a subroutine that
automatically chooses ˆk∗ andλ to optimize size in our GitHub codebase.
F C OMPARISON WITH LEAST AMBIGUOUS SET-VALUED CLASSIFIERS
In this section, we compare RAPS to the Least Ambiguous Set-valued Classiﬁer ( LAC) method
introduced in ?, an alternative conformal procedure that is designed to have small sets. The LAC
method provable gives the smallest possible average set size in the case where the input probabilities
are correct, with the idea that these sets should be small even when the estimated probabilities are
only approximately correct. In the notation of this paper, the LAC method considers nested sets of
the following form:
CLAC(x,τ ) :={y : ˆπx(y)≥ 1−τ},
which can be calibrated using as before in using ˆτccal from Eq. (3).
15
PDF PAGE 16
 We ﬁrst compare naive, APS, RAPS, and LAC in terms of power and coverage in Table 9. In this
experiment, we tuned RAPS to have small set size as described in Appendix E. We see thatLAC also
achieves correct coverage, as expected since it is a conformal method and satisﬁes the guarantee
from Theorem 1. We further see that it has systematically smaller sets that RAPS, although the
difference is slight compared to the gap between APS and RAPS or APS and LAC.
We next compare RAPS to LAC in terms of adaptiveness, tuning RAPS as in Section 4.2. First, in
Table 10, we report on the coverage of LAC for images of different difﬁculties, and see that LAC
has dramatically worse coverage for hard images than for easy ones. Comparing this to RAPS in
Table 8, we see that RAPS also has worse coverage for more difﬁcult images, although the gap is
much smaller for RAPS. Next, in Table 11, we report on the SSCV metric for of adaptiveness (and
conditional coverage) for APS, RAPS, and LAC. We ﬁnd that APS and RAPS have much better
adaptiveness than LAC, with RAPS being the overall winner. The results of all of these comparisons
are expected: LAC is not targetting adpativeness and instead trying to achieve the smallest possible
set size. It succeeds at its goal, sacriﬁcing adaptiveness to do so.
16
TUTORIAL PAGE 2
 Contents
1 Conformal Prediction 4
1.1 Instructions for Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2 Examples of Conformal Procedures 6
2.1 Classiﬁcation with Adaptive Prediction Sets . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.2 Conformalized Quantile Regression . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2.3 Conformalizing Scalar Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.1 The Estimated Standard Deviation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.3.2 Other 1-D Uncertainty Estimates . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.4 Conformalizing Bayes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Evaluating Conformal Prediction 11
3.1 Evaluating Adaptivity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 The Eﬀect of the Size of the Calibration Set . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
3.3 Checking for Correct Coverage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
4 Extensions of Conformal Prediction 16
4.1 Group-Balanced Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4.2 Class-Conditional Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Conformal Risk Control . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Outlier Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
4.5 Conformal Prediction Under Covariate Shift . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
4.6 Conformal Prediction Under Distribution Drift . . . . . . . . . . . . . . . . . . . . . . . . . . 21
5 Worked Examples 23
5.1 Multilabel Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.2 Tumor Segmentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
5.3 Weather Prediction with Time-Series Distribution Shift . . . . . . . . . . . . . . . . . . . . . 24
5.4 Toxic Online Comment Identiﬁcation via Outlier Detection . . . . . . . . . . . . . . . . . . . 25
5.5 Selective Classiﬁcation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
6 Full conformal prediction 27
6.1 Full Conformal Prediction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.2 Cross-Conformal Prediction, CV+, and Jackknife+ . . . . . . . . . . . . . . . . . . . . . . . . 28
7 Historical Notes on Conformal Prediction 28
A Distribution-Free Control of General Risks 39
A.1 Instructions for Learn then Test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
2
TUTORIAL PAGE 12
 1. Evaluating adaptivity. It is extremely important to keep in mind that the conformal prediction
procedure with the smallest average set size is not necessarily the best. A good conformal prediction
procedure will give small sets on easy inputs and large sets on hard inputs in a way that faithfully
reﬂects the model’s uncertainty. This adaptivity is not implied by conformal prediction’s coverage
guarantee, but it is non-negotiable in practical deployments of conformal prediction. We will formalize
adaptivity, explore its consequences, and suggest practical algorithms for evaluating it.
2. Correctness checks. Correctness checks help you test whether you’ve implemented conformal predic-
tion correctly. We will empirically check that the coverage satisﬁes Theorem 1. Rigorously evaluating
whether this property holds requires a careful accounting of the ﬁnite-sample variability present with
real datasets. We develop explicit formulae for the size of the benign ﬂuctuations—if one observes
deviations from 1−α in coverage that are larger than these formulae dictate, then there is a problem
with the implementation.
Many of the evaluations we suggest are computationally intensive, and require running the entire confor-
mal procedure on diﬀerent splits of data at least 100 times. Na¨ ıve implementations of these evaluations can
be slow when the score takes a long time to compute. With some simple computational tricks and strategic
caching, we can speed this process up by orders of magnitude. Therefore to aid the reader, we intersperse
the mathematical descriptions with code to eﬃciently implement these computations.
3.1 Evaluating Adaptivity
Although any conformal procedure yields prediction intervals that satisfy (1), there are many such procedures,
and they diﬀer in other important ways. In particular, a key design consideration for conformal prediction
is adaptivity: we want the procedure to return larger sets for harder inputs and smaller sets for easier
inputs. While most reasonable conformal procedures will satisfy this to some extent, we now discuss precise
metrics for adaptivity that allow the user to check a conformal procedure and to compare multiple alternative
conformal procedures.
Set size. The ﬁrst step is to plot histograms of set sizes. This histogram helps us in two ways. Firstly,
a large average set size indicates the conformal procedure is not very precise, indicating a possible problem
with the score or underlying model. Secondly, the spread of the set sizes shows whether the prediction sets
properly adapt to the diﬃculty of examples. A wider spread is generally desirable, since it means that the
procedure is eﬀectively distinguishing between easy and hard inputs.
set size
#
set size
#
It can be tempting to stop evaluations after plotting the coverage and set size, but certain important
questions remain unanswered. A good spread of set sizes is generally better, but it does not necessarily
indicate that the sets adapt properly to the diﬃculty of X. Above seeing that the set sizes have dynamic
range, we will need to verify that large sets occur for hard examples. We next formalize this notion and give
metrics for evaluating it.
Conditional coverage. Adaptivity is typically formalized by asking for the conditional coverage [14]
property:
P [Ytest∈C (Xtest)|Xtest]≥ 1−α. (7)
12

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Locating tutorial source**</reasoning></content>
  <tool_call id="call_64d8a3f3e3ad487dbbebdc908bb38436" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2107.07511.pdf\"); [print(\"=== PDF PAGE\",p,\"===\\n\",r.pages[p-1].extract_text()) for p in [4,5,13,14,15,16,17,20,50]]'", "timeout": 90}</tool_call>
</message>
<message type="tool">=== PDF PAGE 4 ===
 Figure 1: Prediction set examples on Imagenet. We show three progressively more diﬃcult examples
of the class fox squirrel and the prediction sets (i.e., C(Xtest)) generated by conformal prediction.
1 Conformal Prediction
Conformal prediction [1–3] (a.k.a. conformal inference) is a straightforward way to generate prediction sets
for any model. We will introduce it with a short, pragmatic image classiﬁcation example, and follow up in
later paragraphs with a general explanation. The high-level outline of conformal prediction is as follows.
First, we begin with a ﬁtted predicted model (such as a neural network classiﬁer) which we will call ˆf. Then,
we will create prediction sets (a set of possible labels) for this classiﬁer using a small amount of additional
calibration data—we will sometimes call this the calibration step.
Formally, suppose we have images as input and they each contain one of K classes. We begin with
a classiﬁer that outputs estimated probabilities (softmax scores) for each class: ˆf(x)∈ [0, 1]K. Then, we
reserve a moderate number (e.g., 500) of fresh i.i.d. pairs of images and classes unseen during training,
(X1,Y 1),..., (Xn,Yn), for use as calibration data. Using ˆf and the calibration data, we seek to construct a
prediction set of possible labels C(Xtest)⊂{ 1,...,K } that is valid in the following sense:
1−α≤ P(Ytest∈C (Xtest))≤ 1−α + 1n + 1, (1)
where (Xtest,Y test) is a fresh test point from the same distribution, and α∈ [0, 1] is a user-chosen error rate.
In words, the probability that the prediction set contains the correct label is almost exactly 1 −α; we call
this property marginal coverage, since the probability is marginal (averaged) over the randomness in the
calibration and test points. See Figure 1 for examples of prediction sets on the Imagenet dataset.
To constructC from ˆf and the calibration data, we will perform a simple calibration step that requires
only a few lines of code; see the right panel of Figure 2. We now describe the calibration step in more detail,
introducing some terms that will be helpful later on. First, we set the conformal scoresi = 1− ˆf(Xi)Yi to be
one minus the softmax output of the true class. The score is high when the softmax output of the true class
is low, i.e., when the model is badly wrong. Next comes the critical step: deﬁne ˆq to be the⌈(n+1)(1−α)⌉/n
empirical quantile of s1,...,s n, where⌈·⌉ is the ceiling function (ˆq is essentially the 1−α quantile, but with
a small correction). Finally, for a new test data point (where Xtest is known but Ytest is not), create a
prediction setC(Xtest) ={y : ˆf(Xtest)y≥ 1− ˆq} that includes all classes with a high enough softmax output
(see Figure 2). Remarkably, this algorithm gives prediction sets that are guaranteed to satisfy (1), no matter
what (possibly incorrect) model is used or what the (unknown) distribution of the data is.
true class
class
softmax output
#
scores,       class
softmax output
(1) compute scores
on holdout data
(2) get quantile (3) construct
prediction set
# 1: get conformal scores. n = calib_Y.shape[0]
cal_smx = model(calib_X).softmax(dim=1).numpy()
cal_scores = 1-cal_smx[np.arange(n),cal_labels]
# 2: get adjusted quantile
q_level = np.ceil((n+1)*(1-alpha))/n
qhat = np.quantile(cal_scores, q_level, method='higher')
val_smx = model(val_X).softmax(dim=1).numpy()
prediction_sets = val_smx &gt;= (1-qhat) # 3: form prediction sets
Figure 2: Illustration of conformal prediction with matching Python code.
4
=== PDF PAGE 5 ===
 Remarks
Let us think about the interpretation of C. The function C is set-valued—it takes in an image, and it
outputs a set of classes as in Figure 1. The model’s softmax outputs help to generate the set. This method
constructs a diﬀerent output set adaptively to each particular input . The sets become larger when the model
is uncertain or the image is intrinsically hard. This is a property we want, because the size of the set gives you
an indicator of the model’s certainty. Furthermore, C(Xtest) can be interpreted as a set of plausible classes
that the image Xtest could be assigned to. Finally, C is valid, meaning it satisﬁes (1). 1 These properties of
C translate naturally to other machine learning problems, like regression, as we will see.
With an eye towards generalization, let us review in detail what happened in our classiﬁcation problem.
To begin, we were handed a model that had an inbuilt, but heuristic, notion of uncertainty: softmax outputs.
The softmax outputs attempted to measure the conditional probability of each class; in other words, the
jth entry of the softmax vector estimated P(Y = j| X = x), the probability of class j conditionally on
an input image x. However, we had no guarantee that the softmax outputs were any good; they may have
been arbitrarily overﬁt or otherwise untrustworthy. Therefore, instead of taking the softmax outputs at face
value, we used the holdout set to adjust for their deﬁciencies.
The holdout set contained n≈ 500 fresh data points that the model never saw during training, which
allowed us to get an honest appraisal of its performance. The adjustment involved computing conformal
scores, which grow when the model is uncertain, but are not valid prediction intervals on their own. In our
case, the conformal score was one minus the softmax output of the true class, but in general, the score can
be any function of x and y. We then took ˆq to be roughly the 1−α quantile of the scores. In this case, the
quantile had a simple interpretation—when setting α = 0.1, at least 90% of ground truth softmax outputs
are guaranteed to be above the level 1 − ˆq (we prove this rigorously in Appendix D). Taking advantage of
this fact, at test-time, we got the softmax outputs of a new image Xtest and collected all classes with outputs
above 1− ˆq into a prediction setC(Xtest). Since the softmax output of the new true class Ytest is guaranteed
to be above 1− ˆq with probability at least 90%, we ﬁnally got the guarantee in Eq. (1).
1.1 Instructions for Conformal Prediction
As we said during the summary, conformal prediction is not speciﬁc to softmax outputs or classiﬁcation
problems. In fact, conformal prediction can be seen as a method for taking any heuristic notion of
uncertainty from any model and converting it to a rigorous one (see the diagram below). Conformal pre-
diction does not care if the underlying prediction problem is discrete/continuous or classiﬁcation/regression.
Heuristic
uncertainty
(per input)
Rigorous
uncertainty
(per input)
conformal
prediction
We next outline conformal prediction for a general input x and output y (not necessarily discrete).
1. Identify a heuristic notion of uncertainty using the pre-trained model.
2. Deﬁne the score function s(x,y )∈ R. (Larger scores encode worse agreement between x and y.)
3. Compute ˆq as the ⌈(n+1)(1−α)⌉n quantile of the calibration scores s1 =s(X1,Y 1),...,s n =s(Xn,Yn).
4. Use this quantile to form the prediction sets for new examples:
C(Xtest) ={y :s(Xtest,y )≤ ˆq}. (2)
As before, these sets satisfy the validity property in (1), for any (possibly uninformative) score function and
(possibly unknown) distribution of the data. We formally state the coverage guarantee next.
1Due to the discreteness of Y , a small modiﬁcation involving tie-breaking is needed to additionally satisfy the upper bound
(see [4] for details; this randomization is usually ignored in practice). We will henceforth ignore such tie-breaking.
5
=== PDF PAGE 13 ===
 That is, for every value of the input Xtest, we seek to return prediction sets with 1 −α coverage. This is
a stronger property than the marginal coverage property in (1) that conformal prediction is guaranteed to
achieve—indeed, in the most general case, conditional coverage is impossible to achieve [14]. In other words,
conformal procedures are not guaranteed to satisfy (7), so we must check how close our procedure comes to
approximating it.
The diﬀerence between marginal and conditional coverage is subtle but of great practical importance, so
we will spend some time think about the diﬀerences here. Imagine there are two groups of people, group A
and group B, with frequencies 90% and 10%. The prediction sets always cover Y among people in group A
and never cover Y when the person comes from group B. Then the prediction sets have 90% coverage, but
not conditional coverage. Conditional coverage would imply that the prediction sets cover Y at least 90% of
the time in both groups. This is necessary, but not suﬃcient; conditional coverage is a very strong property
that states the probability of the prediction set needs to be ≥ 90% for a particular person . In other words,
for any subset of the population, the coverage should be ≥ 90%. See Figure 10 for a visualization of the
diﬀerence between conditional and marginal coverage.
errors by group
regression
no coverage
5% coverage
Group 1 Group 1 Group 1Group 2 Group 2 Group 2
marginal conditional
14% coverage 100% coverage 80% coverage 90% coverage 90% coverage
correctly covered example
incorrectly covered example
Figure 10: Prediction sets with various notions of coverage: no coverage, marginal coverage, or
conditional coverage (at a level of 90%). In the marginal case, all the errors happen in the same groups and
regions in X-space. Conditional coverage disallows this behavior, and errors are evenly distributed.
Feature-stratiﬁed coverage metric. As a ﬁrst metric for conditional coverage, we will formalize the
example we gave earlier, where coverage is unequal over some groups. The reader can think of these groups
as discrete categories, like race, or as a discretization of continuous features, like age ranges. Formally,
suppose we have features X(val)i,1 that take values in{1,...,G } for some G. (Here, i = 1,...,n val indexes the
example in the validation set, and the ﬁrst coordinate of each feature is the group.) Let Ig⊂{ 1,...,n val}
be the set of observations such that X(val)i,1 =g for g = 1,...,G . Since conditional coverage implies that the
procedure has the same coverage for all values of Xtest, we use the following measure:
FSC metric : min
g∈{1,...,G}
1
|Ig|
∑
i∈Ig
1
{
Y (val)i ∈C(X(val)i )}
In words, this is the observed coverage among all instances where the discrete feature takes the value g. If
conditional coverage were achieved, this would be 1 −α, and values farther below 1 −α indicate a greater
violation of conditional coverage. Note that this metric can also be used with a continuous feature by binning
the features into a ﬁnite number of categories.
13
=== PDF PAGE 14 ===
 Size-stratiﬁed coverage metric. We next consider a more general-purpose metric for how close a confor-
mal procedure comes to satisfying (7), introduced in [4]. First, we discretize the possible cardinalities ofC(x),
into G bins, B1,...,B G. For example, in classiﬁcation we might divide the observations into three groups,
depending on whetherC(x) has one element, two elements, or more than two elements. LetIg⊂{ 1,...,n val}
be the set of observations falling in bin g for g = 1,...,G . Then we consider the following
SSC metric : min
g∈{1,...,G}
1
|Ig|
∑
i∈Ig
1
{
Y (val)i ∈C(X(val)i )}
In words, this is the observed coverage for all units for which the set size |C(x)| falls into bin g. As before,
if conditional coverage were achieved, this would be 1−α, and values farther below 1−α indicate a greater
violation of conditional coverage. Note that this is the same expression as for the FSC metric, except that
the deﬁnition ofIg has changed. Unlike the FSC metric, the user does not have to deﬁne an important set
of discrete features a-priori—it is a general metric that can apply to any example.
See [15] and [16] for additional metrics of conditional coverage.
3.2 The Eﬀect of the Size of the Calibration Set
We ﬁrst pause to discuss how the size of the calibration set aﬀects conformal prediction. We consider this
question for two reasons. First, the user must choose this for a practical deployment. Roughly speaking, our
conclusion will that be choosing a calibration set of size n = 1000 is suﬃcient for most purposes. Second, the
size of the calibration set is one source of ﬁnite-sample variability that we will need to analyze to correctly
check the coverage. We will build on the results here in the next section, where we give a complete description
of how to check coverage in practice.
How does the size of the calibration set, n, aﬀect conformal prediction? The coverage guarantee in (1)
holds for any n, so we can see that our prediction sets have coverage at least 1 −α even with a very small
calibration set. Intuitively, however, it may seem that largern is better, and leads to more stable procedures.
This intuition is correct, and it explains why using a larger calibration set is beneﬁcial in practice. The details
are subtle, so we carefully work through them here.
The key idea is that the coverage of conformal prediction conditionally on the calibration set is a random
quantity. That is, if we run the conformal prediction algorithm twice, each time sampling a new calibration
dataset, then check the coverage on an inﬁnite number of validation points, those two numbers will not be
equal. The coverage property in (1) says that coverage will be at least 1−α on average over the randomness
in the calibration set, but with any one ﬁxed calibration set, the coverage on an inﬁnite validation set will
be some number that is not exactly 1 −α. Nonetheless, we can choose n large enough to control these
ﬂuctuations in coverage by analyzing its distribution.
In particular, the distribution of coverage has an analytic form, ﬁrst introduced by Vladimir Vovk in [14],
namely,
P
(
Ytest∈C (Xtest)
⏐⏐{(Xi,Yi)}ni=1)∼ Beta (n + 1−l,l ),
where
l =⌊(n + 1)α⌋.
Notice that the conditional expectation above is the coverage with an inﬁnite validation data set, holding the
calibration data ﬁxed. A simple proof of this fact is available in [14]. We plot the distribution of coverage
for several values of n in Figure 11.
Inspecting Figure 11, we see that choosing n = 1000 calibration points leads to coverage that is typically
between .88 and .92, hence our rough guideline of choosing about 1000 calibration points. More formally,
we can compute exactly the number of calibration points n needed to achieve a coverage of 1 −α±ϵ with
probability 1−δ. Again, the average coverage is always at least 1 −α; the parameter δ controls the tail
probabilities of the coverage conditionally on the calibration data. For any δ, the required calibration set
size n can be explicitly computed from a simple expression, and we report on several values in Table 1 for
the reader’s reference. Code allowing the user to produce results for any choice of n andα accompanies the
table.
14
=== PDF PAGE 15 ===
 0.82 0.84 0.86 0.88 0.90 0.92 0.94 0.96 0.98
Distribution of coverage (infinite validation set)
n=100
n=1000
n=10000
1
Figure 11: The distribution of coverage with an inﬁnite validation set is plotted for diﬀerent values of
n with α = 0.1. The distribution converges to 1−α with rateO
(
n−1/2).
ϵ 0.1 0.05 0.01 0.005 0.001
n(ϵ) 22 102 2491 9812 244390
Table 1: Calibration set size n(ϵ) required for coverage slack ϵ with δ = 0.1 and α = 0.1.
3.3 Checking for Correct Coverage
As an obvious diagnostic, the user will want to assess whether the conformal procedure has the correct
coverage. This can be accomplished by running the procedure over R trials with new calibration and
validation sets, and then calculating the empirical coverage for each,
Cj = 1nval
nval∑
i=1
1
{
Y (val)i,j ∈C j
(
X(val)i,j
)}
, for j = 1,...,R,
where nval is the size of the validation set, ( X(val)i,j ,Y (val)i,j ) is the ith validation example in trial j, andCj is
calibrated using the calibration data from the jth trial. A histogram of the Cj should be centered at roughly
1−α, as in Figure 11. Likewise, the mean value,
C = 1R
R∑
j=1
Cj,
should be approximately 1−α.
With real datasets, we only have n +nval data points total to evaluate our conformal algorithm and
therefore cannot draw new data for each of the R rounds. So, we compute the coverage values by randomly
splitting the n +nval data points R times into calibration and validation datasets, then running conformal.
Notice that rather than splitting the data points themselves many times, we can instead ﬁrst cache all
conformal scores and then compute the coverage values over many random splits, as in the code sample in
Figure 12.
If properly implemented, conformal prediction is guaranteed to satisfy the inequality in (1). However, if
the reader sees minor ﬂuctuations in the observed coverage, they may not need to worry: the ﬁniteness of
n, nval, and R can lead to benign ﬂuctuations in coverage which add some width to the Beta distribution
in Figure 11. Appendix C gives exact theory for analyzing the mean and standard deviation of C. From
this, we will be able to tell if any deviation from 1 −α indicates a problem with the implementation, or
15
=== PDF PAGE 16 ===
 try: # try loading the scores first
scores = np.load('scores.npy')
except:
# X and Y have n + n_val rows each
scores = get_scores(X,Y)
np.save(scores, 'scores.npy')
# calculate the coverage R times and store in list
coverages = np.zeros((R,))
for r in range(R):
np.random.shuffle(scores) # shuffle
calib_scores, val_scores = (scores[:n],scores[n:]) # split
qhat = np.quantile(calib_scores, np.ceil((n+1)*(1-alpha)/n), method='higher') # calibrate
coverages[r] = (val_scores &lt;= qhat).astype(float).mean() # see caption
average_coverage = coverages.mean() # should be close to 1-alpha
plt.hist(coverages) # should be roughly centered at 1-alpha
Figure 12: Python code for computing coverage with eﬃcient score caching. Notice that from the
expression for conformal sets in (2), a validation point is covered if and only if s(X,Y )≤ ˆq, which is how
the third to last line is succinctly computing the coverage.
if it is benign. Code for checking the coverage at all diﬀerent values of n, nval, and R is available in the
accompanying Jupyter notebook of Figure 12.
4 Extensions of Conformal Prediction
At this point, we have seen the core of the matter: how to construct prediction sets with coverage in
any standard supervised prediction problem. We now broaden our horizons towards prediction tasks with
diﬀerent structure, such as side information, covariate shift, and so on. These more exotic problems arise
quite frequently in the real world, so we present practical conformal algorithms to address them.
4.1 Group-Balanced Conformal Prediction
In certain settings, we might want prediction intervals that have equal error rates across certain subsets of
the data. For example, we may require our medical classiﬁer to have coverage that is correct for all racial
and ethnic groups. To formalize this, we suppose that the ﬁrst feature of our inputs, Xi,1, i = 1,...,n takes
values in some discrete set {1,...,G} corresponding to categorical groups. We then ask for group-balanced
coverage:
P (Ytest∈C (Xtest)|Xtest,1 =g)≥ 1−α, (8)
for all groups g∈{ 1,...,G }. In words, this means we have a 1−α coverage rate for all groups. Notice that
the group output could be a post-processing of the original features in the data. For example, we might bin
the values of Xtest into a discrete set.
Recall that a standard application of conformal prediction will not necessarily yield coverage within each
group simultaneously—that is, (8) may not be satisﬁed. We saw an example in Figure 10; the marginal
guarantee from normal conformal prediction can still be satisﬁed even if all errors happen in one group.
In order to achieve group-balanced coverage, we will simply run conformal prediction seperately for each
group, as visualized below.
16
=== PDF PAGE 17 ===
 Making this formal, given a conformal score function s, we stratify the scores on the calibration set by
group,
s(g)i =s(Xj,Yj), where Xj,1 is the ith occurrence of group g.
Then, within each group, we calculate the conformal quantile
ˆq(g) = Quantile
(
s1,...,s n(g);
⌈
(n(g) + 1)(1−α)⌉
n(g)
)
, where n(g) is the number of examples of group g.
Finally, we form prediction sets by ﬁrst picking the relevant quantile,
C(x) =
{
y :s(x,y )≤ ˆq(x1)
}
.
That is, for a point x that we see falls in group x1, we use the threshold ˆq(x1) to form the prediction set, and
so on. This choice of C satisﬁes (8), as was ﬁrst documented by Vovk in [14].
Proposition 1 (Error control guarantee for group-balanced conformal prediction) . Suppose (X1,Y 1),...,
(Xn,Yn), (Xtest,Ytest) are an i.i.d. sample from some distribution. Then the set C deﬁned above satisﬁes the
error control property in (8).
4.2 Class-Conditional Conformal Prediction
In classiﬁcation problems, we might similarly ask for coverage onevery ground truth class. For example, if we
had a medical classiﬁer assigning inputs to class normal or class cancer, we might ask that the prediction sets
are 95% accurate both when the ground truth is class cancer and also when the ground truth is class normal.
Formally, we return to the classiﬁcation setting, where Y ={1,...,K}. We seek to achieve class-balanced
coverage,
P (Ytest∈C (Xtest)|Ytest =y)≥ 1−α, (9)
for all classes y∈{ 1,...,K }.
To achieve class-balanced coverage, we will calibrate within each class separately. The algorithm will be
similar to the group-balanced coverage of Section 4.1, but we must modify it because we do not know the
correct class at test time. (In contrast, in Section 4.1, we observed the group information Xtest,1 as an input
feature.) See the visualization below.
17
=== PDF PAGE 20 ===
 Proposition 3 (Error control guarantee for outlier detection). SupposeX1,...,X n,X test are an i.i.d. sam-
ple from some distribution. Then the set C deﬁned above satisﬁes the error control property in (14).
As with standard conformal prediction, the score function is very important for the method to perform
well—that is, to be eﬀective at ﬂagging outliers. Here, we wish to choose the score function to eﬀectively
distinguish the type of outliers that we expect to see in the test data from the clean data. The general
problem of training models to distinguish outliers is sometimes called anomaly detection, novelty detection,
or one-class classiﬁcation, and there are good out-of-the box methods for doing this; see [19] for an overview
of outlier detection. Conformal outlier detection can also be seen as a hypothesis testing problem; points
that are rejected as outliers have a p-value less thanalpha for the null hypothesis of exchangeability with the
calibration data. This interpretation is closely related to the classical permutation test [20, 21]. See [22–24]
for more on this interpretation and other statistical properties of conformal outlier detection.
4.5 Conformal Prediction Under Covariate Shift
All previous conformal methods rely on Theorem 1, which assumes that the incoming test points come from
the same distribution as the calibration points. However, past data is not necessarily representative of future
data in practice.
One type of distribution shift that conformal prediction can handle is covariate shift. Covariate shift
refers to the situation where the distribution of Xtest changes fromP toPtest, but the relationship between
Xtest and Ytest, i.e. the distribution of Ytest|Xtest, stays ﬁxed.
Imagine our calibration features {Xi}ni=1 are drawn independently from P but our test feature Xtest is
drawn fromPtest. Then, there has been a covariate shift, and the data are no longer i.i.d. This problem is
common in the real world. For example,
• You are trying to predict diseases from MRI scans. You conformalized on a balanced dataset of 50%
infants and 50% adults, but in reality, the frequency is 5% infants and 95% adults. Deploying the
model in the real world would invalidate coverage; the infants are over-represented in our sample, so
diseases present during infancy will be over-predicted. This was a covariate shift in age.
• You are trying to do instance segmentation, i.e., to segment each object in an image from the back-
ground. You collected your calibration images in the morning but seek to deploy your system in the
afternoon. The amount of sunlight has changed, and more people are eating lunch. This was a covariate
shift in the time of day.
To address the covariate shift from P toPtest, one can form valid prediction sets with weighted conformal
prediction, ﬁrst developed in [25].
In weighted conformal prediction, we account for covariate shift by upweighting conformal scores from
calibration points that would be more likely under the new distribution. We will be using the likelihood ratio
w(x) = dPtest(x)dP(x) ;
20
=== PDF PAGE 50 ===
 0.896 0.898 0.900 0.902 0.904
Distribution of C with n = 1000, nval = 1000
0.896 0.898 0.900 0.902 0.904
Distribution of C with n = 10000, nval = 10000
R = 100
R = 1000
R = 10000
Figure 26: The distribution of average empirical coverage over R trials with n calibration points
and nval validation points.
Furthermore, we can analytically reason about the tail properties of C. Since C is the average of R i.i.d.
beta-binomial random variables, its mean and standard deviation are
E
(
C
)
= 1− ln + 1 and
√
Var
(
C
)
=
√
l(n + 1−l)(n +nval + 1)
nvalR(n + 1)2(n + 2) =O
(
1√
R min(n,n val)
)
.
The best way for a practitioner to carefully debug their procedure is to compute C empirically, and then
cross-reference with Figure 26. We give code to simulate histograms with any n, R, and nval in the linked
notebook of Figure 26. If the simulated average empirical coverage does not align well with the coverage
observed on the real data, there is likely a problem in the conformal implementation.
D Theorem and Proof: Coverage Property of Conformal Predic-
tion
This is a standard proof of validity for split-conformal prediction ﬁrst appearing in [2], but we reproduce it
here for completeness. Let us begin with the lower bound.
Theorem D.1 (Conformal calibration coverage guarantee) . Suppose (Xi,Yi)i=1,...,n and (Xtest,Y test) are
i.i.d. Then deﬁne ˆq as
ˆq = inf
{
q :|{i :s(Xi,Yi)≤q}|n ≥⌈(n + 1)(1−α)⌉n }.
and the resulting prediction sets as
C(X) ={y :s(X,y )≤ ˆq}.
Then,
P
(
Ytest∈C (Xtest)
)
≥ 1−α.
This is the same coverage property as (1) in the introduction, but written more formally. As a technical
remark, the theorem also holds if the observations to satisfy the weaker condition of exchangeability; see [1].
Below, we prove the lower bound.
Proof of Theorem 1. Letsi =s(Xi,Yi) fori = 1,...,n andstest =s(Xtest,Y test). To avoid handling ties, we
consider the case where the si are distinct with probability 1. See [25] for a proof in the general case.
50

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Inspecting root list**</reasoning></content>
  <tool_call id="call_70f2393853084d2aa443fb87a9ea885b" name="execute">{"command": "python -c 'import json,hashlib,pathlib; root=pathlib.Path(\"/work\"); listing=json.loads((root/\"template/repo_contents.json\").read_text()); print([(x[\"name\"],x[\"sha\"]) for x in listing if x[\"name\"].startswith(\"iclr2027\")]); d=json.loads((root/\"template/iclr2027_contents.json\").read_text()); exec(\"for x in d:\\n p=root/\\\"template\\\"/x[\\\"path\\\"]; b=p.read_bytes(); git=hashlib.sha1(b\\\"blob \\\"+str(len(b)).encode()+b\\\"\\\\0\\\"+b).hexdigest(); print(x[\\\"path\\\"],\\\"SHA256\\\",hashlib.sha256(b).hexdigest(),\\\"matches_official_git_blob\\\",git==x[\\\"sha\\\"])\\n\"); print(\"ACCESS LOG\",(root/\"access_log.json\").read_text())'", "timeout": 30}</tool_call>
</message>
<message type="tool">[('iclr2027.zip', 'a079db54799d53378169a6e2c4f2105371522181'), ('iclr2027', '413badc001888f7d3277699d80e64f6c8fb38781')]
iclr2027/fancyhdr.sty SHA256 b56ec4434b9f4607529a4b23dc68ad8d4b94f1f631c8cddaf7da78140d53a5ea matches_official_git_blob True
iclr2027/iclr2027_conference.bib SHA256 cdd86e7d4c31854dcf2145871657c944588a6d44c3b72e160ff4baa8df1a52fb matches_official_git_blob True
iclr2027/iclr2027_conference.bst SHA256 2d67552db7ed38ccfccb5957b52f95656e25c249724761d3cf5f7922ad1844c5 matches_official_git_blob True
iclr2027/iclr2027_conference.sty SHA256 797deef41724e93761426ac0cbcca46279a91cc650dd1f0ce76a4f08d2098ea6 matches_official_git_blob True
iclr2027/iclr2027_conference.tex SHA256 03e556d6e5593e498fd39f262ec2d184ebfe8693cbf47fb7cea3402d8d5166ac matches_official_git_blob True
iclr2027/math_commands.tex SHA256 90473c4d0542070db244cea73ef962d6cddc5b2a746757e6a40ddf5fdfb90ba9 matches_official_git_blob True
iclr2027/natbib.sty SHA256 88bc70c0e48461934cab5b2accef06b74a8b3ac45ad03ccd3f2a6b7e0d6d530d matches_official_git_blob True
ACCESS LOG [
  {
    "requested_url": "https://arxiv.org/pdf/2107.07511",
    "final_url": "https://arxiv.org/pdf/2107.07511",
    "status": 200,
    "bytes": 5360733,
    "sha256": "c69aa191d8363c25b36685db4adb7e6980e55ee39892fd3626206c16e1e0efa1",
    "path": "./literature/2107.07511.pdf",
    "utc": "2026-11-02T18:05:39.099243+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/1904.06019",
    "final_url": "https://arxiv.org/pdf/1904.06019",
    "status": 200,
    "bytes": 423685,
    "sha256": "d80dba944a136e075bbfe281009152ce42041e0a455f68f73684ace83cfc3fed",
    "path": "./literature/1904.06019.pdf",
    "utc": "2026-11-02T18:05:39.590307+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2009.14193",
    "final_url": "https://arxiv.org/pdf/2009.14193",
    "status": 200,
    "bytes": 1339455,
    "sha256": "ca78c0ab20b95151db93e75f0fed5ef88faf180023b80d36c9e671034bc43f85",
    "path": "./literature/2009.14193.pdf",
    "utc": "2026-11-02T18:05:40.183158+00:00"
  },
  {
    "requested_url": "https://arxiv.org/pdf/2402.10723",
    "final_url": "https://arxiv.org/pdf/2402.10723",
    "status": 200,
    "bytes": 1756530,
    "sha256": "ac4a42679abdeaff5cfbe6bb316ac60373dfd9eefc97afc9ce94eb4899c68d09",
    "path": "./literature/2402.10723.pdf",
    "utc": "2026-11-02T18:05:40.831276+00:00"
  },
  {
    "requested_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "final_url": "https://api.github.com/repos/ICLR/Master-Template/contents/",
    "status": 200,
    "bytes": 16961,
    "sha256": "dc54ed42f6d93f1f1debb1d044bf45a48b2e65cbc310f914f683f3b443061f07",
    "path": "./template/repo_contents.json",
    "utc": "2026-11-02T18:05:41.442059+00:00"
  },
  {
    "requested_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md",
    "final_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md",
    "status": 200,
    "bytes": 52,
    "sha256": "69fd79b87c37393ceb4e58ba897a26578e1384d890a09dce539aef6baaf455c1",
    "path": "/work/template/README.md",
    "utc": "2026-11-02T18:09:06.627454+00:00"
  },
  {
    "requested_url": "https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027",
    "final_url": "https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027",
    "status": 200,
    "bytes": 6179,
    "sha256": "88c68c47145b42b117fbcd853ca828ecbe69eb2f6492d6ac5808f5921d49a9bf",
    "path": "/work/template/iclr2027_contents.json",
    "utc": "2026-11-02T18:09:07.128471+00:00"
  },
  {
    "requested_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip",
    "final_url": "https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip",
    "status": 200,
    "bytes": 39348,
    "sha256": "0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e",
    "path": "/work/template/iclr2027.zip",
    "utc": "2026-11-02T18:09:07.593380+00:00"
  }
]

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Creating bibliography notes**</reasoning> <reasoning>**Checking author spellings**</reasoning></content>
  <tool_call id="call_9b2b6c0e18c948fd836f53bfbe8de062" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2402.10723.pdf\"); print(r.pages[0].extract_text()[:6000]); r=PdfReader(\"/work/literature/2009.14193.pdf\"); print(r.pages[0].extract_text()[:3000]); r=PdfReader(\"/work/literature/1904.06019.pdf\"); print(r.pages[0].extract_text()[:2200])'", "timeout": 60}</tool_call>
</message>
<message type="tool">CONFORMALIZED CREDAL SET PREDICTORS
A PREPRINT
Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2
1Institute of Informatics, LMU Munich, Germany
2Munich Center for Machine Learning (MCML), Germany
3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany
alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de
ABSTRACT
Credal sets are sets of probability distributions that are considered as candidates for an imprecisely
known ground-truth distribution. In machine learning, they have recently attracted attention as an
appealing formalism for uncertainty representation, in particular due to their ability to represent
both the aleatoric and epistemic uncertainty in a prediction. However, the design of methods for
learning credal set predictors remains a challenging problem. In this paper, we make use of conformal
prediction for this purpose. More specifically, we propose a method for predicting credal sets in the
classification task, given training data labeled by probability distributions. Since our method inherits
the coverage guarantees of conformal prediction, our conformal credal sets are guaranteed to be
valid with high probability (without any assumptions on model or distribution). We demonstrate the
applicability of our method to natural language inference, a highly ambiguous natural language task
where it is common to obtain multiple annotations per example.
Keywords Conformal Prediction · Uncertainty Representation · Credal Sets
1 Introduction
Representing and quantifying uncertainty is becoming increasingly important in machine learning (ML), particularly
as ML models are employed in safety-critical application domains such as medicine or autonomous driving. In such
domains, a distinction between so-called aleatoric uncertainty and epistemic uncertainty is often useful [Hora, 1996].
Broadly speaking, aleatoric uncertainty is due to the inherent randomness of the data-generating process, whereas
epistemic uncertainty stems from the learner’s lack of knowledge about the best predictive model. Thus, while the
former is irreducible, the latter can in principle be reduced through additional information, e.g., by gathering additional
data to learn from.
Representation of aleatoric and epistemic uncertainty requires formalism more expressive than standard probability
distributions [H¨ullermeier and Waegeman, 2021]. One such formalism which prevails in the recent ML literature is
second-order probability distributions. Essentially, in a classification setting, these are distributions over distributions
over classes. Models producing second-order distributions as predictions can be learned in a classical Bayesian way
[Kendall and Gal, 2017, Depeweg et al., 2018] or using more recent approaches such as evidential deep learning [Sensoy
et al., 2018]. Yet, approaches of that kind are not unproblematic and have been subject to criticism [Bengs et al., 2022,
2023]. Another formalism suitable for representing both types of uncertainty is the concept of a credal set, which is
well-established in the field of imprecise probability theory [Walley, 1991] and meanwhile also attracted attention in ML
[Shaker and H¨ullermeier, 2020, H¨ullermeier et al., 2022]. Credal sets are (convex) sets of probability distributions that
can be considered as candidates for an imprecisely known ground-truth distribution. Figure 1 shows examples of credal
sets in a three-class scenario, where the space of distributions can be visualized by the two-dimensional probability
simplex. Broadly speaking, the larger the credal set, the higher the epistemic uncertainty, and the more “in the middle”
the set is located, i.e., the closer it is to the uniform distribution, the higher the aleatoric uncertainty.
arXiv:2402.10723v1  [stat.ML]  16 Feb 2024
UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING
CONFORMAL PREDICTION
Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan
Department of Electrical Engineering and Computer Sciences
Department of Statistics
University of California, Berkeley
Berkeley, CA 94704, USA
{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu
ABSTRACT
Convolutional image classiﬁers can achieve high predictive accuracy, but quanti-
fying their uncertainty remains an unresolved challenge, hindering their deploy-
ment in consequential settings. Existing uncertainty quantiﬁcation techniques,
such as Platt scaling, attempt to calibrate the network’s probability estimates, but
they do not have formal guarantees. We present an algorithm that modiﬁes any
classiﬁer to output a predictive set containing the true label with a user-speciﬁed
probability, such as 90%. The algorithm is simple and fast like Platt scaling, but
provides a formal ﬁnite-sample coverage guarantee for every model and dataset.
Our method modiﬁes an existing conformal prediction algorithm to give more sta-
ble predictive sets by regularizing the small scores of unlikely classes after Platt
scaling. In experiments on both Imagenet and Imagenet-V2 with ResNet-152 and
other classiﬁers, our scheme outperforms existing approaches, achieving coverage
with sets that are often factors of 5 to 10 smaller than a stand-alone Platt scaling
baseline.
1 I NTRODUCTION
Imagine you are a doctor making a high-stakes medical decision based on diagnostic information
from a computer vision classiﬁer. What would you want the classiﬁer to output in order to make
the best decision? This is not a casual hypothetical; such classiﬁers are already used in medical
settings (e.g., Razzak et al., 2018; Lundervold &amp; Lundervold, 2019; Li et al., 2014). A maximum-
likelihood diagnosis with an accompanying probability may not be the most essential piece of in-
formation. To ensure the health of the patient, you must also rule in or rule out harmful diagnoses.
In other words, even if the most likely diagnosis is a stomach ache, it is equally or more important
to rule out stomach cancer. Therefore, you would want the classiﬁer to give you—in addition to
an estimate of the most likely outcome—actionable uncertainty quantiﬁcation, such as a set of pre-
dictions that provably covers the true diagnosis with a high probability (e.g., 90%). This is called
a prediction set (see Figure 1). Our paper describes a method for constructing prediction sets from
any pre-trained image classiﬁer that are formally guaranteed to contain the true class with the de-
sired probability, relatively small, and practical to implement. Our method modiﬁes a conformal
predictor (V ovk et al., 2005) given in Romano et al. (2020) for the purpose of modern image classi-
ﬁcation in order to make it more stable in the presence of noisy small probability estimates. Just as
importantly, we provide extensive evaluations and code for conformal prediction in
Conformal Prediction Under Covariate Shift
Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas
Abstract
We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a
weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in
which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is
known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).
Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a
certain weighted notion of exchangeability. We discuss other potential applications of our new conformal methodology,
including latent variable and missing data problems.
1 Introduction
Let (Xi,Yi)∈ Rd× R,i = 1,...,n denote training data that is assumed to be i.i.d. from an arbitrary distributionP .
Given a desired coverage rate 1−α∈ (0, 1), consider the problem of constructing a band ˆCn : Rd→{ subsets of R},
based on the training data such that, for a new i.i.d. point (Xn+1,Yn+1),
P
{
Yn+1∈ ˆCn(Xn+1)
}
≥ 1−α, (1)
where this probability is taken over then + 1 points (Xi,Yi),i = 1,...,n + 1 (then training points and the test point).
Crucially, we will require (1) to hold with no assumptions whatsoever on the common distributionP .
Conformal prediction, a framework pioneered by Vladimir V ovk and colleagues in the 1990s, provides a means for
achieving this goal, relying only on exchangeablility of the training and test data. The deﬁnitive reference is the book
by V ovk et al. (2005); see also Shafer and V ovk (2008); V ovk et al. (2009); V ovk (2013); Burnaev and V ovk (2014), and
http://www.alrw.net for an often-updated list of conformal prediction work by V ovk and colleagues. Moreover,
we refer to Lei and Wasserman (2014); Lei et al. (2018) for recent developments in the areas of nonparametric and
high-dimensional regression. In this work, we extend conformal prediction beyond the setting of exchangeable data,
allowing for provably valid inference even when the 

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking bibliographic versions**</reasoning></content>
  <tool_call id="call_8dd2b372762d4e45bcf9017d1e7a157e" name="execute">{"command": "python -c 'from pypdf import PdfReader; ids=[\"2107.07511\",\"1904.06019\",\"2009.14193\",\"2402.10723\"]; exec(\"for id in ids:\\n r=PdfReader(\\\"/work/literature/\\\"+id+\\\".pdf\\\"); txt=r.pages[0].extract_text(); print(id,\\\"pages\\\",len(r.pages),\\\"metadata\\\",str(r.metadata)); print(\\\"version lines\\\",[l for l in txt.splitlines() if \\\"arXiv\\\" in l]); print(\\\"first lines\\\",txt.splitlines()[:8])\")'", "timeout": 60}</tool_call>
</message>
<message type="tool">2107.07511 pages 51 metadata {'/Author': '', '/CreationDate': 'D:20221208011258Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20221208011258Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) kpathsea version 6.3.2', '/Producer': 'pdfTeX-1.40.21', '/Subject': '', '/Title': '', '/Trapped': '/False'}
version lines ['arXiv:2107.07511v6  [cs.LG]  7 Dec 2022']
first lines ['A Gentle Introduction to Conformal Prediction and', 'Distribution-Free Uncertainty Quantiﬁcation', 'Anastasios N. Angelopoulos and Stephen Bates', 'December 8, 2022', 'Abstract', 'Black-box machine learning models are now routinely used in high-risk settings, like medical diagnos-', 'tics, which demand uncertainty quantiﬁcation to avoid consequential model failures. Conformal predic-', 'tion (a.k.a. conformal inference) is a user-friendly paradigm for creating statistically rigorous uncertainty']
1904.06019 pages 17 metadata {'/Author': '', '/CreationDate': 'D:20200708002641Z', '/Creator': 'LaTeX with hyperref package', '/Keywords': '', '/ModDate': 'D:20200708002641Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.17 (TeX Live 2016) kpathsea version 6.2.2', '/Producer': 'pdfTeX-1.40.17', '/Subject': '', '/Title': '', '/Trapped': '/False'}
version lines ['arXiv:1904.06019v3  [stat.ME]  6 Jul 2020']
first lines ['Conformal Prediction Under Covariate Shift', 'Ryan J. Tibshirani Rina Foygel Barber Emmanuel J. Candès Aaditya Ramdas', 'Abstract', 'We extend conformal prediction methodology beyond the case of exchangeable data. In particular, we show that a', 'weighted version of conformal prediction can be used to compute distribution-free prediction intervals for problems in', 'which the test and training covariate distributions differ, but the likelihood ratio between these two distributions is', 'known—or, in practice, can be estimated accurately with access to a large set of unlabeled data (test covariate points).', 'Our weighted extension of conformal prediction also applies more generally, to settings in which the data satisﬁes a']
2009.14193 pages 18 metadata {'/Author': '', '/CreationDate': 'D:20220907011307Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20220907011307Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) kpathsea version 6.3.2', '/Producer': 'pdfTeX-1.40.21', '/Subject': '', '/Title': '', '/Trapped': '/False'}
version lines ['arXiv:2009.14193v5  [cs.CV]  3 Sep 2022']
first lines ['UNCERTAINTY SETS FOR IMAGE CLASSIFIERS USING', 'CONFORMAL PREDICTION', 'Anastasios N. Angelopoulos∗†, Stephen Bates∗, Jitendra Malik, &amp; Michael I. Jordan', 'Department of Electrical Engineering and Computer Sciences', 'Department of Statistics', 'University of California, Berkeley', 'Berkeley, CA 94704, USA', '{angelopoulos,stephenbates,malik,jordan}@cs.berkeley.edu']
2402.10723 pages 16 metadata {'/Author': '', '/CreationDate': 'D:20240219015235Z', '/Creator': 'LaTeX with hyperref', '/Keywords': '', '/ModDate': 'D:20240219015235Z', '/PTEX.Fullbanner': 'This is pdfTeX, Version 3.141592653-2.6-1.40.25 (TeX Live 2023) kpathsea version 6.3.5', '/Producer': 'pdfTeX-1.40.25', '/Subject': '', '/Title': '', '/Trapped': '/False'}
version lines ['arXiv:2402.10723v1  [stat.ML]  16 Feb 2024']
first lines ['CONFORMALIZED CREDAL SET PREDICTORS', 'A PREPRINT', 'Alireza Javanmardi1,2, David Stutz 3, and Eyke H¨ullermeier 1,2', '1Institute of Informatics, LMU Munich, Germany', '2Munich Center for Machine Learning (MCML), Germany', '3Max Planck Institute for Informatics, Saarland Informatics Campus, Germany', 'alireza.javanmardi@ifi.lmu.de, david.stutz@mpi-inf.mpg.de, eyke@ifi.lmu.de', 'ABSTRACT']

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Locating credal setup pages**</reasoning></content>
  <tool_call id="call_a2b256c7387447fbbbeea2c219b0359e" name="execute">{"command": "python -c 'from pypdf import PdfReader; r=PdfReader(\"/work/literature/2402.10723.pdf\"); [print(\"PDF PAGE\",p,\"\\n\",r.pages[p-1].extract_text()) for p in [6,7,8,9,13,14]]'", "timeout": 90}</tool_call>
</message>
<message type="tool">PDF PAGE 6 
 Conformalized Credal Set Predictors A PREPRINT
4.1 Noisy Observations
So far, we (implicitly) assumed that ground-truth probability distributions λxi will be provided as training (and
calibration) data. Needless to say, this assumption will rarely hold true in practice. Instead, observations will rather be
noisy versions ˜λxi of the true probabilities, i.e., the data will be of the form
D =
n 
x1, ˜λx1 , . . . , xN , ˜λxN o ⊂ X ×∆K . (9)
Notably, such datasets emerge in scenarios where each data instance x is annotated by multiple human experts, which
recently have attracted a lot of attention in the context of machine learning and also conformal prediction [Stutz
et al., 2023b, Javanmardi et al., 2023]. In this context, ˜λx denotes the distribution derived from aggregating annotator
disagreements concerning the label of instance x. Of course, conformal prediction can still be applied to noisy data of
that kind, but the coverage guarantee will then only hold for the noisy labeling:
P

˜λxnew ∈ h(xnew) ≥ 1 − ˜α. (10)
Practically, one may expect that the guarantees will hold for the ground-truth as well, simply because calibration on
noisy instead of clean data will tend to make prediction regions larger and hence more conservative. Moreover, since
nonconformity is derived from a predictive model g(·) that seeks to recover ground-truth probabilities, the latter should
conform at least as well as noisy distributions. Of course, this intuition is not a formal guarantee. In order to provide
such a guarantee for the ground-truth probabilities, one obviously needs to make some assumptions. Concretely, let us
make the following bounded noise assumption for the labeling process: The labeling noise is (stochastically) bounded
in the sense that, given the nonconformity function f and a (small) probability δ &gt;0, there exists a tolerance ϵ &gt;0
such that
P

|f (x, λx) − f (x, ˜λx)| &lt; ϵ ≥ 1 − δ (11)
all x ∈ X.
Theorem 4.2. Let α &gt;0 be any miscoverage rate, and suppose the bounded noise assumption holds. Let q = q(E, ˜α)
be the critical threshold on the noisy calibration data Dcalib for miscoverage rate
˜α = α − δ1 − δ .
Then, for any new query xnew ∈ X,
P
 
f (xnew, λxnew) &lt; q+ ϵ ≥ 1 − α .
The proof is deferred to Appendix A.. As a consequence of this result, a conformal predictor learned on the noisy data
with modified miscoverage rate ˜α can be turned into a valid predictor (with miscoverage rate α) for the ground-truth
data by increasing the learned rejection threshold by ϵ, provided the bounded noise property (11) can be ascertained.
Thus, if we denote the corresponding credal set predictor by hϵ, we can guarantee that
P
 
λxnew ∈ hϵ(xnew) ≥ 1 − α . (12)
5 Experiments
In this section, we evaluate the performance of our proposed methods using both synthetic and real datasets. In vanilla
conformal prediction, the performance of a method is usually assessed based on the average prediction set size, aka
efficiency, and the average coverage on the test set. It is more appealing to have the promised coverage with smaller
sets. In our scenario, the analytical calculation of credal sets is not feasible. Therefore, for the sake of illustration as
well as other analyses, such as efficiency calculation, we resort to approximations. We discretize the simplex with a
resolution of 0.005, yielding M = 19969 distributions. This enables the straightforward construction of credal sets, as
defined in (8). The efficiency is gauged by considering the fraction of all M distributions that lie within the predicted
credal sets. All implementations and experiments can be found in the technical supplement of this work.1
5.1 Learning Model
In our experiments, we employ a deep neural network as the learner. Specifically, the model consists of three hidden
layers with 256, 64, and 16 units, utilizing ReLU as the activation function. Prior to the output layer, a dropout
1The link to the code: https://github.com/alireza-javanmardi/conformal-credal-sets
6
PDF PAGE 7 
 Conformalized Credal Set Predictors A PREPRINT
Table 1: Summary of the nonconformity functions used in experiments.
Name Formulation Predictor
TV 12 PKk=1 |λxk − g(x)k| first-order
WS - first-order
KL PKk=1 λxk log( λxkg(x)k ) first-order
Inner 1 − PKk=1 λxk g(x)k first-order
SO as in (6) second-order
layer with a rate of 0.3 is incorporated. The same model architecture serves both first- and second-order predictors,
differing only in the activation functions of the output layers. For the first-order predictor, softmax is used, while for
the second-order predictor, ReLU is employed. Learning is facilitated using the Adam optimizer with a learning rate
of 10−4, utilizing cross-entropy as the loss function for the first-order predictor and negative log-likelihood for the
second-order predictor.
5.2 Nonconformity Functions
CP should work regardless of the choice of nonconformity score function, while this choice can affect the efficiency
and geometry of the prediction set. For the sake of comparison, we examine different nonconformity functions in our
experiments. When utilizing a first-order predictor, besides total variation (TV) and the First Wasserstein (WS) distance,
we also investigate the Kullback–Leibler (KL) divergence and 1 minus the inner product (Inner) as nonconformity
functions. For the second-order predictor, we consider 1 minus the relative likelihood (SO) as defined in (6). Table 1
offers a summary of all five nonconformity functions employed in our experiments.
5.3 Real Data
We focus on the ChaosNLI dataset [Nie et al., 2020], an English Natural Language Inference (NLI) dataset that captures
the inherent variability in human judgments of textual entailment. Here, the classes are entailment, neutral, and
contradiction for each premise-hypothesis pair. Instances in this dataset are selected from the development sets of SNLI
[Bowman et al., 2015], MNLI [Williams et al., 2018], and AbductiveNLI [Bhagavatula et al., 2019], for which the
majority vote was less than three among the five human annotators. These instances were then given to100 independent
humans for annotation, given strict annotation guidelines.
We combine the chaos-SNLI and chaos-MNLI subsets, resulting in a dataset of 3113 datapoints. For model training,
we leverage a language model from the Hugging Face transformers library [Wolf et al., 2019], initially trained on
SNLI and MultiNLI datasets for classification tasks2. We utilize the last hidden layer output of this model to embed the
premise-hypothesis pairs from our 3113 instances, serving as inputs for our deep neural network. To split the data, we
randomly select 500 instances for calibration, 500 for testing, and the remaining for training. This process is repeated
ten times with different random seeds. In Figure 3, we compare the resulting credal sets of different nonconformity
functions for three specific instances. Figure 4 summarizes the overall performance of the proposed methods on this
data under different miscoverage rates (α). Notably, the mean of the average coverage over the test data across various
random seeds aligns with or exceeds the nominal value, consistent with the conformal prediction guarantee.
5.4 Synthetic Data
The primary objective of conducting experiments with synthetic data is to illustrate the impact of noisy observations,
particularly to showcase the behavior of the proposed credal sets when we only have access to an approximation of the
ground truth distributions. Our experiment revolves around a K-class classification task with K ∈ {3, 4, 6, 8, 10}. For
each K, we consider 10-dimensional features X ∈ R10, where each X1, . . . , X10 are independent standard normal
random variables. Subsequently, we generate a random matrix β ∈ R10×K, with its elements drawn independently
from the standard normal distribution. To define the ground truth probability over the classes for object X, we use the
following formulation:
λxk := P(Y = k|x) = Zj(x)P
j Zj(x) ,
2The model can be found at https://huggingface.co/cross-encoder/nli-deberta-base
7
PDF PAGE 8 
 Conformalized Credal Set Predictors A PREPRINT
Premise-Hypothesis pair TV KL WS Inner SO
Premise: A man in a bar drinks from
a pitcher while a man in a green hat
looks on and a woman in a black
shirt drink from a glass.
Hypothesis: The women is drinking
water.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.24 0 .18 0 .28 0 .36 0 .06
Premise: The streets are busy and
people contemplate their futures.
Hypothesis: People are screaming
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.33 0 .20 0 .33 0 .41 0 .47
Premise: A photographer snaps a
midair action shot of a snowboarder.
Hypothesis: The midair shot snaps
at a boarder of snow.
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
HQWDLOPHQW
QHXWUDO
FRQWUDGLFWLRQ
0.31 0 .27 0 .26 0 .34 0 .08
Figure 3: Various credal sets obtained for three instances from ChaosNLI dataset [Nie et al., 2020]. The ground
truth distributions are denoted by orange squares. Black circles indicate model predictions in cases employing a
first-order learner (first four columns). For the last column, utilizing a second-order learner, the predicted second-order
distributions are represented through contour plots. The miscoverage rate is α = 0.2, and the efficiency of each credal
set is written below it.
79 ./ :6 ,QQHU 62
              
0 LVFRYHUDJHUDWH 





$YHUDJH&amp;RYHUDJH






$YHUDJH(IILFLHQF\$YHUDJH&amp;RYHUDJH
$YHUDJH(IILFLHQF\
Figure 4: Coverage and efficiency results of different nonconformity functions applied on the ChaosNLI dataset [Nie
et al., 2020]. The horizontal dashed lines indicate the nominal coverage levels.
where Z(x) := exp(x⊤β). Employing this data-generating process, we generate N = 1500 samples to construct the
dataset DK = {(xi, λxi )}Ni=1.
To obtain noisy versions of DK, we employ a sampling approach. Specifically, we independently sample each
distribution λxi m times and utilize relative frequencies to create its noisy counterpart ˜λxim . We represent the resulting
dataset as DKm = {(xi, ˜λxim )}Ni=1. We repeat this process four times with m ∈ {1, 5, 10, 100}.
Given each dataset DKm, we randomly partition data points equally into training, calibration, and test sets and perform
the proposed methodologies accordingly. Again, we repeat this process ten times with different random seeds for each
dataset DKm. Due to the computational complexity in calculating efficiency for cases with K &gt;3, we utilize the quantile
of the calibration nonconformity scores as an efficiency metric. In Figure 5, we represent the overall result for TV
under different K and m values. It can be observed that the coverage is fulfilled across almost all scenarios, including
m = 1 with degenerate distributions. This observed behavior is somewhat intuitive. The model endeavors to learn the
underlying probabilistic relationship between X and Y , even given the noisy data 3. Consequently, during calibration
3Of course, this holds under some reasonable assumptions on noise.
8
PDF PAGE 9 
 Conformalized Credal Set Predictors A PREPRINT
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH$YHUDJH&amp;RYHUDJH
$YHUDJH4XDQWLOH
Figure 5: Coverage and quantile results for synthetic data, where the ground truth distributions are approximated by
observing m samples from them. The horizontal dashed line indicates the nominal coverage levels 1 − α = 0.9.
with noisy instances, the nonconformity scores of noise-free instances are mostly upper-bounded by the scores of their
noisy counterparts, resulting in more conservative sets that effectively cover the ground-truth distributions. It can also
be seen that the quantile of the nonconformity scores shrinks as m increases. Results for other nonconformity functions,
along with some visualizations for the specific case of K = 3, can be found in Appendix B..
6 Limitations
The methods we proposed are promising but still subject to certain limitations. One challenge, for example, lies in the
representation of credal sets as subsets of the probability simplex. For the nonconformity functions we used in this
work, there are no closed-form equations for the resulting credal sets. Instead, the sets are only represented implicitly
(through the nonconformity threshold). Numerical approximation is feasible but essentially limited to scenarios with a
small number of classes.
The issue of representation is also connected to the computation of uncertainty measures, i.e., numerical measures
quantifying the total, aleatoric, and epistemic uncertainty associated with a credal set [Klir and Wierman, 1999].
Computation of these measures involves the computation of specific characteristics of the set, such as its distance from
the center of the simplex or its volume [Sale et al., 2023].
Our generalization to the case of noisy training data, i.e., labelings˜λ that only approximate the ground-truth probabilities
λ, provides guarantees under the bounded noise assumption. While this assumption is plausible, and in a sense always
achievable with a sufficiently large ϵ, its practical use requires a meaningful choice of ϵ and δ, which leads to inference
that is both valid and efficient. This will be difficult in cases of limited knowledge about the labeling noise. If labels are
constructed from relative frequencies (like in the case of multiple annotators), classical statistical methods might be
applicable. In general, however, an appropriate choice of ϵ and δ for practical problems is still an open problem.
7 Conclusion and Future Work
Conformal credal set prediction connects machine learning with imprecise probability theory and offers a novel data-
driven approach to constructing predictions that effectively capture both aleatoric and epistemic uncertainty. Thereby, it
provides the basis of a new approach to reliable, uncertainty-aware machine learning. Leveraging the inherent validity
of the conformal prediction framework, our conformalized credal sets are assured to cover the ground truth distributions
with high probability. We have explored different nonconformity functions within this novel setting and evaluated their
performance through numerical experiments.
A natural next step is to explore alternative approaches for defining nonconformity functions, with the goal of devising
formulations amenable to closed-form solutions for credal sets. Besides, the nonconformity has a strong influence on
the efficiency and hence the uncertainty of credal set predictions. Obviously, there is a preference for nonconformity
functions leading to higher efficiency and lower uncertainty.
Another interesting direction is to extend the learning of credal set predictors to standard (zero-order) training data.
As already mentioned, learning a second-order predictor from data of that kind turns out to be difficult in the case of
second-order probability distributions. Broadly speaking, this is due to the inherent ambiguity of the missing first-order
information, which cannot be resolved due to certain averaging effects [Bengs et al., 2022, 2023]. For the case of credal
predictors, the situation is still less clear.
9
PDF PAGE 13 
 Conformalized Credal Set Predictors A PREPRINT
Appendix A. Proof of Theorem 4.2
Proof. Let A denote the event f (xnew, λxnew) &lt; q+ ϵ and ˜A the event f (xnew, ˜λxnew) &lt; q. We have
P (A) ≥ P (A ∧ ˜A)
= P ( ˜A) · P (A | ˜A)
= P ( ˜A) · (1 − P (¬A | ˜A))
Since ¬A means that f (xnew, λxnew) ≥ q + ϵ, the conditional event ¬A | B implies a violation of the closeness
condition in (11), wherefore the probability P (¬A | B) is upper-bounded by δ according to (11). Therefore, noting that
P ( ˜A) ≥ 1 − ˜α is the standard guarantee by CP,
P (A) ≥ P ( ˜A) · (1 − P (¬A | ˜A))
≥ (1 − ˜α) · (1 − δ)
= 1 − α .
Appendix B. More Results for the Synthetic Data
Figure 6 depicts the overall coverage and quantile comparison between four different nonconformity functions TV,
KL, WS, and Inner. In Figure 7, we illustrate the evolution of the credal sets as m changes from 1 to 100 for different
nonconformity functions when K = 3. For this case, the full comparison of efficiency and coverage across various
nonconformity functions is provided in Figure 8.
13
PDF PAGE 14 
 Conformalized Credal Set Predictors A PREPRINT
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH
(a) TV
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH





$YHUDJH4XDQWLOH
(b) KL
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH





$YHUDJH4XDQWLOH
(c) WS
.  .  .  .  . 
                   
PQXPEHURIVDPSOHV





$YHUDJH&amp;RYHUDJH






$YHUDJH4XDQWLOH
(d) Inner
Figure 6: Coverage and quantile results for synthetic data, where the ground truth distributions are approximated by
observing m samples from them. The horizontal dashed lines indicate the nominal coverage levels 1 − α = 0.9.
14

[Command succeeded with exit code 0]</message>
<message type="ai">
  <content><reasoning>**Checking theorem caveats**</reasoning> <reasoning>**Preparing research notes**</reasoning></content>
  <tool_call id="call_de95dd031b5a4f0db387ecb031271f94" name="write_file">{"content": "@misc{angelopoulos2021gentle,\n  title = {A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification},\n  author = {Angelopoulos, Anastasios N. and Bates, Stephen},\n  year = {2021},\n  eprint = {2107.07511},\n  archivePrefix = {arXiv},\n  primaryClass = {cs.LG},\n  url = {https://arxiv.org/pdf/2107.07511},\n  note = {Consulted PDF: arXiv:2107.07511v6, 7 December 2022; title page dated 8 December 2022}\n}\n\n@misc{tibshirani2019covariateshift,\n  title = {Conformal Prediction Under Covariate Shift},\n  author = {Tibshirani, Ryan J. and Barber, Rina Foygel and Cand{\\`e}s, Emmanuel J. and Ramdas, Aaditya},\n  year = {2019},\n  eprint = {1904.06019},\n  archivePrefix = {arXiv},\n  primaryClass = {stat.ME},\n  url = {https://arxiv.org/pdf/1904.06019},\n  note = {Consulted PDF: arXiv:1904.06019v3, 6 July 2020}\n}\n\n@misc{angelopoulos2020uncertaintysets,\n  title = {Uncertainty Sets for Image Classifiers Using Conformal Prediction},\n  author = {Angelopoulos, Anastasios N. and Bates, Stephen and Malik, Jitendra and Jordan, Michael I.},\n  year = {2020},\n  eprint = {2009.14193},\n  archivePrefix = {arXiv},\n  primaryClass = {cs.CV},\n  url = {https://arxiv.org/pdf/2009.14193},\n  note = {Consulted PDF: arXiv:2009.14193v5, 3 September 2022; this identifier is not a Romano-authored paper}\n}\n\n@misc{javanmardi2024credal,\n  title = {Conformalized Credal Set Predictors},\n  author = {Javanmardi, Alireza and Stutz, David and H{\\\"u}llermeier, Eyke},\n  year = {2024},\n  eprint = {2402.10723},\n  archivePrefix = {arXiv},\n  primaryClass = {stat.ML},\n  url = {https://arxiv.org/pdf/2402.10723},\n  note = {Consulted PDF: arXiv:2402.10723v1, 16 February 2024}\n}\n", "file_path": "/work/literature/references.bib"}</tool_call>
</message>
<message type="tool">Updated file /work/literature/references.bib</message>

