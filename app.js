// ResearchWorld-Eval experiment dashboard. Read-only: it shows the facts in data/ and draws no conclusions.
// Pure render functions (data in, HTML string out) are exported for the tests; `configure` sets the language,
// the page strings (strings.json) and the glossary they use. The browser glue at the end fetches the data
// (site.json says from where) and routes on the URL hash; every page has its own address:
//   #/                      overview          #/matrix, #/matrix/<batch>     plan matrix, one batch
//   #/tasks, #/task/<id>    E2E tasks         #/compare/<task key>           one task under every condition
//   #/conditions, #/condition/<name>          #/systems, #/system/<name>
//   #/benchmarks, #/benchmark/<id>            #/items, #/item/<benchmark>/<item>  benchmark items, one item
//   #/runs, #/run/<run-id>
//   #/cells/<batch>         condition x task cell matrix     #/cell/<batch>/<condition>/<task>  one cell
//   #/defects, #/defect/<system>/<id>   known defects of the systems under test
//   #/ranking, #/ranking/<task>   system ranking by the pairwise judge, and one task's pairs with the judge's reasons
//   #/results               summaries         #/glossary, #/glossary/<term>  #/about
// A query after the route (#/runs?system=coding-agent) holds a page's filters; ?lang=en in the address picks
// the language.

export const LANGS = ["zh", "en"];
const S = { lang: "zh", strings: { zh: {}, en: {} }, terms: {}, planned: null };

export function configure({ lang, strings, glossary, batches } = {}) {
  if (strings) S.strings = strings;
  if (batches !== undefined) S.planned = batches ? new Set(batches) : null;   // the batches that have a plan matrix; others are only named
  if (lang && LANGS.includes(lang)) S.lang = lang;
  if (glossary) S.terms = Object.fromEntries(glossary.map((g) => [g.id, g]));
  return S.lang;
}

export function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
const enc = (s) => encodeURIComponent(s);

// A page string in the current language, with {name} placeholders filled (values are escaped).
export function t(key, vars = {}) {
  const s = S.strings[S.lang]?.[key] ?? S.strings.zh?.[key] ?? key;
  return esc(s).replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
}
// A data text given in both languages ({zh, en}), or a plain string.
export function L(v) {
  if (v == null) return "";
  if (typeof v === "string") return v;
  return v[S.lang] ?? v.zh ?? v.en ?? "";
}
const verbatim = () => ` <span class="tag" title="${t("verbatim.title")}">${t("verbatim")}</span>`;
const missing = (why) => `<span class="missing"${why ? ` title="${esc(why)}"` : ""}>${t("not_recorded")}</span>${why ? `<div class="sub">${esc(why)}</div>` : ""}`;

// ---- glossary terms ---------------------------------------------------------------------------------

// A value shown with its full name and meaning: hover for both, click for the glossary entry.
export function term(id, text) {
  const g = S.terms[id];
  const shown = text ?? (g ? (g.short && !String(g.short).includes("/") ? g.short : L(g.name)) : id);
  if (!g) return esc(shown ?? "–");
  return `<a class="term" href="#/glossary/${enc(id)}" title="${esc(L(g.name))} — ${esc(L(g.means))}">${esc(shown)}</a>`;
}
const tname = (id) => (S.terms[id] ? L(S.terms[id].name) : id ?? "–");

export function condLabel(name, full = true) {
  if (!name) return "–";
  const g = S.terms[name];
  const link = `<a class="term cond" href="#/condition/${enc(name)}" title="${esc(g ? L(g.name) : name)}">${esc(name)}</a>`;
  return full && g ? `${link}<div class="sub">${esc(L(g.name))}</div>` : link;
}
const sysLink = (name) => (name ? `<a href="#/system/${enc(name)}" title="${esc(S.terms[name] ? L(S.terms[name].means) : "")}">${esc(tname(name))}</a>` : "–");
const runLink = (id) => `<a href="#/run/${enc(id)}">${esc(id)}</a>`;
const taskUnit = (key) => String(key || "").split("/")[0];
const itemHref = (key) => `#/item/${String(key).split("/").map(enc).join("/")}`;
function taskLink(key, kind) {
  if (!key) return "–";
  const unit = taskUnit(key);
  const href = key.includes("/") && !key.endsWith("/all") ? itemHref(key) : kind === "benchmark" || key.includes("/") ? `#/benchmark/${enc(unit)}` : `#/task/${enc(unit)}`;
  return `<a href="${href}">${esc(key)}</a>`;
}

// ---- formatting -------------------------------------------------------------------------------------

export function fmtTime(s) {
  return s ? esc(String(s).replace("T", " ").replace("Z", " UTC")) : "–";
}

export function fmtDuration(sec) {
  if (sec == null) return "–";
  sec = Math.round(sec);
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  return h ? t("dur.hm", { h, m }) : m ? t("dur.ms", { m, s }) : t("dur.s", { s });
}

export function fmtUsd(spend) {
  if (!spend) return "–";
  if (spend.usd != null) return `$${Number(spend.usd).toFixed(2)}`;
  if (spend.usd_basis === "subscription" && spend.equivalent_usd != null) return t("usd.equivalent", { usd: Number(spend.equivalent_usd).toFixed(2) });
  return { subscription: t("usd.subscription"), unpriced: t("usd.unpriced") }[spend.usd_basis] || "–";
}

const kTokens = (v) => (v == null ? "–" : v >= 1e6 ? `${(v / 1e6).toFixed(2)}M` : v >= 1e3 ? `${(v / 1e3).toFixed(1)}k` : String(Math.round(v)));

export function fmtNum(v, digits = 3) {
  if (v == null || v === "") return "–";
  const n = Number(v);
  if (Number.isNaN(n)) return esc(v);
  return Number.isInteger(n) ? String(n) : n.toFixed(digits).replace(/0+$/, "").replace(/\.$/, "");
}

export function fmtTokens(tk) {
  if (!tk) return "–";
  const k = (v) => (v == null ? "–" : v >= 1e6 ? `${(v / 1e6).toFixed(2)}M` : v >= 1e3 ? `${(v / 1e3).toFixed(1)}k` : String(v));
  return t("tokens.line", { i: k(tk.input), o: k(tk.output), cr: k(tk.cache_read), cw: k(tk.cache_write) });
}

export function scoreText(s) {
  if (!s || !s.summary) return "–";
  const m = s.summary;
  return `${fmtNum(m.value)} / ${fmtNum(m.max)}${m.direction === "lower" ? ` ${t("score.lower_better")}` : ""}`;
}

// An external reviewer's score against the original paper's (Stanford: also the solve line), or ASI-Bench's solve line
// (Issue #142, #152): "0.86x the original (6.3), solve line 5.04: solved"
export function relativeText(s) {
  const r = s?.summary?.relative;
  if (!r) return "";
  const bits = [];
  if (r.original != null) bits.push(t("rel.vs_original", { ratio: fmtNum(r.ratio, 2), original: fmtNum(r.original, 1) }));
  if (r.solve_line != null) bits.push(t("rel.solve_line", { line: fmtNum(r.solve_line, 2) }));
  if (r.solved != null) bits.push(`<strong>${t(r.solved ? "rel.solved" : "rel.not_solved")}</strong>`);
  return bits.join(" · ");
}
// The role an evaluator's score has on its run page: an E2E run's main score is an external reviewer's, rubric-judge auxiliary
const PRIMARY_EVALUATORS = ["stanford-agentic-reviewer", "ai-scientist-reviewer"];
const roleTag = (ev) => (PRIMARY_EVALUATORS.includes(ev) ? ` <span class="tag" title="${t("rel.primary_note")}">${t("rel.primary")}</span>`
  : ev === "rubric-judge" ? ` <span class="tag" title="${t("rel.auxiliary_note")}">${t("rel.auxiliary")}</span>` : "");
// A Stanford review page on file whose score could not be read yet: to be parsed, never "no score"
const pendingTag = () => `<span class="tag pending">${term("review-pending-parse", t("rel.pending_parse"))}</span>`;
const pendingParse = (list) => (list || []).map((ev) => `<div>${term(ev, tname(ev))}: ${pendingTag()}</div>`).join("");

// An extra score's name: its glossary term, also for a per-model extra "<name> (<model>)"
function extraName(k) {
  const m = /^(.*) \(([^()]+)\)$/.exec(k);
  return m && S.terms[m[1]] ? `${term(m[1], tname(m[1]))} (${esc(m[2])})` : term(k, S.terms[k] ? tname(k) : k);
}

function mainScore(run) {
  const s = (run.scores || []).find((x) => x.summary);
  const rel = s ? relativeText(s) : "";
  const pending = (run.review_pending || []).length && !(s && PRIMARY_EVALUATORS.includes(s.evaluator)) ? pendingParse(run.review_pending) : "";
  return (s ? `${term(s.evaluator, tname(s.evaluator))}: ${scoreText(s)}${roleTag(s.evaluator)}${rel ? `<div class="sub">${rel}</div>` : ""}` : (pending ? "" : "–")) + pending;
}

function statusClass(status, live) {
  return live ? "running" : /^completed/.test(status) ? "done" : /^running/.test(status) ? "stale" : "failed";
}
export function statusBadge(status, live) {
  const g = S.terms[status];
  const text = g ? L(g.name) : status;
  return `<span class="badge ${statusClass(status, live)}" title="${esc(g ? L(g.means) : status)}">${esc(text)}${live ? " ●" : ""}</span>`;
}
const purpose = (p) => (p ? term(p, tname(p)) : "–");
// A run's purpose, with "unfinished" for an evaluation run that did not end normally (Issue #67)
export function runPurpose(r) {
  if (!r.unfinished) return purpose(r.purpose);
  return `${purpose(r.purpose)} <span class="badge failed" title="${esc(t("run.unfinished_note", { status: r.status }))}">${t("run.unfinished")}</span>`;
}
// A run's status with the end reason its system reported (e.g. a world's budget-exhausted behind "timeout")
export function runStatus(r) {
  return `${statusBadge(r.shown_status, r.live)}${r.status_reason ? `<div class="sub">${term(r.status_reason, tname(r.status_reason))}</div>` : ""}` +
    (r.stop_reason ? `<div class="sub">${t("run.stop_reason", { why: esc(r.stop_reason) })}</div>` : "");
}
// Why a field of a run is empty (Issue #67), or "–" when nothing says why
const why = (r, field) => (r.missing?.[field] ? `<span class="sub">${t(`miss.${field}.${r.missing[field]}`)}</span>` : "–");
const kv = (rows) => `<table class="kv"><tbody>${rows.filter(Boolean).map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join("")}</tbody></table>`;
// A batch that has no plan matrix (a benchmark kept out of the formal batches, #86) is named, not linked.
const batchLink = (name) => (S.planned && !S.planned.has(name) ? `<span>${esc(name)}</span>` : `<a href="#/matrix/${enc(name)}">${esc(name)}</a>`);
const section = (title, body, id = "") => `<section${id ? ` id="${id}"` : ""}><h2>${title}</h2>${body}</section>`;
const table = (head, rows, empty, foot = "") => `<div class="scroll"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.length ? rows.join("") : `<tr><td colspan="${head.length}" class="sub">${empty || t("none")}</td></tr>`}</tbody>${foot ? `<tfoot>${foot}</tfoot>` : ""}</table></div>`;
const crumbs = (...items) => `<nav class="crumbs">${items.map(([href, label]) => (href ? `<a href="${href}">${label}</a>` : `<span>${label}</span>`)).join(" › ")}</nav>`;

function link(url, text) {
  if (!url) return esc(text || "–");
  return /^https?:\/\//.test(url) ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text || url)}</a>` : esc(text || url);
}

// ---- navigation ---------------------------------------------------------------------------------------

export const NAV = ["overview", "matrix", "performance", "analysis", "tasks", "benchmarks", "items", "conditions", "systems", "defects", "runs", "results", "glossary", "about"];

export function renderNav(view) {
  const active = { batch: "matrix", cells: "matrix", cell: "matrix", defect: "defects", task: "tasks", experiment: "tasks", condition: "conditions", system: "systems", benchmark: "benchmarks", item: "items", run: "runs" }[view] || view;
  return NAV.map((v) => `<a href="#/${v === "overview" ? "" : v}"${v === active ? ' class="active" aria-current="page"' : ""}>${t(`nav.${v}`)}</a>`).join("");
}

// ---- filters (runs, matrix) -------------------------------------------------------------------------------

export function applyFilters(runs, f) {
  return runs.filter((r) =>
    (!f.batch || r.batch === f.batch) &&
    (!f.condition || r.condition === f.condition) &&
    (!f.system || r.system === f.system) &&
    (!f.purpose || r.purpose === f.purpose) &&
    (!f.status || statusClass(r.shown_status, r.live) === f.status) &&
    (!f.benchmark || (f.benchmark === "e2e" ? r.task_kind === "e2e" : taskUnit(r.task) === f.benchmark)));
}

function options(values, selected, label, show = (v) => v) {
  return `<option value="">${label}: ${t("filter.all")}</option>` +
    [...new Set(values.filter(Boolean))].sort().map((v) => `<option value="${esc(v)}"${v === selected ? " selected" : ""}>${esc(show(v))}</option>`).join("");
}

export function renderFilters(index, f, fields = ["batch", "benchmark", "condition", "system", "purpose", "status"]) {
  const runs = index.runs || [];
  const benches = ["e2e", ...Object.values(index.tasks || {}).filter((x) => x.kind === "benchmark").map((x) => x.id)];
  const sel = {
    batch: () => options([...(index.conditions.plan.batches || []), ...runs.map((r) => r.batch)], f.batch, t("f.batch")),
    benchmark: () => options(benches, f.benchmark, t("f.benchmark"), (v) => (v === "e2e" ? "E2E" : tname(v))),
    condition: () => options((index.conditions.items || []).map((c) => c.name), f.condition, t("f.condition")),
    system: () => options([...runs.map((r) => r.system), ...Object.keys(index.systems || {})], f.system, t("f.system"), tname),
    purpose: () => options(runs.map((r) => r.purpose), f.purpose, t("f.purpose"), tname),
    status: () => options(["running", "done", "failed", "stale"], f.status, t("f.status"), (v) => t(`state.${v}`)),
  };
  return `<form class="filters" id="filters" aria-label="${t("filter.label")}">${fields.map((k) => `<select name="${k}" aria-label="${t(`f.${k}`)}">${sel[k]()}</select>`).join("")}</form>`;
}

// ---- overview ---------------------------------------------------------------------------------------------

function stat(value, label, href, cls = "") {
  return `<a class="stat ${cls}" href="${href}"><span class="num">${value}</span><span class="label">${label}</span></a>`;
}

export function renderOverview(index) {
  const runs = index.runs || [];
  const live = runs.filter((r) => r.live);
  const evalRuns = runs.filter((r) => r.purpose === "evaluation");
  const done = evalRuns.filter((r) => r.status === "completed").length;
  const failed = evalRuns.filter((r) => /^(failed|timeout|stopped|error|lost)$/.test(r.status)).length;
  const conds = index.conditions.items || [];
  const tasks = Object.values(index.tasks || {});
  const cells = (index.matrix || []).reduce((n, m) => n + m.tasks.length * conds.length, 0);
  const cellsDone = (index.matrix || []).reduce((n, m) => n + Object.values(m.totals).reduce((a, x) => a + x.done, 0), 0);
  const usd = runs.reduce((a, r) => a + (r.spend?.usd || 0), 0);
  const stats = [
    stat(`${cellsDone} / ${cells}`, t("ov.cells_done"), "#/matrix"),
    ...((index.cellmatrix || []).length ? [stat(`${(index.cellmatrix[0].tasks || []).length} × ${Object.keys(index.cellmatrix[0].rows || {}).length}`, t("ov.cell_matrix"), `#/cells/${enc(index.cellmatrix[0].batch)}`)] : []),
    stat(live.length, t("ov.running_now"), "#/runs?status=running", live.length ? "running" : ""),
    stat(`${done} / ${failed}`, t("ov.eval_done_failed"), "#/runs?purpose=evaluation"),
    stat(runs.length, t("ov.all_runs"), "#/runs"),
    stat(conds.length, t("ov.conditions"), "#/conditions"),
    stat(Object.keys(index.systems || {}).length, t("ov.systems"), "#/systems"),
    stat(tasks.filter((x) => x.kind === "e2e").length, t("ov.e2e_tasks"), "#/tasks"),
    stat(tasks.filter((x) => x.kind === "benchmark").length, t("ov.benchmarks"), "#/benchmarks"),
    stat((index.items || []).length, t("ov.items"), "#/items"),
    stat(`$${usd.toFixed(2)}`, t("ov.spend"), "#/results"),
  ].join("");
  const liveList = live.length
    ? table([t("col.run"), t("col.system"), t("col.task"), t("col.condition"), t("col.elapsed"), t("col.last_activity")],
        live.map((r) => `<tr><td>${runLink(r.run_id)}</td><td>${sysLink(r.system)}</td><td>${taskLink(r.task, r.task_kind)}</td><td>${condLabel(r.condition)}</td><td>${fmtDuration(r.spend?.wall_s)}</td><td>${fmtTime(r.last_activity)}</td></tr>`))
    : `<p class="sub">${t("ov.nothing_running")}</p>`;
  const recent = runs.slice(0, 8).map((r) => `<tr><td>${runLink(r.run_id)}</td><td>${sysLink(r.system)}</td><td>${runPurpose(r)}</td><td>${runStatus(r)}</td><td>${fmtTime(r.started_at)}</td></tr>`);
  return `<section class="intro"><h2>${t("ov.title")}</h2><p>${t("ov.lead")}</p><p class="note">${t("ov.reference_public")} ${t("ov.data_time", { time: fmtTime(index.generated_at) })}</p></section>
    ${renderPhaseProgress(index)}
    ${renderPlanSummary(index)}
    ${renderPhase1Chart(index)}
    <div class="stats">${stats}</div>
    ${section(t("ov.plan"), renderPlan(index, {}, true))}
    ${section(t("ov.running"), liveList)}
    ${section(t("ov.recent"), table([t("col.run"), t("col.system"), t("col.purpose"), t("col.status"), t("col.start")], recent) + `<p><a href="#/runs">${t("ov.all_runs_link")}</a></p>`)}`;
}

// A run the plan counts as another batch's cell (plan.credits, Issue #155): where it ran, who decided, when and on what basis.
export function creditTag(c) {
  return `<span class="tag hist" title="${t("mx.credited_tip", { by: c.by, date: c.date, source: c.source })}">${t("mx.credited", { batch: c.from_batch })}</span>`;
}

// ---- matrix -------------------------------------------------------------------------------------------------

export function renderPlan(index, f = {}, compact = false) {
  const conds = (index.conditions.items || []).filter((c) => (!f.condition || c.name === f.condition) && (!f.system || c.system === f.system));
  const mats = (index.matrix || []).filter((m) => !f.batch || m.batch === f.batch);
  const pending = index.conditions.plan.cells === "pending";
  const head = mats.map((m) => `<th><a href="#/matrix/${enc(m.batch)}">${esc(m.batch)}</a><div class="sub">${t("mx.n_tasks", { n: m.tasks.length })}</div></th>`).join("");
  const rows = conds.map((c) => {
    const cells = mats.map((m) => {
      const x = m.totals[c.name] || { tasks: 0, done: 0, running: 0, failed: 0, unsupported: 0 };
      const planned = m.planned[c.name];
      const plan = planned == null ? (compact ? "" : `<div class="sub">${term("pending", t("mx.plan_pending"))}</div>`) : planned ? "" : `<div class="sub">${t("mx.not_planned")}</div>`;
      const state = x.running ? "running" : x.done && x.done === x.tasks ? "done" : x.done || x.failed ? "partial" : "not-started";
      return `<td class="cell ${state}"><a href="#/matrix/${enc(m.batch)}?condition=${enc(c.name)}">${t("mx.done_of", { d: x.done, n: x.tasks })}</a>` +
        (x.running ? `<div>${t("mx.running_n", { n: x.running })}</div>` : "") + (x.failed ? `<div>${t("mx.failed_n", { n: x.failed })}</div>` : "") +
        (x.unsupported ? `<div>${t("mx.unsupported_n", { n: x.unsupported })}</div>` : "") + plan + `</td>`;
    }).join("");
    return `<tr><th class="rowhead">${condLabel(c.name)}</th>${cells}</tr>`;
  }).join("");
  const note = compact ? (pending ? `<p class="note">${t("mx.note_pending")}</p>` : "") : `<p class="note">${t("mx.note", { src: "<code>src/experiments/conditions.yaml</code>" })}${pending ? " " + t("mx.note_pending") : ""}</p>`;
  return `${note}<div class="scroll"><table class="matrix"><thead><tr><th>${t("col.condition")}</th>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
}

export function renderMatrix(index, f = {}) {
  const tabs = (index.matrix || []).map((m) => `<a href="#/matrix/${enc(m.batch)}">${esc(m.batch)}</a>`).join("");
  const cellTabs = (index.cellmatrix || []).map((m) => `<a href="#/cells/${enc(m.batch)}">${esc(m.batch)}</a>`).join("");
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.matrix")])}<h2>${t("mx.title")}</h2>
    <nav class="tabs">${tabs}</nav>${cellTabs ? `<p>${t("cx.new_link")}</p><nav class="tabs">${cellTabs}</nav>` : ""}${renderFilters(index, f, ["system", "condition"])}${renderPlan(index, f)}`;
}

export function renderBatch(index, name, f = {}) {
  const m = (index.matrix || []).find((x) => x.batch === name);
  if (!m) return `<p>${t("mx.no_batch", { name: esc(name) })}</p>`;
  const conds = (index.conditions.items || []).filter((c) => (!f.condition || c.name === f.condition) && (!f.system || c.system === f.system));
  const tabs = (index.matrix || []).map((x) => `<a href="#/matrix/${enc(x.batch)}"${x.batch === name ? ' class="active"' : ""}>${esc(x.batch)}</a>`).join("");
  const head = conds.map((c) => `<th>${condLabel(c.name, false)}</th>`).join("");
  const rows = m.tasks.map((key) => `<tr><th class="rowhead">${taskLink(key, key.includes("/") ? "benchmark" : "e2e")}</th>` + conds.map((c) => {
    const cell = m.cells[`${key}|${c.name}`] || { state: "not-started" };
    const sc = (cell.scores || [])[0];
    const label = tname(cell.state);
    const tip = cell.state === "unsupported" ? esc(L({ zh: cell.reason, en: cell.reason_en || cell.reason })) : t("cmp.link");
    const linkTo = key.endsWith("/all") ? (cell.latest ? runLink(cell.latest) : `<span title="${tip}">${esc(label)}</span>`) : `<a href="${compareHref(key, c.name)}" title="${tip}">${esc(label)}</a>`;
    const plan = cell.planned == null ? `<div class="sub">${t("mx.plan_pending")}</div>` : cell.planned ? "" : `<div class="sub">${t("mx.not_planned")}</div>`;
    return `<td class="cell ${cell.state}">${linkTo}${sc ? `<div>${scoreText(sc)}</div>` : ""}${cell.runs?.length > 1 ? `<div class="sub">${t("mx.n_runs", { n: cell.runs.length })}</div>` : ""}${(cell.credited || []).map((c) => `<div class="sub">${creditTag(c)}</div>`).join("")}${plan}</td>`;
  }).join("") + `</tr>`).join("");
  const desc = S.lang === "en" && m.description_en ? m.description_en : m.description;
  return `${crumbs(["#/", t("nav.overview")], ["#/matrix", t("nav.matrix")], [null, esc(name)])}
    <h2>${t("mx.batch", { name: esc(name) })}</h2><nav class="tabs">${tabs}</nav>
    <p>${esc(desc || "")}${m.error ? ` <span class="badge failed">${esc(m.error)}</span>` : ""}</p>
    ${(index.cellmatrix || []).some((x) => x.batch === name) ? `<p><a href="#/cells/${enc(name)}">${t("cx.new_link")}</a></p>` : ""}
    ${renderFilters(index, f, ["system", "condition"])}
    <div class="scroll"><table class="matrix"><thead><tr><th>${t("col.task")}</th>${head}</tr></thead><tbody>${rows}</tbody></table></div>
    <p class="note">${t("mx.cell_note")}</p>
    ${section(t("rep.title"), renderBatchReport(m, conds))}`;
}

export function fmtDelivery(d) {
  if (!d) return "–";
  if (d.complete && d.mapped?.length) return `${t("rep.delivered_mapped")}<div class="sub">${d.mapped.map((p) => t("rep.mapped", { p: esc(p) })).join("; ")}</div>`;
  if (d.complete) return t("rep.delivered");
  const parts = [...(d.missing || []).map((p) => t("rep.missing", { p: esc(p) })), ...(d.unchanged || []).map((p) => t("rep.unchanged", { p: esc(p) }))];
  return `<span class="missing">${t("rep.incomplete")}</span><div class="sub">${parts.join("; ")}</div>`;
}

// One row per task x condition that has a run: the latest run's status (and why it ended so), score, delivery and
// process metrics, for reading a batch across conditions (Issue #77).
export function renderBatchReport(m, conds) {
  const rows = [];
  for (const key of m.tasks) for (const c of conds) {
    const cell = m.cells[`${key}|${c.name}`];
    if (cell?.state === "unsupported") {
      rows.push(`<tr><td>${taskLink(key, "benchmark")}</td><td>${condLabel(c.name, false)}</td><td>${esc(tname("unsupported"))}<div class="sub">${esc(L({ zh: cell.reason, en: cell.reason_en || cell.reason }))}</div></td>` +
        `<td>–</td><td>–</td><td>–</td><td>–</td><td>–</td><td>–</td><td>–</td><td>–</td></tr>`);
      continue;
    }
    if (!cell || !cell.latest) continue;
    const sp = cell.spend || {};
    const why = cell.error || cell.status_reason;
    rows.push(`<tr><td>${taskLink(key, key.includes("/") ? "benchmark" : "e2e")}<div class="sub"><a href="${compareHref(key, c.name)}">${t("cmp.link")}</a></div></td><td>${condLabel(c.name, false)}</td>
      <td><a href="#/run/${enc(cell.latest)}">${esc(tname(cell.status || cell.state))}</a>${(cell.credited || []).map((c) => `<div class="sub">${creditTag(c)}</div>`).join("")}${why ? `<div class="sub">${esc(why)}</div>` : ""}${cell.stop_reason ? `<div class="sub">${t("run.stop_reason", { why: esc(cell.stop_reason) })}</div>` : ""}${cell.conclusion ? `<div class="sub">${t("rep.concluded", { why: esc(L({ zh: cell.conclusion, en: cell.conclusion_en || cell.conclusion })) })}</div>` : ""}</td>
      <td>${(cell.scores || []).map((s) => scoreText(s)).join("<br>") || "–"}</td><td>${fmtDelivery(cell.delivery)}</td>
      <td>${fmtDuration(sp.wall_s)}</td><td>${fmtDuration(sp.model_s)}</td><td>${fmtNum(sp.turns)}</td><td>${fmtNum(sp.requests)}</td>
      <td>${sp.tokens ? kTokens(Object.values(sp.tokens).reduce((a, v) => a + (v || 0), 0)) : "–"}</td><td>${fmtUsd(sp)}</td></tr>`);
  }
  return table([t("col.task"), t("col.condition"), t("col.status"), t("col.score"), t("rep.delivery"), t("metric.wall_s"), t("metric.model_s"),
    t("metric.turns"), t("metric.requests"), t("metric.tokens"), t("col.cost")], rows, t("rep.none")) + `<p class="note">${t("rep.note")}</p>`;
}

// ---- run configuration ----------------------------------------------------------------------------------------

function val(v, why) {
  if (v == null || v === "" || (Array.isArray(v) && !v.length)) return missing(why);
  if (Array.isArray(v)) return esc(v.join(", "));
  if (typeof v === "object") return `<code>${esc(JSON.stringify(v))}</code>`;
  return esc(v);
}
const capVal = (v) => (v == null ? `<span class="sub">${t("cfg.no_cap")}</span>` : esc(Array.isArray(v) ? v.join(", ") : v));

// The run configuration (record `setup`): what the system, agent, model, limits, network, tools and
// environment of a run (or a condition's planned run) are; a missing field shows "not recorded" and why.
export function renderSetup(s) {
  if (!s) return `<p>${missing()}</p>`;
  if (s.error && !s.system) return `<p class="badge failed">${esc(s.error)}</p>`;
  const why = (f) => (s.reasons || {})[f];
  const sys = s.system || {}, ag = s.agent || {}, m = s.model || {}, lim = s.limits || {}, res = s.resources || {};
  const net = s.network || {}, tools = s.tools || {}, env = s.environment || {};
  const agentText = ag.kind === "none" ? `${term("none", tname("none"))}${ag.how ? `<div class="sub">${esc(ag.how)}${verbatim()}</div>` : ""}`
    : ag.kind ? `${term(ag.kind, ag.name || tname(ag.kind))} ${ag.version ? `<code>${esc(ag.version)}</code>` : missing(why("agent.version"))}${ag.how ? `<div class="sub">${esc(ag.how)}${verbatim()}</div>` : ""}`
    : missing(why("agent.kind"));
  const caps = Object.entries(lim.caps || {});
  const parts = [
    `<h3>${t("cfg.system")}</h3>` + kv([
      [t("cfg.system_name"), sys.name ? sysLink(sys.name) : missing(why("system.name"))],
      [t("cfg.version"), sys.version ? `<code>${esc(sys.version)}</code>` : missing(why("system.version"))],
      sys.upstream ? [t("cfg.upstream"), `${link(sys.upstream.repository, sys.upstream.repository)}${sys.upstream.commit ? ` @ <code>${esc(sys.upstream.commit)}</code>` : ""}`] : null,
    ]),
    `<h3>${t("cfg.agent_model")}</h3>` + kv([
      [t("cfg.agent"), agentText],
      [t("cfg.provider"), m.provider ? term(m.provider, m.provider) : missing(why("model.provider"))],
      [t("cfg.model"), m.model ? term(m.model, m.model) : missing(why("model.model"))],
      [t("cfg.effort"), m.effort ? term(m.effort, m.effort) : missing(why("model.effort"))],
    ]),
    `<h3>${t("cfg.limits")}</h3>` + kv([
      [t("cfg.time_limit"), lim.time_limit_hours != null ? t("cfg.hours", { h: fmtNum(lim.time_limit_hours) }) : missing(why("limits.time_limit_hours"))],
      [t("cfg.budget"), lim.budget_usd != null ? `$${fmtNum(lim.budget_usd)}` : `<span class="sub">${t("cfg.no_cap")}</span>`],
      [t("cfg.turns"), capVal(lim.turns)],
      [t("cfg.tokens"), capVal(lim.tokens)],
      caps.length ? [t("cfg.caps"), caps.map(([k, v]) => `<code>${esc(k)}</code> = ${capVal(v)}`).join("<br>")] : null,
      [t("cfg.resources"), res.cpus != null ? t("cfg.res_line", { c: esc(res.cpus), m: esc(res.memory_gb ?? "–"), g: esc(res.gpus ?? "–") }) : missing(why("resources.cpus"))],
    ]),
    `<h3>${t("cfg.network")}</h3>` + kv([
      [t("cfg.shield"), net.shield ? (net.shield === "none" ? `<span class="badge failed">${t("cfg.no_shield")}</span>` : term(net.shield, net.shield)) : missing(why("network.shield"))],
      net.offline ? [t("cfg.offline"), `${term("offline", t("yes"))}`] : null,
      net.deny_hosts?.length ? [t("cfg.deny_hosts"), `<details><summary>${t("cfg.n_hosts", { n: net.deny_hosts.length })}</summary>${esc(net.deny_hosts.join(", "))}</details>`] : null,
      net.blocklist ? [t("cfg.blocklist"), `<code>${esc(net.blocklist)}</code>`] : null,
      net.passthrough_hosts?.length ? [t("cfg.passthrough"), esc(net.passthrough_hosts.join(", "))] : null,
      net.search ? [t("cfg.search"), esc(net.search) + verbatim()] : null,
      net.web_access ? [t("cfg.web"), esc(net.web_access) + verbatim()] : null,
    ]),
    `<h3>${t("cfg.tools")}</h3>` + kv([
      [t("cfg.permissions"), tools.permissions ? esc(tools.permissions) + verbatim() : missing(why("tools.permissions"))],
      tools.settings && Object.keys(tools.settings).length ? [t("cfg.settings"), `<details><summary>${t("cfg.n_settings", { n: Object.keys(tools.settings).length })}</summary>${kv(Object.entries(tools.settings).map(([k, v]) => [`<code>${esc(k)}</code>`, esc(Array.isArray(v) ? v.join(", ") : typeof v === "object" ? JSON.stringify(v) : v)]))}</details>`] : null,
    ]),
    `<h3>${t("cfg.environment")}</h3>` + kv([
      [t("cfg.image"), env.image ? `<code>${esc(env.image)}</code>` : missing(why("environment.image"))],
      env.system_image ? [t("cfg.system_image"), `<code>${esc(env.system_image)}</code>`] : null,
      [t("cfg.official_image"), env.official_task_image ? `${t("yes")}${env.task_image ? ` <code>${esc(env.task_image)}</code>` : ""}` : env.task_image ? `${term(env.mode || "own-image", tname(env.mode || "own-image"))} <code>${esc(env.task_image)}</code>` : t("cfg.own_image")],
      env.preinstalled ? [t("cfg.preinstalled"), esc(L(env.preinstalled)) + (typeof env.preinstalled === "string" ? verbatim() : "")] : null,
    ]),
  ];
  if (s.roles?.length) {
    const rows = s.roles.map((r) => `<tr><td>${r.role === "*" ? t("cfg.all_roles") : esc(r.role)}</td><td>${r.agent ? term(r.agent, r.agent_name || r.agent) : "–"} ${r.agent_version ? `<div class="sub"><code>${esc(r.agent_version)}</code></div>` : ""}</td><td>${r.provider ? term(r.provider, r.provider) : missing()}</td><td>${r.model ? term(r.model, r.model) : "–"}</td><td>${r.effort ? term(r.effort, r.effort) : "–"}</td></tr>`);
    parts.push(`<h3>${t("cfg.roles")}</h3>` + table([t("cfg.role"), t("cfg.agent"), t("cfg.provider"), t("cfg.model"), t("cfg.effort")], rows));
  }
  if (s.world) {
    const w = s.world;
    parts.push(`<h3>${t("cfg.world")}</h3>` + kv([
      [t("cfg.hutian"), `${esc(w.hutian_version || "–")} <code>${esc(w.hutian_commit || "")}</code>`],
      w.entry ? [t("cfg.entry"), term(`entry-${w.entry}`, `researchworld ${w.entry}`)] : null,
      [t("cfg.digest"), w.digest ? `<code>${esc(w.digest)}</code>` : `<span class="sub">${t("cfg.digest_later")}</span>`],
      [t("cfg.world_budget"), Object.keys(w.budget || {}).length ? esc(JSON.stringify(w.budget)) : missing()],
      w.edges?.length ? [t("cfg.edges"), esc(w.edges.map((e) => e.join(" → ")).join("; "))] : null,
    ]));
  }
  const notes = Object.entries(s.notes || {});
  if (notes.length) parts.push(`<details class="notes"><summary>${t("cfg.notes", { n: notes.length })}${verbatim()}</summary>${kv(notes.map(([k, v]) => [`<code>${esc(k)}</code>`, esc(v)]))}</details>`);
  const gaps = (s.missing || []);
  const src = s.derived ? `<p class="note">${t(`cfg.derived.${s.derived}`)}</p>` : `<p class="note">${t("cfg.from_record")}</p>`;
  const gapNote = gaps.length ? `<p class="note">${t("cfg.gaps", { list: gaps.map((g) => `<code>${esc(g)}</code>`).join(", ") })}</p>` : "";
  return `<div class="config">${src}${parts.join("")}${gapNote}</div>`;
}

// ---- tasks ---------------------------------------------------------------------------------------------------

const taskTitle = (x) => (S.lang === "en" ? x.title_en || x.title : x.title || x.title_en) || "";

export function renderTasks(index) {
  const formal = new Set(((index.batches || []).find((b) => b.name === "e2e-formal") || {}).tasks || []);
  const rows = Object.values(index.tasks || {}).filter((x) => x.kind === "e2e").map((x) => `<tr><td><a href="#/task/${enc(x.id)}">${esc(x.id)}</a></td>
    <td>${esc(taskTitle(x))}${S.lang === "zh" && x.title_en ? `<div class="sub">${esc(x.title_en)}</div>` : S.lang === "en" && x.title ? `<div class="sub">${esc(x.title)}</div>` : ""}</td>
    <td>${formal.has(x.id) ? t("tk.formal") : x.id === "s00" ? term("smoke", tname("smoke")) : t("tk.reserve")}</td>
    <td><a href="${compareHref(x.id)}">${t("cmp.link")}</a></td></tr>`);
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.tasks")])}<h2>${t("tk.title")}</h2><p class="note">${t("tk.lead")}</p>
    ${table([t("col.task"), t("col.title"), t("tk.status"), t("cmp.crumb")], rows)}
    <p class="note">${t("tk.benchmarks_elsewhere")} <a href="#/benchmarks">${t("nav.benchmarks")}</a></p>`;
}

function fileBlocks(files, open = false) {
  return (files || []).map((f) => {
    const note = (f.note ? ` <span class="sub">— ${esc(f.note)}${verbatim()}</span>` : "")
      + (f.encoding ? ` <span class="sub">${t("file.encoding", { enc: esc(String(f.encoding).toUpperCase()) })}</span>` : "")
      + (f.text == null && f.unshown ? ` <span class="sub">— ${t(`file.unshown.${f.unshown}`)}</span>` : "");
    return f.text != null
      ? `<details${open ? " open" : ""}><summary>${esc(f.name)} <span class="sub">${t("bytes", { n: esc(f.size) })}</span>${note}</summary><pre>${esc(f.text)}</pre></details>`
      : `<div>${esc(f.name)} <span class="sub">${t("bytes", { n: esc(f.size) })}</span>${note}</div>`;
  }).join("");
}

function paperBlock(p) {
  if (!p) return missing();
  return kv([
    [t("prov.title"), p.title ? esc(p.title) : missing()],
    [t("prov.authors"), p.authors ? esc([].concat(p.authors).join(", ")) : missing()],
    [t("prov.venue"), p.venue ? esc(p.venue) : missing()],
    [t("prov.link"), p.url ? link(p.url) : missing()],
    p.pdf ? [t("prov.pdf"), link(p.pdf)] : null,
    p.code ? [t("prov.code"), link(p.code)] : null,
    p.licence ? [t("prov.licence"), esc(p.licence)] : null,
    p.first_public_date ? [t("prov.first_public"), esc(p.first_public_date)] : null,
  ]);
}

export function renderTask(page) {
  const s = page.settings?.conditions || {};
  const ev = `<p class="note">${t("tk.ev_note")}</p>${fileBlocks(page.evaluator)}`;
  const other = S.lang === "en" ? page.title : page.title_en;
  return `${crumbs(["#/", t("nav.overview")], ["#/tasks", t("nav.tasks")], [null, esc(page.id)])}
    <h2>${esc(page.id)} ${esc(taskTitle(page))}</h2>${other ? `<p class="sub">${esc(other)}</p>` : ""}
    <p><a href="${compareHref(page.id)}">${t("tk.under_conditions")}</a></p>
    ${section(t("tk.provenance"), `<h3>${t("tk.original_paper")}</h3>${paperBlock(page.original)}
      <h3>${t("tk.data_source")}</h3>${page.data ? `<pre class="plain">${esc(page.data)}</pre>${S.lang === "en" ? verbatim() : ""}` : missing()}`)}
    ${section(t("tk.settings"), kv([
      [term("time-cutoff", t("tk.time_cutoff")), `${esc(page.time_cutoff || "–")} <span class="sub">${t("tk.cutoff_note")}</span>`],
      [t("cfg.time_limit"), t("tk.hours_same", { h: esc(s.time_limit_hours ?? "–") })],
      [t("cfg.resources"), t("cfg.res_line", { c: esc(s.cpus ?? "–"), m: esc(s.memory_gb ?? "–"), g: esc(s.gpus ?? "–") })],
      [term("shield", t("cfg.shield")), esc(page.settings?.shield?.mode || "–")],
    ]))}
    ${section(t("it.conditions"), renderConditionSetups(page.conditions))}
    ${section(term("candidate-side", t("tk.candidate")), `<p class="note">${t("tk.candidate_note")}${S.lang === "en" ? verbatim() : ""}</p>${fileBlocks(page.candidate)}`)}
    ${section(term("evaluator-side", t("tk.evaluator")), ev)}`;
}

// ---- compare: one task (E2E task or benchmark item) under every condition (Issue #80) ---------------------------

const compareHref = (key, condition) => `#/compare/${String(key).split("/").map(enc).join("/")}${condition ? `?condition=${enc(condition)}` : ""}`;

export function fmtBytes(n) {
  if (n == null) return "–";
  return n >= 1 << 20 ? `${(n / (1 << 20)).toFixed(1)} MB` : n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : t("bytes", { n: esc(n) });
}

// A long text's summary: its first heading and its opening paragraphs (markdown, later headings skipped) up to
// `max` characters.
export function summarize(text, max = 420) {
  const src = String(text || "").replace(/\r/g, "");
  let title = "", fence = false;
  const paras = [[]];
  for (const raw of src.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("```")) { fence = !fence; continue; }
    if (fence) continue;
    const h = /^#{1,6}\s+(.*)$/.exec(line);
    if (h && !title && !paras[0].length) { title = h[1].trim(); continue; }
    if (h || !line) { if (paras[paras.length - 1].length) paras.push([]); continue; }
    paras[paras.length - 1].push(line.replace(/^[-*>]\s+/, ""));
  }
  let para = "";
  for (const p of paras.filter((x) => x.length)) {
    if (para && para.length + p.join(" ").length > max) break;
    para = para ? `${para} ¶ ${p.join(" ")}` : p.join(" ");
    if (para.length >= max / 2) break;
  }
  if (!para && !title) para = src.trim();
  const cut = para.length > max;
  return { title, body: cut ? `${para.slice(0, max).trimEnd()}…` : para, cut: cut || src.trim().length > title.length + para.length + 8 };
}

// A text shown as its summary, with its full text behind a button.
function summaryBlock(name, text, note = "", expand = true) {
  const s = summarize(text);
  return `<div class="summary">${name ? `<div class="sname"><code>${esc(name)}</code>${note ? ` <span class="sub">— ${esc(note)}</span>` : ""}</div>` : ""}` +
    `${s.title ? `<strong>${esc(s.title)}</strong>` : ""}${s.body ? `<p>${esc(s.body)}</p>` : ""}` +
    `${expand ? `<details><summary>${t("cmp.expand")}</summary><pre>${esc(text)}</pre></details>` : ""}</div>`;
}

const isPdf = (p) => /\.pdf$/i.test(String(p || ""));
const isImage = (p) => /\.(png|jpe?g|gif|svg|webp)$/i.test(String(p || ""));
const fileUrl = (base, runId, path) => `${base}files/${enc(runId)}/${String(path).split("/").map(enc).join("/")}`;

// Why a file is not published, in the page's language.
const AUDIT_TIERS = ["no_hit", "hit_not_used", "needs_review", "hit_and_used", "task_rule"];
const AUDIT_COUNTS = [["hits", "audit.n.hits"], ["used", "audit.n.used"], ["needs_review", "audit.n.needs_review"], ["same_year", "audit.n.same_year"], ["shield_misses", "audit.n.shield_misses"]];

export function auditLine(a) {
  if (a.error) return `<span class="missing">${t("audit.error")}</span> <code>${esc(a.error)}</code>`;
  const tier = AUDIT_TIERS.includes(a.tier) ? `<strong>${t(`audit.tier.${a.tier}`)}</strong><div class="sub">${t(`audit.means.${a.tier}`)}</div>` : `<code>${esc(a.tier ?? "–")}</code>`;
  const counts = AUDIT_COUNTS.filter(([k]) => a[k] != null).map(([k, label]) => `${t(label)} ${esc(a[k])}`).join(" · ");
  return `${tier}${counts ? `<div class="sub">${counts}</div>` : ""}`;
}

export function fileWhy(f) {
  const r = f.reason || f.file_reason;
  if (r === "credential") return t("dl.why.credential");
  if (r === "unreadable-pdf") return t("dl.why.unreadable_pdf");
  if (r === "extra-resource") return t("dl.why.extra_resource");
  if (r === "extra-resource-unchecked") return t("dl.why.extra_resource_unchecked");
  if (r === "too-large") return t("dl.why.too_large", { mb: esc(f.limit ?? "–") });
  if (r === "over-budget") return t("dl.why.over_budget", { mb: esc(f.limit ?? "–") });
  if (r === "too-many-files") return t("dl.why.too_many", { n: esc(f.count ?? "–"), limit: esc(f.limit ?? "–") });
  if (r === "not-collected") return t("dl.why.not_collected");
  if (r === "not-in-batch") return t("dl.why.not_in_batch");
  if (r === "unreadable") return t("dl.why.unreadable");
  return esc(r || "");
}

// Buttons that open a published file: a PDF in a new tab or inside the page, a text or an image inside the page.
function viewer(url, path, big = false) {
  const open = `<a class="btn${big ? " primary" : ""}" href="${esc(url)}" target="_blank" rel="noopener" data-open="${esc(url)}"${isPdf(path) ? ' data-type="application/pdf"' : ""}>${isPdf(path) ? t("cmp.open_pdf") : t("cmp.open")}</a>`;
  const inline = isPdf(path) ? `<button type="button" data-embed="${esc(url)}">${t("cmp.show_inline")}</button>`
    : isImage(path) ? `<button type="button" data-image="${esc(url)}">${t("cmp.show_inline")}</button>`
    : `<button type="button" data-preview="${esc(url)}">${t("cmp.show_text")}</button>`;
  return `<span class="actions">${open}${inline}</span><div class="viewer" hidden></div>`;
}

function outputLine(f, base, runId, big = false) {
  const role = f.role || f.key;
  const label = role ? `<span class="tag">${t(`cmp.role.${role}`)}</span> ` : "";
  const name = `<code>${esc(f.path)}</code> <span class="sub">${fmtBytes(f.size)}</span>`;
  if (f.status === "published") return `<div class="output${big ? " key" : ""}">${label}${name} ${viewer(fileUrl(base, runId, f.path), f.path, big)}</div>`;
  return `<div class="output${big ? " key" : ""}">${label}${name} <span class="sub">${f.status === "withheld" ? t("dl.withheld") : t("dl.listed")}: ${fileWhy(f)}</span></div>`;
}

const OUTPUTS_SHOWN = 400;

function runBody(r, base) {
  const sp = r.spend || {};
  const tokens = sp.tokens ? Object.values(sp.tokens).reduce((a, v) => a + (v || 0), 0) : null;
  const scores = (r.scores || []).filter((s) => s.summary || !(r.review_pending || []).includes(s.evaluator)).map((s) => `<div>${term(s.evaluator, tname(s.evaluator))}${roleTag(s.evaluator)}: <strong>${scoreText(s)}</strong>` +
    (relativeText(s) ? `<div class="sub">${relativeText(s)}</div>` : "") + (s.result ? `<details><summary>${t("run.rationale")}</summary><pre>${esc(JSON.stringify(s.result, null, 1))}</pre></details>` : "") + `</div>`)
    .concat((r.review_pending || []).length ? [pendingParse(r.review_pending)] : [])
    .concat((r.unscored || []).filter((e) => !(r.review_pending || []).includes(e)).map((e) => `<div>${term(e, tname(e))}: <span class="missing">${t("run.unscored")}</span></div>`));
  const key = r.key_outputs || [];
  const [lead, ...rest] = key;
  const others = r.outputs || [];
  const otherList = others.slice(0, OUTPUTS_SHOWN).map((f) => outputLine(f, base, r.run_id)).join("");
  return `<div class="status">${runStatus(r)}${r.purpose !== "evaluation" ? ` <span class="sub">(${purpose(r.purpose)})</span>` : r.unfinished ? ` ${runPurpose(r)}` : ""}</div>
    ${r.continued_from ? `<div class="sub">${t("run.continued", { run: esc(r.continued_from.run_id), cp: esc(r.continued_from.checkpoint), at: r.continued_from.fraction == null ? "–" : `${Math.round(r.continued_from.fraction * 100)}%`, change: esc(r.continued_from.change || "control"), role: esc(r.continued_from.role || "–") })}</div>` : ""}
    ${(r.skillpacks || []).length ? `<div class="sub">${t("run.skillpacks", { list: esc(r.skillpacks.map((p) => `${p.id} ${String(p.digest).slice(0, 8)}`).join(", ")) })}</div>` : ""}
    ${(r.extra_resources || []).length ? `<div class="sub">${t("run.extra", { list: esc(r.extra_resources.map((p) => `${p.asset} ${String(p.digest).slice(0, 8)}`).join(", ")) })}</div>` : ""}
    ${r.error ? `<details class="error"><summary>${t("run.error")}</summary><pre>${esc(r.error)}</pre></details>` : ""}
    <div class="scores">${scores.join("") || `<span class="sub">${t("run.no_scores")}</span>`}</div>
    <div class="metrics"><span title="${t("metric.wall_s")}">⏱ ${fmtDuration(sp.wall_s)}</span><span title="${t("metric.tokens")}">${t("cmp.tokens", { n: tokens == null ? "–" : kTokens(tokens) })}</span><span title="${t("col.cost")}">${fmtUsd(sp)}</span></div>
    <div class="keyout"><h4>${t("cmp.key_output")}</h4>${lead ? outputLine(lead, base, r.run_id, true) + rest.map((f) => outputLine(f, base, r.run_id)).join("") : `<span class="sub">${r.live || r.status === "running" ? t("cmp.still_running") : t("cmp.no_key_output")}</span>`}</div>
    ${others.length ? `<details class="others"><summary>${t("cmp.other_outputs", { n: others.length })}</summary>${otherList}${others.length > OUTPUTS_SHOWN ? `<p class="sub">${t("cmp.more_on_run", { n: others.length - OUTPUTS_SHOWN })}</p>` : ""}</details>` : ""}
    <p class="sub">${runLink(r.run_id)} · ${fmtTime(r.started_at)}</p>`;
}

// A reason shown by its first sentence, the rest behind a click.
function shortText(text, max = 140) {
  const s = String(text || "");
  const m = /^(.{20,}?[。.;；])(\s|$)/.exec(s);
  const head = m && m[1].length <= max ? m[1] : s.length > max ? `${s.slice(0, max)}…` : s;
  return head === s ? `<p class="sub">${esc(s)}</p>` : `<details class="sub"><summary>${esc(head)}</summary>${esc(s)}</details>`;
}

// One card: a condition (or the runs outside every condition) on this task, its runs behind tabs.
function card(c, base, focus) {
  const runs = c.runs || [];
  const head = c.condition ? `<header>${condLabel(c.condition)}<div class="sub">${sysLink(c.system)}${c.model && c.model !== "pending" ? ` · ${term(c.model, c.model)}` : ""}${c.effort && c.effort !== "pending" ? ` · ${term(c.effort, c.effort)}` : ""}</div></header>`
    : `<header><strong>${t("cmp.other_runs")}</strong></header>`;
  const concluded = c.concluded ? `<p class="note">${t("rep.concluded", { why: esc(L({ zh: c.concluded.reason, en: c.concluded.reason_en || c.concluded.reason })) })}</p>` : "";
  if (!runs.length) {
    const why = c.unsupported ? `${statusBadge("unsupported")}${shortText(L({ zh: c.unsupported.reason, en: c.unsupported.reason_en || c.unsupported.reason }))}`
      : `<span class="sub">${esc(tname("not-started"))}</span>`;
    return `<article class="card empty${focus ? " focus" : ""}" id="cmp-${esc(c.condition || "other")}">${head}${why}${concluded}</article>`;
  }
  const id = esc(c.condition || "other");
  const tabs = runs.length > 1 ? `<nav class="runtabs" role="tablist">${runs.map((r, i) => `<button type="button" role="tab" data-tab="${id}" data-idx="${i}" aria-selected="${i === 0}" title="${esc(r.run_id)}">${esc((r.started_at || r.run_id).slice(5, 16).replace("T", " "))}${r.purpose !== "evaluation" ? ` · ${esc(tname(r.purpose))}` : ""}</button>`).join("")}</nav>` : "";
  const bodies = runs.map((r, i) => `<div class="runbody" data-tab="${id}" data-idx="${i}"${i ? " hidden" : ""}>${runBody(r, base)}</div>`).join("");
  return `<article class="card${focus ? " focus" : ""}" id="cmp-${id}">${head}${concluded}${runs.length > 1 ? `<p class="sub">${t("cmp.n_runs", { n: runs.length })}</p>` : ""}${tabs}${bodies}</article>`;
}

function taskPart(cmp, task) {
  if (cmp.kind === "e2e") {
    const files = task.candidate || [];
    const main = files.find((f) => f.name === "TASK.md") || files[0];
    const s = task.settings?.conditions || {};
    return `${main?.text != null ? summaryBlock("", main.text, "", false) : missing()}
      <details><summary>${t("cmp.full_task")}</summary>${fileBlocks(files, true)}${kv([
        [t("cfg.time_limit"), t("tk.hours_same", { h: esc(s.time_limit_hours ?? "–") })],
        [t("cfg.resources"), t("cfg.res_line", { c: esc(s.cpus ?? "–"), m: esc(s.memory_gb ?? "–"), g: esc(s.gpus ?? "–") })],
      ])}</details>`;
  }
  if (task.error) return `<p class="badge failed">${t("it.unreadable")}: ${esc(task.error)}</p>`;
  const prompt = task.prompt || [];
  const main = prompt.find((f) => f.name === "TASK.md") || prompt[0];
  const st = task.settings || {};
  return `${main ? summaryBlock("", main.text, "", false) : missing()}
    <p class="sub">${t("it.deliverables")}: ${(st.deliverables || []).map((d) => `<code>${esc(d)}</code>`).join(", ") || "–"} · ${t("cfg.time_limit")}: ${hoursText(st.limits?.time_limit_hours)}</p>
    <details><summary>${t("cmp.full_task")}</summary>${fileBlocks(prompt, true)}
      <h3>${t("it.files", { n: (task.files || []).length, kb: fmtNum((task.files || []).reduce((a, f) => a + (f.size || 0), 0) / 1024, 1) })}</h3>
      ${(task.files || []).slice(0, 200).map((f) => `<div><code>${esc(f.path)}</code> <span class="sub">${fmtBytes(f.size)}</span></div>`).join("")}</details>`;
}

function refFile(r, base) {
  const url = r.file ? `${base}${String(r.file).split("/").map(enc).join("/")}` : null;
  const head = `<code>${esc(r.name)}</code> <span class="sub">${fmtBytes(r.size)}${r.note ? ` — ${esc(r.note)}` : ""}</span>`;
  if (r.text != null) return summaryBlock(r.name, r.text, r.note);
  if (url) return `<div class="output${isPdf(r.name) ? " key" : ""}">${head} ${viewer(url, r.name, isPdf(r.name))}</div>`;
  return `<div class="output">${head} <span class="sub">${r.file_reason ? fileWhy(r) : r.unshown ? t(`file.unshown.${r.unshown}`) : ""}</span></div>`;
}

function referencePart(cmp, task, base) {
  if (cmp.kind === "e2e") {
    return `<h3>${t("tk.original_paper")}</h3>${paperBlock(task.original)}
      <p class="sub">${term("time-cutoff", t("tk.time_cutoff"))}: ${esc(task.time_cutoff || "–")}</p>
      ${(task.evaluator || []).map((f) => (f.text != null ? summaryBlock(f.name, f.text) : refFile(f, base))).join("")}`;
  }
  return `<h3>${t("tk.original_paper")}</h3>${originalOf(task.shield?.source)}
    ${(task.references || []).map((r) => refFile(r, base)).join("") || `<p class="sub">${t("none")}</p>`}`;
}

// The compare page: the task (summary, full text behind a button), every condition's runs side by side with their
// key outputs first, and the reference material. `task` is the task's or the item's page.
export function renderCompare(cmp, task = {}, base = "data/", focus = "") {
  const title = cmp.kind === "e2e" ? `${esc(cmp.key)} ${esc(taskTitle(task))}` : `${esc(tname(cmp.benchmark))} · ${esc(cmp.item)}`;
  const crumbsHtml = cmp.kind === "e2e"
    ? crumbs(["#/", t("nav.overview")], ["#/tasks", t("nav.tasks")], [`#/task/${enc(cmp.key)}`, esc(cmp.key)], [null, t("cmp.crumb")])
    : crumbs(["#/", t("nav.overview")], ["#/items", t("nav.items")], [itemHref(cmp.key), esc(cmp.key)], [null, t("cmp.crumb")]);
  const cols = cmp.columns || [];
  const withRuns = cols.filter((c) => c.runs?.length).length;
  const cards = [...cols.filter((c) => c.runs?.length), ...cols.filter((c) => !c.runs?.length)].map((c) => card(c, base, c.condition === focus)).join("");
  const other = (cmp.other_runs || []).length ? card({ condition: null, runs: cmp.other_runs }, base, false) : "";
  return `${crumbsHtml}<h2>${t("cmp.title", { title })}</h2>
    <p class="lead">${cmp.kind === "e2e" ? `<a href="#/task/${enc(cmp.key)}">${t("cmp.task_page")}</a>` : `<a href="${itemHref(cmp.key)}">${t("cmp.item_page")}</a>`}${(task.batches || []).length ? ` · ${t("col.batch")}: ${task.batches.map(batchLink).join(", ")}` : ""}</p>
    ${section(term("candidate-side", t("cmp.task")), taskPart(cmp, task))}
    ${section(t("cmp.systems"), `<p class="note">${t("cmp.systems_note", { n: withRuns, m: cols.length })}</p><div class="cards">${cards}${other}</div>`)}
    ${section(term("evaluator-side", t("cmp.reference")), referencePart(cmp, task, base))}`;
}

// ---- run configuration of every condition on one task (E2E task or benchmark item) -----------------------------

const hoursText = (h) => (h != null ? t("cfg.hours", { h: fmtNum(h) }) : missing());
function netText(n) {
  if (!n || !n.shield) return missing();
  if (n.shield === "none") return `<span class="badge failed">${t("cfg.no_shield")}</span>`;
  return term(n.shield, n.shield) + (n.offline && n.shield !== "offline" ? ` · ${term("offline", "offline")}` : "") +
    (n.deny_hosts?.length ? `<div class="sub">${t("cfg.n_hosts", { n: n.deny_hosts.length })}</div>` : "");
}
function envText(e) {
  if (!e) return missing();
  const mode = e.mode ? term(e.mode, tname(e.mode)) : t("cfg.own_image");
  return `${mode}${e.task_image ? `<div class="sub"><code>${esc(e.task_image)}</code></div>` : ""}`;
}

// One row per condition: what a run of that condition gets on this task (its system's `item_setup`), and the full
// configuration behind a click.
export function renderConditionSetups(conds) {
  const rows = (conds || []).map((c) => {
    const s = c.setup;
    const head = `<th class="rowhead">${condLabel(c.name)}</th><td>${sysLink(c.system)}</td>`;
    if (!s) return `<tr>${head}<td colspan="7">${term("pending", tname("pending"))}${c.pending?.length ? `<div class="sub">${esc(c.pending.join(", "))}</div>` : ""}</td></tr>`;
    if (s.error) return `<tr>${head}<td colspan="7"><span class="badge failed">${esc(s.error)}</span></td></tr>`;
    const ag = s.agent || {}, m = s.model || {}, lim = s.limits || {}, res = s.resources || {}, w = s.world;
    const roles = (s.roles || []).map((r) => (r.role === "*" ? t("cfg.all_roles") : r.role));
    const all = (s.roles || []).some((r) => r.role === "*");
    const rw = w ? `${w.entry ? term(`entry-${w.entry}`, `researchworld ${w.entry}`) : ""}<div class="sub">${all ? t("cfg.all_roles") : `${t("it.n_roles", { n: roles.length })}: ${esc(roles.join(", "))}`}</div>` : "–";
    return `<tr>${head}
      <td>${ag.kind ? term(ag.kind, ag.name || ag.kind) : missing()}${ag.version ? `<div class="sub"><code>${esc(ag.version)}</code></div>` : ""}</td>
      <td>${m.model ? term(m.model, m.model) : missing()}${m.effort ? `<div class="sub">${term(m.effort, m.effort)}</div>` : ""}</td>
      <td>${lim.time_limit_hours != null ? hoursText(lim.time_limit_hours) : missing((s.reasons || {})["limits.time_limit_hours"])}${lim.budget_usd != null ? `<div class="sub">$${fmtNum(lim.budget_usd)}</div>` : ""}</td>
      <td>${res.cpus != null ? t("cfg.res_line", { c: esc(res.cpus), m: esc(res.memory_gb ?? "–"), g: esc(res.gpus ?? "–") }) : `<span class="sub">${t("it.system_default")}</span>`}</td>
      <td>${netText(s.network)}</td><td>${envText(s.environment)}</td><td>${rw}</td></tr>
      <tr class="detail"><td colspan="9"><details><summary>${t("it.full_setup", { name: esc(c.name) })}</summary>${renderSetup(s)}</details></td></tr>`;
  });
  return `<p class="note">${t("it.conditions_note")}</p>` + table([t("col.condition"), t("col.system"), t("cfg.agent"), `${t("cfg.model")} / ${t("cfg.effort")}`, t("cfg.time_limit"), t("cfg.resources"), t("cfg.network"), t("cfg.environment"), t("it.entry_roles")], rows);
}

export function renderJudges(judges) {
  const j = (judges || {})[S.lang] || (judges || {}).zh || (judges || {}).en;
  if (!j) return `<p class="sub">${t("it.no_judges")}</p>`;
  return `<p class="note">${t("it.judges_note", { path: `<code>${esc(j.path)}</code>` })}</p>` +
    j.sections.map((sec) => `<details><summary>${esc(sec.split("\n")[0].replace(/^## /, ""))}</summary><pre class="plain">${esc(sec)}</pre></details>`).join("");
}

// ---- benchmark items ---------------------------------------------------------------------------------------------

export function renderItems(index, f = {}) {
  const all = index.items || [];
  const list = all.filter((x) => (!f.benchmark || x.benchmark === f.benchmark) && (!f.batch || (x.batches || []).includes(f.batch)));
  const benches = [...new Set(all.map((x) => x.benchmark))];
  const batches = [...new Set(all.flatMap((x) => x.batches || []))];
  const form = `<form class="filters" id="filters" aria-label="${t("filter.label")}">
    <select name="benchmark" aria-label="${t("f.benchmark")}">${options(benches, f.benchmark, t("f.benchmark"), tname)}</select>
    <select name="batch" aria-label="${t("f.batch")}">${options(batches, f.batch, t("f.batch"))}</select></form>`;
  const rows = list.map((x) => `<tr><td><a href="${itemHref(x.key)}">${esc(x.item)}</a>${x.error ? ` <span class="badge failed">${t("it.unreadable")}</span>` : ""}</td>
    <td><a href="#/benchmark/${enc(x.benchmark)}">${esc(tname(x.benchmark))}</a></td><td>${hoursText(x.time_limit_hours)}</td>
    <td>${[x.offline ? term("offline", "offline") : "", x.image ? t("it.has_image") : ""].filter(Boolean).join(" · ") || "–"}</td>
    <td>${(x.batches || []).map(batchLink).join(", ") || "–"}</td>
    <td>${x.runs ? `${x.runs} · ${x.latest ? `${runLink(x.latest)} ${statusBadge(x.latest_status, x.latest_live)}` : ""}` : "–"}</td>
    <td><a href="${compareHref(x.key)}">${t("cmp.link")}</a></td></tr>`);
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.items")])}<h2>${t("it.title", { n: list.length })}</h2>
    <p class="note">${t("it.lead")}</p>${form}
    ${table([t("it.item"), t("bm.name"), t("cfg.time_limit"), t("cfg.network") + " / " + t("cfg.environment"), t("col.batch"), t("nav.runs"), t("cmp.crumb")], rows)}`;
}

function originalOf(src) {
  if (!src || !Object.keys(src).length) return missing();
  return kv([
    src.title ? [t("prov.title"), esc(src.title)] : null,
    src.authors ? [t("prov.authors"), esc([].concat(src.authors).join(", "))] : null,
    src.time_cutoff ? [term("time-cutoff", t("tk.time_cutoff")), esc(src.time_cutoff)] : null,
    ...["abs_url", "pdf_url", "html_url", "openreview_url", "neurips_url"].filter((k) => src[k]).map((k) => [esc(k), link(src[k])]),
    src.arxiv_id ? ["arXiv", esc(src.arxiv_id)] : null,
    src.code_repository ? [t("prov.code"), [].concat(src.code_repository).map((u) => link(u)).join("<br>")] : null,
  ]);
}

// One benchmark item: what the system gets, the item's settings, every condition's configuration on it, the
// reference material and its runs. `bench` is the benchmark's page (its JUDGES.md sections).
export function renderItem(page, bench = {}) {
  const name = esc(tname(page.benchmark));
  const head = `${crumbs(["#/", t("nav.overview")], ["#/items", t("nav.items")], [`#/items?benchmark=${enc(page.benchmark)}`, name], [null, esc(page.item)])}
    <h2>${name} · ${esc(page.item)}</h2>
    <p class="lead"><a href="${compareHref(page.key)}">${t("tk.under_conditions")}</a> · <a href="#/benchmark/${enc(page.benchmark)}">${t("it.benchmark_page")}</a>${(page.batches || []).length ? ` · ${t("col.batch")}: ${page.batches.map(batchLink).join(", ")}` : ""}</p>`;
  if (page.error) return `${head}<p class="badge failed">${t("it.unreadable")}: ${esc(page.error)}</p>${section(t("it.conditions"), renderConditionSetups(page.conditions))}${section(t("nav.runs"), renderRunsTable(page.runs || []))}`;
  const st = page.settings || {}, lim = st.limits || {};
  const files = page.files || [];
  const bytes = files.reduce((a, f) => a + (f.size || 0), 0);
  const fileRows = files.map((f) => `<tr><td><code>${esc(f.path)}</code></td><td>${esc(f.size)}</td></tr>`);
  return `${head}
    ${section(term("candidate-side", t("it.candidate")), `<p class="note">${t("it.prompt_note")}${verbatim()}</p>${fileBlocks(page.prompt, true)}
      <h3>${t("it.files", { n: files.length, kb: fmtNum(bytes / 1024, 1) })}</h3>${(page.file_notes || []).map((n) => `<p class="note">${esc(n)}${verbatim()}</p>`).join("")}
      ${files.length ? `<details${files.length <= 20 ? " open" : ""}><summary>${t("it.file_list")}</summary>${table([t("dl.file"), t("dl.bytes")], fileRows)}</details>` : `<p class="sub">${t("none")}</p>`}`)}
    ${section(t("it.settings"), kv([
      [t("cfg.time_limit"), hoursText(lim.time_limit_hours)],
      [t("cfg.resources"), lim.cpus != null || lim.memory_gb != null ? t("cfg.res_line", { c: esc(lim.cpus ?? "–"), m: esc(lim.memory_gb ?? "–"), g: "–" }) : `<span class="sub">${t("it.system_default")}</span>`],
      [t("cfg.network"), st.offline ? `${term("offline", "offline")} <span class="sub">${t("it.offline_note")}</span>` : `${term("shield", t("it.shielded"))} <span class="sub">${t("it.shielded_note")}</span>`],
      [t("cfg.image"), st.image ? `<code>${esc(st.image)}</code> <span class="sub">${t("it.image_note")}</span>` : `<span class="sub">${t("it.no_image")}</span>`],
      [t("it.deliverables"), (st.deliverables || []).map((d) => `<code>${esc(d)}</code>`).join(", ") || "–"],
      [t("it.work"), st.work ? term(`work-${st.work}`, st.work) : "–"],
      (st.inputs || []).length ? [t("it.mounts"), st.inputs.map((i) => `<code>${esc(i.path)}</code>`).join("<br>")] : null,
      st.software ? [t("it.software"), t("yes")] : null,
    ]) + `<p class="note">${t("it.settings_note")}</p>`)}
    ${section(t("it.conditions"), renderConditionSetups(page.conditions))}
    ${section(term("evaluator-side", t("it.reference")), `<h3>${t("tk.original_paper")}</h3>${originalOf(page.shield?.source)}
      <h3>${t("it.reference_files")}</h3>${fileBlocks(page.references) || `<p class="sub">${t("none")}</p>`}
      <h3>${t("it.evaluator_record")}</h3><pre class="plain">${esc(JSON.stringify(page.evaluator || {}, null, 1))}</pre>
      <h3>${t("it.blocklist_source")}</h3><p class="note">${t("it.blocklist_note")}</p><pre class="plain">${esc(JSON.stringify({ ...(page.shield?.extra || {}), probe_url: page.shield?.probe_url }, null, 1))}</pre>`)}
    ${section(t("it.judges"), renderJudges(bench.judges))}
    ${section(t("nav.runs"), renderRunsTable(page.runs || []))}`;
}

// ---- conditions ----------------------------------------------------------------------------------------------

export function renderConditions(index) {
  const runs = index.runs || [];
  const rows = (index.conditions.items || []).map((c) => {
    const mine = runs.filter((r) => r.condition === c.name && r.purpose === "evaluation");
    const ag = c.setup?.agent || {};
    return `<tr><th class="rowhead">${condLabel(c.name)}</th><td>${sysLink(c.system)}</td>
      <td>${ag.kind ? term(ag.kind, ag.name) : term("pending", tname("pending"))}${ag.version ? ` <code>${esc(ag.version)}</code>` : ""}</td>
      <td>${c.provider ? term(c.provider, c.provider) : "–"}</td><td>${c.model && c.model !== "pending" ? term(c.model, tname(c.model)) : term("pending", tname("pending"))}</td>
      <td>${c.effort && c.effort !== "pending" ? term(c.effort, c.effort) : "–"}</td><td>${mine.length} / ${mine.filter((r) => r.status === "completed").length}</td></tr>`;
  });
  const notes = (S.lang === "en" && index.conditions.notes_en?.length ? index.conditions.notes_en : index.conditions.notes) || [];
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.conditions")])}<h2>${t("cd.title")}</h2>
    <p class="note">${t("cd.lead", { src: index.conditions.source ? link(index.conditions.source, "Issue #31") : "conditions.yaml" })} ${term("condition-name", t("cd.naming"))}</p>
    ${table([t("col.condition"), t("col.system"), t("cfg.agent"), t("cfg.provider"), t("cfg.model"), t("cfg.effort"), t("cd.eval_runs")], rows)}
    ${notes.length ? `<h3>${t("cd.notes")}</h3><ul>${notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}`;
}

function conditionPacks(c) {
  const all = c.skillpack || [], roles = Object.entries(c.skillpacks || {});
  if (!all.length && !roles.length) return null;
  const ids = (list) => list.map((id) => `<code>${esc(id)}</code>`).join(", ");
  const lines = [...(all.length ? [t("cd.skillpacks_all", { list: ids(all) })] : []), ...roles.map(([role, list]) => t("cd.skillpacks_role", { role: `<code>${esc(role)}</code>`, list: ids(list) }))];
  return [t("cd.skillpacks"), lines.map((l) => `<div>${l}</div>`).join("")];
}

export function renderCondition(index, name) {
  const c = (index.conditions.items || []).find((x) => x.name === name);
  if (!c) return `<p>${t("cd.none", { name: esc(name) })}</p>`;
  const runs = (index.runs || []).filter((r) => r.condition === name);
  const desc = S.lang === "en" ? c.description_en || c.description : c.description;
  const notes = S.lang === "en" ? c.notes_en || c.notes : c.notes;
  const totals = (index.matrix || []).map((m) => {
    const x = m.totals[name] || { tasks: 0, done: 0, running: 0, failed: 0 };
    return `<tr><td><a href="#/matrix/${enc(m.batch)}?condition=${enc(name)}">${esc(m.batch)}</a></td><td>${x.done} / ${x.tasks}</td><td>${x.running}</td><td>${x.failed}</td></tr>`;
  });
  return `${crumbs(["#/", t("nav.overview")], ["#/conditions", t("nav.conditions")], [null, esc(name)])}
    <h2>${esc(name)}</h2><p class="lead">${esc(L(c.full_name))}</p><p>${esc(desc || "")}</p>${notes ? `<p class="note">${esc(notes)}</p>` : ""}
    ${kv([[t("col.system"), sysLink(c.system)], [t("cfg.agent"), c.agent === "pending" ? term("pending", tname("pending")) : term(c.agent, c.agent)],
      [t("cfg.provider"), c.provider ? term(c.provider, c.provider) : "–"], [t("cfg.model"), c.model === "pending" ? term("pending", tname("pending")) : term(c.model, tname(c.model))],
      [t("cfg.effort"), c.effort === "pending" ? term("pending", tname("pending")) : term(c.effort, c.effort)],
      c.pending?.length ? [t("cd.pending"), esc(c.pending.join(", "))] : null, conditionPacks(c)])}
    ${section(t("cd.planned"), `<p class="note">${t("cd.planned_note")}</p>${c.setup ? renderSetup(c.setup) : `<p>${t("cd.no_planned")}</p>`}`)}
    ${section(t("cd.progress"), table([t("col.batch"), t("mx.done"), t("state.running"), t("state.failed")], totals))}
    ${section(t("cd.runs", { n: runs.length }), renderRunsTable(runs))}`;
}

// ---- systems ---------------------------------------------------------------------------------------------------

function provRow(label, v, render) {
  if (v && typeof v === "object" && v.none) return [label, `<span class="sub">${t("prov.none")}</span>: ${esc(v.none)}${verbatim()}`];
  return [label, v && (typeof v !== "object" || Object.keys(v).length) ? render(v) : missing()];
}
const paperText = (p) => `${p.title ? `<strong>${esc(p.title)}</strong>` : missing()}${p.authors ? `<div class="sub">${esc([].concat(p.authors).join(", "))}</div>` : ""}<div>${esc(p.venue || "")} ${p.url ? link(p.url) : ""}</div>`;
const repoText = (r) => `${link(r.url, r.url)}${r.commit ? ` @ <code>${esc(r.commit)}</code>` : ""}${r.release ? ` (${esc(r.release)})` : ""}${r.licence ? `<div class="sub">${t("prov.licence")}: ${esc(r.licence)}</div>` : ""}`;

export function renderSystems(index) {
  const runs = index.runs || [];
  const rows = Object.values(index.systems || {}).map((s) => `<tr><th class="rowhead">${sysLink(s.name)}<div class="sub"><code>${esc(s.name)}</code></div></th>
    <td>${esc(L(s.source?.summary) || s.description)}</td><td><code>${esc(s.version || "–")}</code></td>
    <td>${(s.conditions || []).map((c) => condLabel(c, false)).join(" ") || "–"}</td><td>${runs.filter((r) => r.system === s.name).length}</td></tr>`);
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.systems")])}<h2>${t("sy.title")}</h2><p class="note">${t("sy.lead")} ${term("baseline", t("sy.baselines"))}</p>
    ${table([t("col.system"), t("sy.what"), t("cfg.version"), t("nav.conditions"), t("nav.runs")], rows)}`;
}

export function renderSystem(index, name) {
  const s = (index.systems || {})[name];
  if (!s) return `<p>${t("sy.none", { name: esc(name) })}</p>`;
  const src = s.source || {};
  const comps = (src.components || []).map((c) => `<tr><td>${esc(c.name)}</td><td><code>${esc(c.version || "–")}</code></td><td>${esc(c.licence || "–")}</td><td>${c.url ? link(c.url) : esc(c.note || "")}</td></tr>`);
  const runs = (index.runs || []).filter((r) => r.system === name);
  const agg = ((index.aggregates || {}).evaluation || { system: [] }).system.find((x) => x.system === name);
  return `${crumbs(["#/", t("nav.overview")], ["#/systems", t("nav.systems")], [null, esc(tname(name))])}
    <h2>${esc(tname(name))}</h2><p class="lead">${esc(L(src.summary) || s.description)}</p>
    ${section(t("sy.provenance"), kv([
      provRow(t("prov.paper"), src.paper, paperText),
      provRow(t("prov.repository"), src.repository, repoText),
      [t("cfg.version"), `<code>${esc(s.version || "–")}</code>`],
      provRow(t("cfg.environment"), src.environment, (e) => esc(L(e))),
    ]) + (comps.length ? `<h3>${t("sy.components")}</h3>` + table([t("sy.component"), t("cfg.version"), t("prov.licence"), t("prov.link")], comps) : ""))}
    ${section(t("nav.conditions"), (s.conditions || []).map((c) => `<div>${condLabel(c)}</div>`).join("") || `<p class="sub">${t("none")}</p>`)}
    ${agg ? section(t("sy.results"), renderAggregates([agg], "system")) : ""}
    ${systemDefects(index, name)}
    ${section(t("sy.runs", { n: runs.length }), renderRunsTable(runs))}`;
}

// ---- benchmarks ------------------------------------------------------------------------------------------------

export function renderBenchmarks(index) {
  const rows = Object.values(index.tasks || {}).filter((x) => x.kind === "benchmark").map((b) => {
    const p = b.provenance || {};
    return `<tr><th class="rowhead"><a href="#/benchmark/${enc(b.id)}">${esc(tname(b.id))}</a><div class="sub"><code>${esc(b.id)}</code></div></th>
      <td>${p.paper?.none ? `<span class="sub">${t("prov.none")}</span>` : p.paper?.url ? link(p.paper.url, p.paper.title) : missing()}</td>
      <td><a href="#/items?benchmark=${enc(b.id)}">${b.plan_items ?? b.items ?? "–"}</a></td><td>${b.items ?? "–"}</td><td>${esc(p.licence?.code || "–")}</td></tr>`;
  });
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.benchmarks")])}<h2>${t("bm.title")}</h2><p class="note">${t("bm.lead")}</p>
    ${table([t("bm.name"), t("prov.paper"), t("bm.items_plan"), t("bm.items_all"), t("bm.code_licence")], rows)}`;
}

export function renderBenchmark(index, page) {
  const p = page.provenance || {};
  const batches = (index.batches || []).filter((b) => (b.tasks || []).some((k) => taskUnit(k) === page.id));
  const items = [...new Set(batches.flatMap((b) => b.tasks.filter((k) => taskUnit(k) === page.id)))];
  const ev = `<p class="note">${t("bm.ev_note")}</p>${fileBlocks(page.evaluator)}`;
  return `${crumbs(["#/", t("nav.overview")], ["#/benchmarks", t("nav.benchmarks")], [null, esc(tname(page.id))])}
    <h2>${esc(tname(page.id))}</h2><p class="lead">${esc(S.terms[page.id] ? L(S.terms[page.id].means) : "")}</p>
    ${section(t("bm.provenance"), kv([
      provRow(t("prov.paper"), p.paper, paperText),
      provRow(t("prov.repository"), p.repository, repoText),
      provRow(t("bm.dataset"), p.dataset, (d) => `${link(d.url, d.url)}${d.revision ? ` @ <code>${esc(d.revision)}</code>` : ""}${d.note ? `<div class="sub">${esc(d.note)}${verbatim()}</div>` : ""}`),
      [t("bm.licence_code"), p.licence?.code ? esc(p.licence.code) + verbatim() : missing()],
      [t("bm.licence_data"), p.licence?.data ? esc(p.licence.data) + verbatim() : missing()],
      [t("bm.manifest_date"), esc(page.manifest_date || "–")],
    ]) + `<p class="note">${t("bm.from_manifest", { path: `<code>${esc(page.path)}/MANIFEST.yaml</code>` })}</p>`)}
    ${section(t("bm.subset"), kv([
      [t("bm.rule"), p.subset?.rule ? esc(p.subset.rule) + verbatim() : missing()],
      p.subset?.decision ? [t("bm.decision"), esc(p.subset.decision) + verbatim()] : null,
      [t("bm.items_used"), p.subset?.count != null ? esc(p.subset.count) : missing()],
      [t("col.batch"), batches.map((b) => batchLink(b.name)).join(", ") || "–"],
    ]) + (items.length && !items[0].endsWith("/all") ? `<details><summary>${t("bm.item_list", { n: items.length })}</summary><p>${items.map((k) => `<a href="${itemHref(k)}">${esc(k.split("/").slice(1).join("/"))}</a>`).join(" · ")}</p></details>` : "")
      + `<p><a href="#/items?benchmark=${enc(page.id)}">${t("bm.all_items")}</a></p>`)}
    ${section(term("evaluator-side", t("tk.evaluator")), ev)}
    ${section(t("it.judges"), renderJudges(page.judges))}
    ${section(t("nav.runs"), renderRunsTable((page.runs || [])))}`;
}

// ---- runs ---------------------------------------------------------------------------------------------------------

export function renderRunsTable(runs) {
  const body = runs.map((r) => {
    const ag = r.setup?.agent || {};
    return `<tr><td>${runLink(r.run_id)}</td><td>${sysLink(r.system)}</td>
    <td>${ag.kind ? term(ag.kind, ag.name) : why(r, "setup")}${ag.version ? `<div class="sub"><code>${esc(ag.version)}</code></div>` : ""}</td>
    <td>${r.setup?.model?.model ? term(r.setup.model.model, r.setup.model.model) : why(r, "setup")}</td>
    <td>${taskLink(r.task, r.task_kind)}</td><td>${runPurpose(r)}</td><td>${r.condition ? condLabel(r.condition, false) : why(r, "condition")}${r.condition && !r.condition_given ? `<div class="sub">${t("run.inferred")}</div>` : ""}</td>
    <td>${runStatus(r)}</td><td>${fmtTime(r.started_at)}</td><td>${fmtDuration(r.spend?.wall_s)}</td><td>${fmtUsd(r.spend)}</td><td>${mainScore(r)}</td></tr>`;
  });
  return table([t("col.run"), t("col.system"), t("cfg.agent"), t("cfg.model"), t("col.task"), t("col.purpose"), t("col.condition"), t("col.status"), t("col.start"), t("col.elapsed"), t("col.cost"), t("col.score")], body, t("run.none"));
}

export function renderTimeline(runs, generatedAt) {
  const pts = runs.filter((r) => r.started_at);
  if (!pts.length) return `<p class="sub">${t("run.none")}</p>`;
  const ts = (s) => Date.parse(s);
  const now = ts(generatedAt) || Date.now();
  const lo = Math.min(...pts.map((r) => ts(r.started_at)));
  const hi = Math.max(now, ...pts.map((r) => ts(r.ended_at || generatedAt) || now));
  const span = Math.max(hi - lo, 1);
  const bars = pts.slice().sort((a, b) => ts(a.started_at) - ts(b.started_at)).map((r) => {
    const a = ts(r.started_at), b = r.ended_at ? ts(r.ended_at) : now;
    const left = ((a - lo) / span) * 100, width = Math.max(((b - a) / span) * 100, 0.3);
    const cls = statusClass(r.shown_status, r.live);
    return `<div class="tl-row"><span class="tl-label">${runLink(r.run_id)}</span><span class="tl-track"><a class="tl-bar ${cls}" href="#/run/${enc(r.run_id)}" style="left:${left.toFixed(2)}%;width:${width.toFixed(2)}%" title="${esc(r.run_id)}: ${esc(r.shown_status)}, ${fmtTime(r.started_at)} → ${fmtTime(r.ended_at)}"></a></span></div>`;
  }).join("");
  return `<p class="note">${t("tl.note", { from: fmtTime(new Date(lo).toISOString().replace(/\.\d+Z$/, "Z")), to: fmtTime(generatedAt) })}</p><div class="timeline">${bars}</div>`;
}

export function renderRuns(index, f = {}) {
  const runs = applyFilters(index.runs || [], f);
  const extra = [];
  if (index.unrecorded?.length) extra.push(t("run.unrecorded", { n: index.unrecorded.length, list: index.unrecorded.map(esc).join(", ") }));
  if (index.reviews?.count) extra.push(t("run.reviews", { n: index.reviews.count, list: Object.entries(index.reviews.by_reviewer).map(([k, v]) => `${esc(tname(k))} ${v}`).join(", ") }));
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.runs")])}<h2>${t("run.title", { n: runs.length })}</h2>${renderFilters(index, f)}
    ${renderRunsTable(runs)}${section(t("tl.title"), renderTimeline(runs, index.generated_at))}
    ${extra.length ? section(t("run.other"), `<ul>${extra.map((e) => `<li>${e}</li>`).join("")}</ul>`) : ""}`;
}

export function renderRun(page, dataBase = "data/") {
  const sp = page.spend || {};
  const scores = (page.scores || []).filter((s) => s.summary || !(page.review_pending || []).includes(s.evaluator)).map((s) => `<tr><td>${term(s.evaluator, tname(s.evaluator))}${roleTag(s.evaluator)}<div class="sub">${esc(s.version || "")}</div></td>
    <td>${scoreText(s)}${relativeText(s) ? `<div class="sub">${relativeText(s)}</div>` : ""}${s.summary?.label ? `<div class="sub">${esc(s.summary.label)}${S.lang === "en" ? verbatim() : ""}</div>` : ""}</td>
    <td>${Object.entries(s.summary?.extras || {}).map(([k, v]) => `${extraName(k)} ${fmtNum(v)}`).join(", ") || "–"}</td>
    <td>${s.result ? `<details><summary>${t("run.rationale")}</summary><pre>${esc(JSON.stringify(s.result, null, 1))}</pre></details>` : "–"}</td></tr>`)
    .concat((page.review_pending || []).map((e) => `<tr><td>${term(e, tname(e))}${roleTag(e)}</td><td>${pendingTag()}<div class="sub">${t("rel.pending_parse_note")}</div></td><td>–</td><td>–</td></tr>`))
    .concat((page.unscored || []).filter((e) => !(page.review_pending || []).includes(e)).map((e) => `<tr><td>${term(e, tname(e))}</td><td><span class="missing">${t("run.unscored")}</span><div class="sub">${t("run.unscored_note")}</div></td><td>–</td><td>–</td></tr>`));
  const files = (page.deliverables || []).map((f) => {
    const href = `${dataBase}files/${enc(page.run_id)}/${String(f.path).split("/").map(enc).join("/")}`;
    const name = f.status === "published" ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(f.path)}</a>` : esc(f.path);
    return `<tr><td>${t(`dl.${f.kind}`)}${f.key ? ` <span class="tag">${t("cmp.key_output")}</span>` : ""}</td><td>${name}</td><td>${esc(f.size ?? "–")}</td><td>${f.status === "published" ? t("dl.published") : `${f.status === "withheld" ? t("dl.withheld") : t("dl.listed")}: ${fileWhy(f)}`}</td></tr>`;
  });
  const audit = page.audit ? auditLine(page.audit) : why(page, "audit");
  const ag = page.setup?.agent || {};
  return `${crumbs(["#/", t("nav.overview")], ["#/runs", t("nav.runs")], [null, esc(page.run_id)])}
    <h2>${t("run.one", { id: esc(page.run_id) })}</h2>${page.task && !String(page.task).endsWith("/all") ? `<p><a href="${compareHref(page.task, page.condition)}">${t("cmp.from_run")}</a></p>` : ""}
    <p class="lead">${sysLink(page.system)} · ${ag.kind ? term(ag.kind, `${ag.name}${ag.version ? " " + ag.version : ""}`) : why(page, "setup")} · ${page.setup?.model?.model ? term(page.setup.model.model, tname(page.setup.model.model)) : "–"} · ${statusBadge(page.shown_status, page.live)}</p>
    ${section(t("run.progress"), kv([
      [t("col.status"), `${runStatus(page)}${page.detached ? ` <span class="sub">${t("run.detached")}</span>` : ""}`],
      [t("col.task"), taskLink(page.task, page.task_kind)],
      [t("run.purpose_batch_condition"), `${runPurpose(page)} · ${esc(page.batch || "–")} · ${page.condition ? condLabel(page.condition) : why(page, "condition")}`],
      [t("run.start_end"), `${fmtTime(page.started_at)} · ${fmtTime(page.ended_at)}`],
      [t("run.elapsed"), `${fmtDuration(sp.wall_s)}${sp.model_s != null ? ` ${t("run.model_time", { d: fmtDuration(sp.model_s) })}` : ""}${sp.turns != null ? ` ${t("run.turns", { n: esc(sp.turns) })}` : ""}${sp.requests != null ? ` ${t("run.requests", { n: esc(sp.requests) })}` : ""}`],
      [term("price-list", t("col.cost")), fmtUsd(sp)],
      [term("tokens", t("run.tokens")), fmtTokens(sp.tokens)],
      sp.unavailable && Object.keys(sp.unavailable).length ? [t("run.unavailable"), `<ul class="plain">${Object.entries(sp.unavailable).map(([k, v]) => `<li>${t(`metric.${k}`)}: <span class="sub">${esc(v)}</span></li>`).join("")}</ul>`] : null,
      [term("heartbeat", t("run.heartbeat")), `${fmtTime(page.heartbeat_at)} · ${fmtTime(page.last_activity)}`],
      [term("audit", t("run.audit")), audit],
      page.system_status ? [t("run.system_report"), `<code>${esc(JSON.stringify(page.system_status))}</code>`] : null,
      page.world_id ? [term("world", t("run.world")), page.world_page ? link(page.world_page, page.world_id) : esc(page.world_id)] : null,
      page.error ? [t("run.error"), `<code>${esc(page.error)}</code>`] : null,
    ]))}
    ${section(t("run.config"), renderSetup(page.setup))}
    ${page.docker_environment ? section("Docker", `<pre>${esc(JSON.stringify(page.docker_environment, null, 2))}</pre>`) : ""}
    ${section(t("run.results"), scores.length ? table([t("run.evaluator"), t("col.score"), t("run.extras"), t("run.basis")], scores) : `<p class="sub">${t("run.no_scores")}</p>`)}
    ${section(t("run.deliverables"), files.length ? table([t("dl.kind"), t("dl.file"), t("dl.bytes"), t("dl.public")], files) : `<p class="sub">${t("run.no_deliverables")}</p>`)}`;
}

// ---- results ------------------------------------------------------------------------------------------------------

export function renderAggregates(rows, key) {
  const rank = (e) => (PRIMARY_EVALUATORS.includes(e) ? PRIMARY_EVALUATORS.indexOf(e) : e === "rubric-judge" ? 90 : 50);
  const evs = [...new Set(rows.flatMap((r) => Object.keys(r.scores || {})))].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
  const head = [key === "condition" ? t("col.condition") : t("col.system"), t("res.runs"), t("res.completed"), t("res.failed"), t("res.running"),
    ...evs.map((e) => `${term(e, tname(e))}${roleTag(e)}<div class="sub">${t("res.mean_sd")}</div>`), t("res.cost"), t("res.wall")];
  const body = rows.map((r) => `<tr><th class="rowhead">${key === "condition" ? condLabel(r[key]) : sysLink(r[key])}</th><td>${r.runs}</td><td>${r.completed}</td><td>${r.failed}</td><td>${r.running}</td>` +
    evs.map((e) => {
      const s = r.scores[e];
      if (!s) return "<td>–</td>";
      const sd = s.variance != null ? ` ± ${fmtNum(Math.sqrt(s.variance))}` : "";
      const rel = s.ratio?.n ? `<div class="sub">${t("rel.mean_ratio", { ratio: fmtNum(s.ratio.mean, 2), n: s.ratio.n })}</div>` : "";
      const solved = s.solved ? `<div class="sub">${t("rel.solved_of", { y: s.solved.yes, n: s.solved.n })}</div>` : "";
      return `<td title="${esc(s.label)}, max ${esc(s.max)}">${fmtNum(s.mean)}${sd} (${s.n})${rel}${solved}</td>`;
    }).join("") +
    `<td>${r.usd != null ? t("res.usd_runs", { usd: Number(r.usd).toFixed(2), n: r.usd_runs }) : "–"}</td><td>${fmtDuration(r.wall_s)}</td></tr>`);
  return table(head, body, t("run.none"));
}

const PROCESS = ["wall_s", "net_wall_s", "model_s", "turns", "requests", "cache_read", "tokens", "usd", "equivalent_usd"];

export function renderProcess(rows, key) {
  const fmt = { wall_s: fmtDuration, net_wall_s: fmtDuration, model_s: fmtDuration, turns: (v) => fmtNum(v, 1), requests: (v) => fmtNum(v, 1), cache_read: kTokens, tokens: kTokens,
    usd: (v) => `$${Number(v).toFixed(2)}`, equivalent_usd: (v) => `$${Number(v).toFixed(2)}` };
  const head = [key === "condition" ? t("col.condition") : t("col.system"), t("res.finished"), ...PROCESS.map((m) => `${t(`metric.${m}`)}<div class="sub">${t("res.mean_n")}</div>`)];
  const body = rows.map((r) => {
    const p = r.process || { runs: 0 };
    return `<tr><th class="rowhead">${key === "condition" ? condLabel(r[key]) : sysLink(r[key])}</th><td>${p.runs}</td>` +
      PROCESS.map((m) => { const e = p[m] || {}; return e.mean == null ? `<td>–</td>` : `<td>${fmt[m](e.mean)} <span class="sub">(${e.n}/${p.runs})</span></td>`; }).join("") + "</tr>";
  });
  return table(head, body, t("run.none")) + `<p class="note">${t("res.process_note")}</p>`;
}

const usd2 = (v) => (v == null ? "–" : `$${Number(v).toFixed(2)}`);
const pct = (v) => (v == null ? "–" : `${(Number(v) * 100).toFixed(0)}%`);
const pm = (s) => (s == null || s.mean == null ? "–" : `${fmtNum(s.mean)}${s.variance != null ? ` ± ${fmtNum(Math.sqrt(s.variance))}` : ""} (${s.n})`);

// the cost against the score of each cell (condition x task), Issue #118: n and spread with every mean, a cost per
// score point where the mean score is above zero, else the reason
export function renderCostScore(cells) {
  const head = [t("col.task"), t("col.condition"), t("cs.positions"), t("cs.runs"), t("cs.score"), t("metric.requests"), t("metric.cache_read"),
    t("metric.model_s"), t("cs.list_usd"), `${t("cs.per_point")}<div class="sub">${t("cs.per_point_sub")}</div>`];
  const body = cells.map((c) => {
    const evs = Object.entries(c.scores || {});
    const p = c.process || {};
    const failed = (c.run_status || []).filter((r) => r.status !== "completed");
    return `<tr><td>${taskLink(c.task)}${(c.credits || []).map((x) => `<div class="sub">${creditTag(x)}</div>`).join("")}</td><th class="rowhead">${condLabel(c.condition)}</th>` +
      `<td>${c.positions ? esc(c.positions.length) : "–"}</td>` +
      `<td title="${esc(failed.map((r) => `${r.run_id}: ${r.status}${r.reason ? ` (${r.reason})` : ""}`).join("; "))}">${c.completed}/${c.runs}</td>` +
      `<td>${evs.length ? evs.map(([e, s]) => `${term(e, tname(e))}: ${pm(s)}`).join("<br>") : "–"}</td>` +
      `<td>${pm(p.requests)}</td><td>${p.cache_read?.mean == null ? "–" : kTokens(p.cache_read.mean)}</td><td>${p.model_s?.mean == null ? "–" : fmtDuration(p.model_s.mean)}</td>` +
      `<td>${p.list_usd?.mean == null ? "–" : `${usd2(p.list_usd.mean)} <span class="sub">(${p.list_usd.n})</span>`}</td>` +
      `<td>${evs.length ? evs.map(([e, s]) => (s.usd_per_point != null ? `${term(e, tname(e))}: ${usd2(s.usd_per_point)}` : `${term(e, tname(e))}: <span class="sub">${t(`cs.why.${s.usd_per_point_why}`)}</span>`)).join("<br>") : "–"}</td></tr>`;
  });
  return table(head, body, t("run.none")) + `<p class="note">${t("cs.note")}</p>`;
}

// where a cell's requests went, by role: the share of requests and of cache reads, and what the turns did
export function renderRoleSplit(cells) {
  const head = [t("col.task"), t("col.condition"), t("cs.role"), t("cs.requests_mean"), t("cs.requests_share"), t("cs.cache_share"),
    t("cs.class.committed"), t("cs.class.interaction"), t("cs.class.none")];
  const body = [];
  for (const c of cells.filter((x) => x.by_role)) {
    for (const [role, e] of Object.entries(c.by_role.roles)) {
      const k = e.turn_classes || {};
      body.push(`<tr><td>${taskLink(c.task)}</td><th class="rowhead">${condLabel(c.condition)}</th><td><code>${esc(role)}</code></td><td>${fmtNum(e.requests_mean, 1)}</td>` +
        `<td>${pct(e.requests_share)}</td><td>${pct(e.cache_read_share)}</td><td>${pct(k.committed)}</td><td>${pct(k.interaction)}</td><td>${pct(k.none)}</td></tr>`);
    }
  }
  return table(head, body, t("cs.no_roles")) + `<p class="note">${t("cs.roles_note")}</p>`;
}

export function renderSpend(runs) {
  const by = {};
  for (const r of runs) {
    const k = r.purpose || "–";
    const e = (by[k] ||= { runs: 0, usd: 0, priced: 0, wall: 0, sub: 0 });
    e.runs += 1;
    if (r.spend?.usd != null) { e.usd += r.spend.usd; e.priced += 1; }
    if (r.spend?.usd_basis === "subscription") e.sub += 1;
    e.wall += r.spend?.wall_s || 0;
  }
  const rows = Object.entries(by).map(([k, e]) => `<tr><th class="rowhead">${purpose(k)}</th><td>${e.runs}</td><td>${t("res.usd_priced", { usd: e.usd.toFixed(2), n: e.priced })}</td><td>${e.sub}</td><td>${fmtDuration(e.wall)}</td></tr>`);
  return table([t("col.purpose"), t("res.runs"), term("price-list", t("res.cost")), term("subscription", t("res.subscription_runs")), t("res.wall_total")], rows) +
    `<p class="note">${t("res.spend_note")}</p>`;
}

export function renderResults(index, f = {}) {
  const p = f.purpose || "evaluation";
  const agg = (index.aggregates || {})[p] || { condition: [], system: [] };
  const purposes = Object.keys(index.aggregates || {});
  const tabs = purposes.map((x) => `<a href="#/results?purpose=${enc(x)}"${x === p ? ' class="active"' : ""}>${x === "all" ? t("res.all_purposes") : esc(tname(x))}</a>`).join("");
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.results")])}<h2>${t("res.title")}</h2>
    <nav class="tabs">${tabs}</nav><p class="note">${t("res.note")}</p>${rankingLink()}
    ${section(t("rel.title"), renderE2EScores(index.e2e_scores || []))}
    ${section(t("res.by_condition"), renderAggregates(agg.condition, "condition"))}
    ${section(t("res.by_system"), renderAggregates(agg.system, "system"))}
    ${section(t("res.process_by_condition"), renderProcess(agg.condition, "condition"))}
    ${section(t("res.process_by_system"), renderProcess(agg.system, "system"))}
    ${section(t("cs.title"), renderCostScore(agg.cells || []))}
    ${section(t("cs.roles_title"), renderRoleSplit(agg.cells || []))}
    ${section(t("res.spend"), renderSpend((index.runs || []).filter((r) => p === "all" || r.purpose === p)))}`;
}

// ---- plan: theses and phases (Issue #152; only the latest design, Issue #163) ----------------------------------------

const phaseTitle = (p) => L({ zh: p.title, en: p.title_en || p.title });
const phaseBadge = (state) => `<span class="badge ${{ done: "done", running: "running", pending: "stale", "not-started": "stale" }[state] || "stale"}">${t(`ph.state.${state}`)}</span>`;
const meter = (done, cells, cls = "done") => (cells ? `<span class="meter" title="${done} / ${cells}"><span class="${cls}" style="width:${Math.min(100, (done / cells) * 100).toFixed(1)}%"></span></span>` : "");

function blockBox(b, index) {
  const batches = b.batches === "pending" ? term("pending", t("ph.pending")) : b.batches.map(batchLink).join(", ");
  const conds = b.conditions === "pending" ? term("pending", t("ph.pending")) : b.conditions.map((c) => condLabel(c, false)).join(", ");
  const p = b.progress || {};
  const why = b.why ? `<div class="sub">${esc(L({ zh: b.why, en: b.why_en || b.why }))}</div>` : "";
  const prog = p.state === "pending" ? "" : `<div class="sub">${t("ph.cells_done", { d: p.done, n: p.cells })}${p.running ? ` · ${t("mx.running_n", { n: p.running })}` : ""}${p.failed ? ` · ${t("mx.failed_n", { n: p.failed })}` : ""}${p.credited ? ` · ${t("ph.credited_n", { n: p.credited })}` : ""}</div>${meter(p.done, p.cells)}`;
  return `<li><strong>${esc(L({ zh: b.title, en: b.title_en || b.title }))}</strong><div class="sub">${t("col.batch")}: ${batches} · ${t("col.condition")}: ${conds}</div>${why}${prog}</li>`;
}

// ---- the four phases at a glance (Issue #259): state, cells by state, where to look, what is missing; phase 2's candidates ------

const ITEM_STATE_ORDER = ["completed", "failed", "unsupported"];
const stateChips = (states) => [...CELL_STATES, ...ITEM_STATE_ORDER].filter((k) => states[k]).map((k) => `<span class="chip">${cellState(k)} <strong>${states[k]}</strong></span>`).join(" ");

function phaseLinks(links) {
  return (links || []).map((l) => `<div><a href="#/${l.page}/${enc(l.batch)}">${t(l.page === "cells" ? "ph.link_cells" : "ph.link_matrix", { batch: esc(l.batch), n: l.tasks })}</a></div>`).join("") || `<span class="sub">–</span>`;
}

export function unrankedCells(g) {
  const rows = (g.unranked || []).map((u) => `<tr><td>${esc(u.condition)}</td><td><a href="#/task/${enc(u.task)}">${esc(u.task)}</a></td>
    <td><a href="${cellHref(u.batch, u.condition, u.task)}">${cellState(u.state)}</a></td><td>${u.run ? runLink(u.run) : "–"}</td>
    <td>${t(["scored", "awaiting-review", "not-reviewed"].includes(u.state) ? "ph.why.unranked_paper" : `ph.why.${u.state}`)}${u.rerunning ? ` ${t("ph.why.rerunning")}` : ""}${u.reason ? `<div class="sub">${esc(L({ zh: u.reason, en: u.reason_en || u.reason }))}</div>` : ""}</td></tr>`);
  if (!rows.length) return "";
  return `<details class="notes" open><summary>${t("ph.unranked", { n: rows.length })}</summary>${table([t("col.condition"), t("col.task"), t("ph.col_cell_state"), t("col.run"), t("ph.col_why")], rows)}</details>`;
}

const outcomeCell = (r) => `${t(`ph.cand.outcome.${r.outcome}`)}${r.confidence ? ` <span class="sub">(${esc(r.confidence)})</span>` : ""}${r.agree === false ? ` <span class="sub">${t("ph.cand.orders_differ")}</span>` : ""}`;

export function renderCandidates(c) {
  if (!c) return "";
  const vars = { subject: esc(c.subject), control: esc(c.control), max: c.max, min: c.min };
  const reason = (r) => t(r.supplement ? "ph.cand.supplement" : "ph.cand.lost");
  const rows = (c.rows || []).map((r) => `<tr><td><a href="#/task/${enc(r.task)}">${esc(r.task)}</a><div class="sub">${esc(L({ zh: r.title, en: r.title_en || r.title }))}</div></td>
    <td><a href="#/ranking/${enc(r.task)}">${outcomeCell(r)}</a></td><td>${r.subject != null ? fmtNum(r.subject, 2) : "–"}</td>
    <td>${r.control != null ? fmtNum(r.control, 2) : "–"}</td><td>${reason(r)}</td></tr>`);
  const status = !c.ranking ? t("ph.cand_no_ranking") : c.ready ? t("ph.cand_ready", vars) : t("ph.cand_provisional", { ...vars, d: c.decided, n: c.total });
  return `${section(t("ph.cand_title"), `<p class="note">${status}</p><p class="note">${t("ph.cand_rule", vars)}</p>` +
    (rows.length ? table([t("col.task"), t("ph.cand.judgment", vars), t("ph.cand.ref", { c: c.subject }), t("ph.cand.ref", { c: c.control }), t("ph.cand.reason")], rows) + `<p class="note">${t("ph.cand_ref_note")}</p>` : `<p class="sub">${t("ph.cand_none")}</p>`))}`;
}

export function renderPhaseProgress(index) {
  const plan = index.conditions.plan || {};
  const phases = plan.phases || [], prog = plan.progress || {};
  if (!phases.length) return "";
  const rows = phases.map((p) => {
    const g = prog[p.id] || {};
    const open = (g.undecided || []).filter((b) => b.why).map((b) => `<div class="sub">${esc(L({ zh: b.why, en: b.why_en || b.why }))}</div>`).join("");
    const body = g.cells ? (g.ranked != null
      ? `${t("ph.ranked", { d: g.ranked, n: g.cells })}${meter(g.ranked, g.cells)}<div class="sub">${t("ph.ranked_note")}</div>${unrankedCells(g)}<div class="sub">${t("ph.stanford_ref", { d: g.scored, n: g.cells, w: g.with_paper - g.scored })}</div><div class="chips">${stateChips(g.states || {})}</div>`
      : `${t("ph.with_result", { d: g.with_result, n: g.cells })}${meter(g.with_result, g.cells)}<div class="chips">${stateChips(g.states || {})}</div>`) : `<span class="sub">${t("ph.no_cells")}</span>`;
    const need = p.state === "done" ? "" : p.state === "running" ? (open ? `<div class="sub">${t("ph.missing")}</div>${open}` : "") : `<div class="sub">${t("ph.prereq")}</div>${open || `<span class="sub">–</span>`}`;
    return `<tr${p.id === plan.current ? ' class="focus"' : ""}><th class="rowhead"><a href="#phase-${enc(p.id)}">${esc(phaseTitle(p))}</a><div class="sub">${esc(p.source || "")}</div></th>
      <td>${phaseBadge(p.state)}${p.id === plan.current ? `<div class="sub">▶ ${t("ph.current")}</div>` : ""}</td><td>${body}</td><td>${phaseLinks(g.links)}</td><td>${need}</td></tr>`;
  });
  const cand = phases.map((p) => renderCandidates((prog[p.id] || {}).candidates)).join("");
  return `${section(t("ph.progress_title"), `<p class="note">${t("ph.progress_note")}</p>` +
    table([t("ph.col_phase"), t("ph.col_state"), t("ph.col_progress"), t("ph.col_where"), t("ph.col_missing")], rows))}${cand}`;
}

export function renderPlanSummary(index) {
  const plan = index.conditions.plan || {};
  const phases = plan.phases || [], theses = plan.theses || [];
  if (!phases.length) return "";
  const thesisCards = theses.map((th, i) => {
    const mine = phases.filter((p) => p.thesis === th.id);
    return `<article class="card"><header><strong>${t("ph.thesis_n", { n: i + 1 })}: ${esc(L({ zh: th.title, en: th.title_en || th.title }))}</strong></header>
      <p>${esc(L({ zh: th.text, en: th.text_en || th.text }))}</p>
      <p class="sub">${t("ph.served_by")}: ${mine.map((p) => `${esc(phaseTitle(p))} ${phaseBadge(p.state)}`).join(" · ") || "–"}</p></article>`;
  }).join("");
  const phaseCards = phases.map((p, i) => {
    const current = p.id === plan.current;
    return `<article class="card phase${current ? " focus" : ""}" id="phase-${esc(p.id)}"><header><strong>${esc(phaseTitle(p))}</strong>
      <div>${phaseBadge(p.state)}${current ? ` <span class="badge running">${t("ph.current")}</span>` : ""}${p.source ? ` <span class="sub">${esc(p.source)}</span>` : ""}</div></header>
      <p>${esc(L({ zh: p.summary, en: p.summary_en || p.summary }))}</p>
      ${p.cells ? `<div class="sub">${t("ph.cells_done", { d: p.done, n: p.cells })}${p.running ? ` · ${t("mx.running_n", { n: p.running })}` : ""}${p.credited ? ` · ${t("ph.credited_n", { n: p.credited })}` : ""}</div>${meter(p.done, p.cells)}` : ""}
      ${p.pending_blocks ? `<div class="sub">${t("ph.blocks_pending", { n: p.pending_blocks })}</div>` : ""}
      <ul class="plain blocks">${p.runs.map((b) => blockBox(b, index)).join("")}</ul></article>`;
  }).join("");
  return `${section(t("ph.theses"), `<div class="cards">${thesisCards}</div>`)}
    ${section(t("ph.phases"), `<p class="note">${t("ph.note")}</p><div class="cards">${phaseCards}</div>`)}`;
}

// ---- E2E scores against the original papers (Issue #142, #152) -----------------------------------------------------------

export function renderE2EScores(rows) {
  const body = [];
  for (const e of rows || []) {
    for (const [cond, c] of Object.entries(e.conditions || {})) {
      const st = c.stanford, ai = c.ai_scientist, ru = c.rubric;
      const stanford = st ? `<strong>${fmtNum(st.value)}</strong> / ${fmtNum(st.max)} <span class="sub">${t("rel.vs_original", { ratio: fmtNum(st.ratio, 2), original: fmtNum(e.original.stanford, 1) })}</span><div>${st.solved != null ? `<strong>${t(st.solved ? "rel.solved" : "rel.not_solved")}</strong>` : ""}</div>`
        : c.stanford_pending_parse ? `${pendingTag()}` : `<span class="sub">${t("rel.no_stanford")}</span>`;
      const rerun = c.latest?.rerunning
        ? `<div><span class="badge running" title="${esc(t("rel.rerun_scores_from", { run: c.run_id, status: c.status }))}">${term("rerun-in-progress", t("rel.rerunning"))} ●</span> ${runLink(c.latest.run_id)}</div><div class="sub">${t("rel.rerun_scores_from", { run: esc(c.run_id), status: esc(c.status) })}</div>` : "";
      body.push(`<tr><td>${taskLink(e.task, "e2e")}</td><th class="rowhead">${condLabel(cond)}</th><td>${rerun}${c.latest?.rerunning ? "" : runLink(c.run_id)}${c.runs > 1 ? `<div class="sub">${t("mx.n_runs", { n: c.runs })}</div>` : ""}</td>
        <td>${e.original.stanford ?? "–"}<div class="sub">${t("rel.solve_line", { line: e.solve_line ?? "–" })}</div></td><td>${stanford}</td>
        <td>${ai ? `${fmtNum(ai.value)} / ${fmtNum(ai.max)}${ai.ratio != null ? ` <span class="sub">${t("rel.vs_original", { ratio: fmtNum(ai.ratio, 2), original: fmtNum(e.original.ai_scientist, 1) })}</span>` : ""}` : "–"}</td>
        <td>${ru ? `${fmtNum(ru.value)} / ${fmtNum(ru.max)}` : "–"}</td></tr>`);
    }
  }
  const head = [t("col.task"), t("col.condition"), t("col.run"), `${term("stanford-agentic-reviewer", tname("stanford-agentic-reviewer"))} (${t("rel.original")})`,
    `${term("stanford-agentic-reviewer", tname("stanford-agentic-reviewer"))}${roleTag("stanford-agentic-reviewer")}`,
    `${term("ai-scientist-reviewer", tname("ai-scientist-reviewer"))}${roleTag("ai-scientist-reviewer")}`, `${term("rubric-judge", tname("rubric-judge"))}${roleTag("rubric-judge")}`];
  return `<p class="note">${t("rel.note")}</p>` + table(head, body, t("run.none"));
}

// ---- the phase 1 interim-results chart (Issue #203) -------------------------------------------------------------------
// Per task, each scored system's Stanford score as a dot against the original paper (solid) and the solve line (dashed).
// The data (`index.phase1`) and the geometry are those of dashboard/phase1.py, which draws the static copy of the release.

export const P1 = { W: 1100, H: 420, LEFT: 56, RIGHT: 16, TOP: 16, BOTTOM: 34, BAND: 0.8, R: 5.5 };

export function p1Marker(kind, x, y, r, attrs) {
  const d = r * 1.15, f = (v) => v.toFixed(2);
  if (kind === "square") return `<rect x="${f(x - r)}" y="${f(y - r)}" width="${f(2 * r)}" height="${f(2 * r)}" ${attrs}/>`;
  let pts = null;
  if (kind === "diamond") pts = [[0, -d * 1.25], [d * 1.25, 0], [0, d * 1.25], [-d * 1.25, 0]];
  else if (kind === "triangle") pts = [[0, -d * 1.2], [d * 1.15, d], [-d * 1.15, d]];
  else if (kind === "down") pts = [[0, d * 1.2], [d * 1.15, -d], [-d * 1.15, -d]];
  else if (kind === "plus" || kind === "cross") {
    const a = d * 1.2, b = d * 0.45;
    pts = [[-b, -a], [b, -a], [b, -b], [a, -b], [a, b], [b, b], [b, a], [-b, a], [-b, b], [-a, b], [-a, -b], [-b, -b]];
    if (kind === "cross") { const k = Math.sqrt(0.5); pts = pts.map(([px, py]) => [(px - py) * k, (px + py) * k]); }
  }
  if (pts) return `<polygon points="${pts.map(([px, py]) => `${f(x + px)},${f(y + py)}`).join(" ")}" ${attrs}/>`;
  return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" ${attrs}/>`;
}

const p1Y = (ch, v) => P1.TOP + ((ch.y.max - v) / (ch.y.max - ch.y.min)) * (P1.H - P1.TOP - P1.BOTTOM);
function p1Band(ch, i) {
  const width = (P1.W - P1.LEFT - P1.RIGHT) / ch.tasks.length;
  return [P1.LEFT + i * width + (width * (1 - P1.BAND)) / 2, P1.LEFT + i * width + (width * (1 + P1.BAND)) / 2];
}
export function p1Dots(ch) {
  const pos = Object.fromEntries(ch.systems.map((s, j) => [s.condition, j]));
  const m = Math.max(1, ch.systems.length);
  return ch.cells.filter((c) => c.score != null && c.condition in pos).map((c) => {
    const [l, r] = p1Band(ch, ch.tasks.indexOf(c.task));
    return { ...c, x: +(l + ((r - l) / m) * (pos[c.condition] + 0.5)).toFixed(2), y: +p1Y(ch, c.score).toFixed(2) };
  });
}
const p1Fixed = (v) => (v == null ? "–" : Number(v).toFixed(2));
const p1Series = (s) => `var(--series-${s.slot})`;
const p1Mark = (s, x, y, r) => p1Marker(s.marker, x, y, r, `style="fill:${p1Series(s)};stroke:var(--panel);stroke-width:2"`);

export function renderPhase1Chart(index) {
  const ch = index.phase1;
  if (!ch) return "";
  const scored = ch.cells.filter((c) => c.score != null);
  if (!ch.tasks.length || !scored.length) return section(t("p1.title", { n: ch.tasks.length }), `<p class="sub">${t("p1.empty")}</p>`, "phase1-chart");
  const orig = Object.fromEntries(ch.originals.map((o) => [o.task, o]));
  const sys = Object.fromEntries(ch.systems.map((s) => [s.condition, s]));
  const grid = ch.y.ticks.map((v) => `<line class="p1-grid" x1="${P1.LEFT}" x2="${P1.W - P1.RIGHT}" y1="${p1Y(ch, v).toFixed(2)}" y2="${p1Y(ch, v).toFixed(2)}"/><text class="p1-tick" x="${P1.LEFT - 8}" y="${(p1Y(ch, v) + 4).toFixed(2)}" text-anchor="end">${v}</text>`).join("");
  const bars = ch.originals.map((o, i) => {
    const [l, r] = p1Band(ch, i);
    const line = (v, cls) => (v == null ? "" : `<line class="${cls}" x1="${l.toFixed(2)}" x2="${r.toFixed(2)}" y1="${p1Y(ch, v).toFixed(2)}" y2="${p1Y(ch, v).toFixed(2)}"/>`);
    return `<text class="p1-task" x="${((l + r) / 2).toFixed(2)}" y="${P1.H - P1.BOTTOM + 20}" text-anchor="middle">${esc(o.task)}</text>${line(o.original, "p1-orig")}${line(o.solve_line, "p1-line")}`;
  }).join("");
  const dots = p1Dots(ch).map((d) => {
    const tip = t("p1.tip", { task: d.task, system: d.condition, score: fmtNum(d.score, 1), original: fmtNum(orig[d.task].original, 1), ratio: fmtNum(d.ratio, 2), verdict: t(d.solved ? "p1.yes" : "p1.no") });
    return `<g class="p1-dot" tabindex="0"><title>${esc(tip)}</title><circle class="p1-hit" cx="${d.x}" cy="${d.y}" r="12"/>${p1Mark(sys[d.condition], d.x, d.y, P1.R)}</g>`;
  }).join("");
  const label = t("p1.title", { n: ch.tasks.length });
  const svgText = `<svg class="p1-svg" viewBox="0 0 ${P1.W} ${P1.H}" role="img" aria-label="${esc(label)}">${grid}${bars}${dots}</svg>`;
  const legend = ch.systems.map((s) => `<span class="p1-key"><svg width="16" height="16" viewBox="-8 -8 16 16" aria-hidden="true">${p1Mark(s, 0, 0, 5)}</svg>${condLabel(s.condition, false)}</span>`).join("")
    + `<span class="p1-key"><svg width="24" height="16" viewBox="0 0 24 16" aria-hidden="true"><line class="p1-orig" x1="1" x2="23" y1="8" y2="8"/></svg>${t("p1.original")}</span>`
    + `<span class="p1-key"><svg width="24" height="16" viewBox="0 0 24 16" aria-hidden="true"><line class="p1-line" x1="1" x2="23" y1="8" y2="8"/></svg>${t("p1.solve_line")}</span>`;
  const n = ch.tasks.length;
  const summary = table([t("col.system"), t("p1.scored"), t("p1.solved"), t("p1.mean_score"), t("p1.mean_ratio")],
    ch.systems.map((s) => `<tr><th class="rowhead">${condLabel(s.condition, false)}</th><td>${s.scored}/${n}</td><td>${s.solved}/${s.scored}</td><td>${p1Fixed(s.mean_score)}</td><td>${p1Fixed(s.mean_ratio)}</td></tr>`));
  const cells = table([t("col.task"), t("col.condition"), t("p1.score"), t("p1.original"), t("p1.solve_line"), t("p1.ratio"), t("col.run")],
    ch.cells.map((c) => `<tr><td>${esc(c.task)}</td><th class="rowhead">${condLabel(c.condition, false)}</th><td>${c.score == null ? `<span class="sub">${t("rel.no_stanford")}</span>` : `${fmtNum(c.score, 1)}${c.solved != null ? ` <span class="sub">${t(c.solved ? "p1.yes" : "p1.no")}</span>` : ""}`}</td><td>${fmtNum(orig[c.task].original, 1)}</td><td>${fmtNum(orig[c.task].solve_line, 2)}</td><td>${fmtNum(c.ratio, 2)}</td><td>${runLink(c.run_id)}</td></tr>`));
  const day = String(index.generated_at || "").slice(0, 10);
  return section(`${label}${day ? t("p1.asof", { date: day }) : ""}`,
    `<p class="note">${t("p1.note")}</p><div class="p1"><div class="scroll p1-plot">${svgText}</div><div class="p1-legend">${legend}</div></div>`
    + `<h3>${t("p1.summary")}</h3>${summary}<details class="p1-cells"><summary>${t("p1.cells")}</summary>${cells}</details>`, "phase1-chart");
}

// ---- the spend of a cell (Issue #257) ----------------------------------------------------------------------------
// `figs` is the shape of dashboard/cells.py `sum_spend` (sums over runs, `n` runs that recorded a figure, `missing`) or, for one
// raw `outputs.spend`, `rawFigs`. A figure a run did not record is never 0: it reads "not recorded", with the system's reason.
const SPEND_FMT = { wall_s: fmtDuration, net_wall_s: fmtDuration, model_s: fmtDuration, experiment_s: fmtDuration, turns: (v) => fmtNum(v, 1), requests: (v) => fmtNum(v, 1), input: kTokens,
  output: kTokens, cache_read: kTokens, cache_write: kTokens, tokens: kTokens, list_usd: (v) => `$${Number(v).toFixed(2)}` };
const usdOf = (sp) => { for (const k of ["list_usd", "usd", "equivalent_usd"]) if (typeof sp?.[k] === "number") return sp[k]; return null; };

export function rawFigs(sp) {
  const tk = sp?.tokens || {};
  const kinds = ["input", "output", "cache_read", "cache_write"];
  const f = { runs: 1, wall_s: sp?.wall_s ?? null, net_wall_s: sp?.net_wall_s ?? null, model_s: sp?.model_s ?? null, experiment_s: sp?.experiment_s ?? null, experiment: sp?.experiment || null, turns: sp?.turns ?? null, requests: sp?.requests ?? null,
    list_usd: usdOf(sp), n: {}, missing: {}, why: sp?.unavailable || {} };
  for (const k of kinds) f[k] = tk[k] ?? null;
  f.tokens = kinds.every((k) => f[k] != null) ? kinds.reduce((a, k) => a + f[k], 0) : null;
  return f;
}

// One figure: its value, or "not recorded" with the reason when no run recorded it; "(n/m)" when only some runs did.
export function fig(f, k, brief = false) {
  if (!f || f[k] == null) {
    const why = f?.why?.[k === "tokens" || k === "input" ? "tokens" : k];
    return brief ? `<span class="missing"${why ? ` title="${esc(why)}"` : ""}>${t("not_recorded")}</span>` : missing(why);   // a table cell keeps the reason in its tooltip
  }
  const part = f.missing?.[k] ? ` <span class="sub" title="${t("sp.partial_tip")}">${t("sp.partial", { n: (f.runs || 0) - f.missing[k], m: f.runs })}</span>` : "";
  return `${SPEND_FMT[k](f[k])}${part}`;
}

// Experiment time of a run or of a sum of runs: a lower bound is marked "≥" with what is missing, and the parts the parser gave.
const expLower = (f) => !!(f?.experiment?.lower_bound || f?.experiment_lower);
function expFig(f) {
  const v = fig(f, "experiment_s");
  if (f?.experiment_s == null) return v;
  const parts = f.experiment?.parts ? Object.entries(f.experiment.parts).filter(([, x]) => typeof x === "number").map(([k, x]) => `${esc(k)} ${fmtDuration(x)}`).join(" · ") : "";
  const notes = (f.experiment?.notes || []).map((n) => `<div class="sub">${esc(n)}</div>`).join("");
  return `${expLower(f) ? `<span title="${esc(t("sp.exp_lower_tip"))}">≥ </span>` : ""}${v}${parts ? `<div class="sub">${parts}</div>` : ""}${notes}`;
}

// The compact line of a matrix cell: wall clock and cost of the shown run.
export function cellSpend(cell) {
  const f = cell.spend;
  if (!f || !cell.counted || (f.wall_s == null && f.list_usd == null)) return "";
  return `<div class="cx-line cx-spend sub" title="${esc(t("metric.wall_s"))} · ${esc(t("metric.experiment_s"))} · ${esc(t("sp.cost"))}">⏱ ${f.wall_s != null ? fmtDuration(f.wall_s) : "–"}${f.experiment_s != null ? ` · 🧪 ${expLower(f) ? "≥ " : ""}${fmtDuration(f.experiment_s)}` : ""} · ${f.list_usd != null ? SPEND_FMT.list_usd(f.list_usd) : "–"}</div>`;
}

// The end of a row: wall clock, tokens and cost of the shown runs / of every attempt, and the mean per shown run.
export function rowSpend(row) {
  const c = row.spend_counted, a = row.spend_all;
  if (!c && !a?.runs) return "";
  const pair = (k) => `${c?.[k] != null ? SPEND_FMT[k](c[k]) : "–"} / ${a?.[k] != null ? SPEND_FMT[k](a[k]) : "–"}`;
  const m = row.spend_mean || {};
  const gap = ["wall_s", "tokens", "list_usd"].some((k) => c?.missing?.[k] || a?.missing?.[k]);
  return `<div class="cx-spendsum" title="${esc(t("sp.sum_tip"))}"><div class="sub">${t("sp.sum_head")}</div>`
    + `<div>⏱ ${pair("wall_s")}</div><div>${t("sp.tokens_short")} ${pair("tokens")}</div><div>${t("sp.cost")} ${pair("list_usd")}</div>`
    + `<div class="sub">${t("sp.mean", { t: m.wall_s != null ? fmtDuration(m.wall_s) : "–", c: m.list_usd != null ? SPEND_FMT.list_usd(m.list_usd) : "–" })}</div>`
    + `${gap ? `<div class="sub">${t("sp.gap")}</div>` : ""}</div>`;
}

// The full spend of the shown run (or of all attempts) as rows of the cell page.
function spendRows(f, label) {
  return [
    [t("metric.wall_s"), fig(f, "wall_s")], [t("metric.net_wall_s"), fig(f, "net_wall_s")], [t("metric.model_s"), fig(f, "model_s")],
    [`${t("metric.experiment_s")} <span class="sub">${t("sp.exp_hint")}</span>`, `${expFig(f)}`],
    [t("metric.tokens"), f?.tokens != null || f?.input != null || f?.output != null
      ? `${fig(f, "tokens")}<div class="sub">${["input", "output", "cache_read", "cache_write"].map((k) => `${t(`sp.tok.${k}`)} ${f[k] != null ? kTokens(f[k]) : "–"}`).join(" · ")}</div>` : fig(f, "tokens")],
    [t("metric.turns"), fig(f, "turns")], [t("metric.requests"), fig(f, "requests")],
    [t("sp.cost_list"), fig(f, "list_usd")],
  ].map(([k, v]) => [label ? `${k} <span class="sub">${label}</span>` : k, v]);
}

// ---- performance and cost side by side (Issue #259) ---------------------------------------------------------------------------
// dashboard/performance.py: per batch and condition, the external reviewer's score and the cost of the runs the cells show.

const SC = { W: 520, H: 300, LEFT: 56, RIGHT: 16, TOP: 14, BOTTOM: 40 };

// One scatter: x is a cost (log scale: the costs of the systems differ by orders of magnitude), y the mean Stanford score.
export function perfScatter(rows, xKey, xFmt, xTitle, ticks = [1, 10, 100, 1000]) {
  const pts = rows.filter((r) => r.mean_score != null && r.mean?.[xKey] != null && r.mean[xKey] > 0);
  if (!pts.length) return `<p class="sub">${t("perf.scatter_empty")}</p>`;
  const xs = pts.map((r) => r.mean[xKey]), ys = pts.map((r) => r.mean_score);
  const lo = Math.log10(Math.min(...xs)), hi = Math.log10(Math.max(...xs));
  const x0 = Math.floor(lo * 2) / 2 - 0.1, x1 = Math.max(Math.ceil(hi * 2) / 2 + 0.1, x0 + 0.5);
  const y0 = Math.max(1, Math.floor(Math.min(...ys) - 0.5)), y1 = Math.min(10, Math.ceil(Math.max(...ys) + 0.5));
  const X = (v) => SC.LEFT + ((Math.log10(v) - x0) / (x1 - x0)) * (SC.W - SC.LEFT - SC.RIGHT);
  const Y = (v) => SC.TOP + ((y1 - v) / (y1 - y0)) * (SC.H - SC.TOP - SC.BOTTOM);
  const yTicks = Array.from({ length: y1 - y0 + 1 }, (_, i) => y0 + i);
  const xTicks = ticks.filter((v) => Math.log10(v) >= x0 && Math.log10(v) <= x1);
  const grid = yTicks.map((v) => `<line class="p1-grid" x1="${SC.LEFT}" x2="${SC.W - SC.RIGHT}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/><text class="p1-tick" x="${SC.LEFT - 8}" y="${(Y(v) + 4).toFixed(1)}" text-anchor="end">${v}</text>`).join("")
    + xTicks.map((v) => `<line class="p1-grid" y1="${SC.TOP}" y2="${SC.H - SC.BOTTOM}" x1="${X(v).toFixed(1)}" x2="${X(v).toFixed(1)}"/><text class="p1-tick" x="${X(v).toFixed(1)}" y="${SC.H - SC.BOTTOM + 16}" text-anchor="middle">${esc(xFmt(v))}</text>`).join("");
  const dots = pts.map((r) => {
    const cx = Number(X(r.mean[xKey]).toFixed(1)), cy = Number(Y(r.mean_score).toFixed(1));
    const tip = t("perf.tip", { system: r.condition, score: fmtNum(r.mean_score, 2), cost: xFmt(r.mean[xKey]) });
    return `<g class="p1-dot" tabindex="0"><title>${esc(tip)}</title><circle class="p1-hit" cx="${cx}" cy="${cy}" r="12"/>${p1Mark(r, cx, cy, P1.R)}</g>`;
  }).join("");
  const label = `${t("perf.scatter_y")} × ${xTitle}`;
  const legend = pts.map((r) => `<span class="p1-key"><svg width="16" height="16" viewBox="-8 -8 16 16" aria-hidden="true">${p1Mark(r, 0, 0, 5)}</svg>${esc(r.condition)}</span>`).join("");
  return `<figure class="perf-scatter"><svg class="p1-svg" viewBox="0 0 ${SC.W} ${SC.H}" role="img" aria-label="${esc(label)}">${grid}${dots}`
    + `<text class="p1-tick" x="${(SC.LEFT + SC.W - SC.RIGHT) / 2}" y="${SC.H - 6}" text-anchor="middle">${esc(xTitle)}</text>`
    + `<text class="p1-tick" transform="translate(12 ${(SC.TOP + SC.H - SC.BOTTOM) / 2}) rotate(-90)" text-anchor="middle">${esc(t("perf.scatter_y"))}</text></svg>`
    + `<figcaption class="sub">${esc(label)}</figcaption><div class="p1-legend">${legend}</div></figure>`;
}

// A mean cost with the number of runs it is over when some run did not record it.
function perfMean(r, k, fmt, lower = false) {
  const v = r.mean?.[k];
  if (!r.counted) return "–";       // no cell of the condition has a counted run
  if (v == null) return `<span class="missing">${t("not_recorded")}</span>`;
  const part = r.n[k] < r.counted ? ` <span class="sub" title="${t("sp.partial_tip")}">${t("sp.partial", { n: r.n[k], m: r.counted })}</span>` : "";
  return `${lower && r.experiment_lower ? `<span title="${esc(t("sp.exp_lower_tip"))}">≥ </span>` : ""}${fmt(v)}${part}`;
}

export function renderPerformance(index) {
  const batches = index.performance || [];
  const usd = (v) => `$${Number(v).toFixed(v < 10 ? 2 : 1)}`;
  const body = batches.map((b) => {
    const rows = b.rows.map((r) => `<tr><th class="rowhead">${condLabel(r.condition, false)}</th>
      <td>${r.scored}/${r.tasks}</td><td>${r.scored ? `${r.solved}/${r.scored}` : "–"}</td><td>${r.mean_score != null ? `<strong>${fmtNum(r.mean_score, 2)}</strong>` : "–"}</td><td>${r.mean_ratio != null ? fmtNum(r.mean_ratio, 2) : "–"}</td>
      <td>${perfMean(r, "wall_s", fmtDuration)}</td><td>${perfMean(r, "net_wall_s", fmtDuration)}</td><td>${perfMean(r, "model_s", fmtDuration)}</td><td>${perfMean(r, "experiment_s", fmtDuration, true)}</td>
      <td>${perfMean(r, "tokens", kTokens)}<div class="sub">${["input", "output", "cache_read"].map((k) => `${t(`sp.tok.${k}`)} ${r.mean?.[k] != null ? kTokens(r.mean[k]) : "–"}`).join(" · ")}</div></td>
      <td>${perfMean(r, "requests", (v) => fmtNum(v, 0))}</td>
      <td>${perfMean(r, "list_usd", usd)}</td><td>${r.usd_per_point != null ? `${usd(r.usd_per_point)} <span class="sub">(${r.usd_per_point_n})</span>` : "–"}</td>
      <td>${r.attempts?.list_usd != null ? `${usd(r.attempts.list_usd)} <span class="sub">${t("perf.runs_n", { n: r.attempts.runs })}</span>` : "–"}</td></tr>`);
    const head = [t("col.condition"), t("perf.scored"), t("perf.solved"), t("perf.mean_score"), t("perf.mean_ratio"),
      t("metric.wall_s"), t("metric.net_wall_s"), t("metric.model_s"), `${t("metric.experiment_s")}<div class="sub">${t("sp.exp_hint")}</div>`, t("metric.tokens"), t("metric.requests"),
      t("sp.cost_list"), `${t("cs.per_point")}<div class="sub">${t("perf.per_point_sub")}</div>`, `${t("perf.attempts_usd")}<div class="sub">${t("perf.attempts_sub")}</div>`];
    return section(esc(b.batch), `<p class="note">${t("perf.note", { n: b.tasks.length })}</p>${table(head, rows)}
      <div class="perf-plots">${perfScatter(b.rows, "list_usd", usd, t("perf.x_usd"))}${perfScatter(b.rows, "wall_s", fmtDuration, t("perf.x_wall"), [600, 3600, 10800, 36000, 108000, 360000])}</div>`);
  }).join("");
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.performance")])}<h2>${t("perf.title")}</h2><p class="note">${t("perf.lead")}</p>${rankingLink()}${body || `<p>${t("perf.none")}</p>`}`;
}

// ---- system ranking by the pairwise judge (Issue #329) ------------------------------------------------------------------------
// dashboard/ranking.py: the record `review pairsort rank-systems` writes; shown as it is, no conclusion drawn.

const CRITERIA = ["title", "figure1", "figures_tables", "experiments", "page_use", "clean_text", "abstract_intro"];
const rkSigned = (v, d = 3) => (v == null ? "–" : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`);
const rkFix = (v, d = 3) => (v == null ? "–" : Number(v).toFixed(d));
const rankingHref = (task) => (task ? `#/ranking/${enc(task)}` : "#/ranking");
const ROLE = { counted: "cx.role.counted", "environment-failure": "cx.role.environment", superseded: "cx.role.superseded", earlier: "cx.role.earlier", later: "cx.role.later" };

export const rankingLink = () => `<p class="note"><a href="${rankingHref()}">${t("rk.link")}</a></p>`;

function rankingAbsent(r) {
  const how = t("rk.absent_how", { path: `<code>${esc(r.path)}</code>`, command: `<code>${esc(r.command)}</code>` });
  const body = r.state === "invalid" ? `<p class="badge failed">${t("rk.invalid", { error: esc(r.error) })}</p><p>${how}</p>`
    : `<p><span class="badge stale">${t("rk.absent")}</span></p><p>${how}</p>`;
  return `${crumbs(["#/", t("nav.overview")], [null, t("rk.title")])}<h2>${t("rk.title")}</h2><p class="note">${t("rk.lead")}</p>${body}`;
}

function rankingConditions(r) {
  const n = r.conditions.length;
  const head = [t("rk.rank"), t("col.condition"), t("rk.strength"), t("rk.mean_rank"), t("rk.interval"),
    ...r.conditions.map((_, i) => t("rk.count_at", { n: i + 1 })), t("rk.papers"), t("rk.missing")];
  const rows = r.conditions.map((c) => {
    const p = (r.papers_by_condition || {})[c.condition] || {};
    return `<tr><td>${c.rank}</td><th class="rowhead">${condLabel(c.condition, false)}</th><td>${rkSigned(c.strength)}</td><td>${rkFix(c.mean_rank, 2)}</td>
      <td>${rkFix(c.rank_ci95[0], 0)}–${rkFix(c.rank_ci95[1], 0)}</td>${c.rank_counts.slice(0, n).map((k) => `<td>${k || "·"}</td>`).join("")}
      <td>${p.papers ?? "–"}</td><td>${p.missing ?? "–"}${p.pair_slots != null ? ` <span class="sub">/ ${p.pair_slots}</span>` : ""}</td></tr>`;
  });
  return `<p class="note">${t("rk.conditions_note", { n: r.method.resamples, tasks: r.counts.tasks, seed: r.method.seed, prior: r.method.prior })}</p>${table(head, rows)}`;
}

function rankingFlips(r) {
  const rows = r.flip_table.map((f) => `<tr><td>${condLabel(f.above_in_main, false)}</td><td>${condLabel(f.below_in_main, false)}</td>
    <td>${rkFix(f.share_resamples_main_order)}</td><td>${rkFix(f.flip_rate)}</td></tr>`);
  return `<p class="note">${term("flip-rate", t("rk.flips_note"))}</p>${table([t("rk.above"), t("rk.below"), t("rk.keep_share"), t("rk.flip")], rows)}`;
}

function rankingSplit(r) {
  const s = r.split_half;
  const cols = ["mean", "min", "p2.5", "median", "p97.5", "max"];
  const rows = ["spearman", "kendall"].map((k) => `<tr><th class="rowhead">${t(`rk.${k}`)}</th>${cols.map((c) => `<td>${rkFix(s[k][c], 4)}</td>`).join("")}<td>${s[k].n}</td></tr>`);
  return `<p class="note">${t("rk.split_note", { a: s.halves[0], b: s.halves[1], n: r.method.resamples, seed: r.method.split_seed })}</p>
    ${table([t("rk.stat"), t("rk.mean"), t("rk.min"), "2.5%", t("rk.median"), "97.5%", t("rk.max"), "n"], rows)}`;
}

function rankingWinners(r) {
  const order = r.conditions.map((c) => c.condition);
  const slots = {};
  for (const p of r.missing) slots[p.task] = (slots[p.task] || 0) + 1;
  const rows = r.tasks.map((task) => {
    const w = r.task_winners[task] || { winner: [], wins: {} };
    return `<tr><th class="rowhead"><a href="${rankingHref(task)}">${esc(task)}</a></th><td>${w.winner.map((c) => condLabel(c, false)).join(", ") || "–"}</td>
      ${order.map((c) => `<td>${fmtNum(w.wins[c] ?? 0, 1)}</td>`).join("")}<td>${slots[task] || 0}</td></tr>`;
  });
  return `<p class="note">${term("task-winner", t("rk.winners_note"))}</p>
    ${table([t("rk.task"), t("rk.winner"), ...order.map((c) => esc(c)), t("rk.missing")], rows)}`;
}

function rankingMissing(r) {
  const rows = r.missing.map((m) => `<tr><td><code>${esc(m.id)}</code></td><td><a href="${rankingHref(m.task)}">${esc(m.task)}</a></td>
    <td>${m.conditions.map((c) => condLabel(c, false)).join(" × ")}</td><td>${esc(m.reason)}${verbatim()}</td></tr>`);
  return table([t("rk.pair"), t("rk.task"), t("col.condition"), t("rk.reason")], rows, t("rk.no_missing"));
}

function rankingCosts(r) {
  const rows = r.costs.batches.map((b) => `<tr><td><code>${esc(b.label)}</code></td><td>${b.pairs}</td><td>${b.attempts}</td><td>$${Number(b.cost_usd).toFixed(2)}</td></tr>`);
  const foot = `<tr><th>${t("rk.total")}</th><td>${r.counts.pairs}</td><td>${r.costs.total_attempts}</td><td>$${Number(r.costs.total_cost_usd).toFixed(2)}</td></tr>`;
  return `<p class="note">${t("rk.costs_note")}</p>${table([t("rk.batch"), t("rk.pairs"), t("rk.attempts"), t("rk.cost")], rows, "", foot)}`;
}

function rankingPapers(r, runs) {
  const known = new Set((runs || []).map((x) => x.run_id));
  const rows = (r.papers || []).map((p) => `<tr><td><a href="${rankingHref(p.task)}">${esc(p.task)}</a></td><td>${condLabel(p.condition, false)}</td>
    <td>${known.has(p.run) ? runLink(p.run) : `<code>${esc(p.run)}</code>`}</td><td>${p.pages ?? "–"}</td>
    <td>${p.cell_role ? `${t(ROLE[p.cell_role] || "cx.role.earlier")} <span class="sub">${esc(p.cell_batch)}</span>${p.cell_rerunning ? ` <span class="tag pending">${t("cx.rerunning")}</span>` : ""}` : `<span class="sub">${t("rk.paper_no_cell")}</span>`}</td></tr>`);
  return `<details><summary>${t("rk.papers_summary", { n: rows.length })}</summary><p class="note">${t("rk.papers_note")}</p>
    ${table([t("rk.task"), t("col.condition"), t("rk.paper_run"), t("rk.pages"), t("rk.paper_cell")], rows)}</details>`;
}

function rankingExtra(index) {
  const list = ((index.conditions || {}).plan?.extra_resources || []).filter((e) => e.batch);
  return list.length ? section(t("rk.s.extra"), `<p class="note">${t("rk.extra_note")}</p><ul>${list.map((e) => `<li><a href="${cellHref(e.batch, e.condition, e.task)}">${esc(e.condition)} × ${esc(e.task)}</a>: ${esc(S.lang === "en" ? e.reason_en : e.reason)}</li>`).join("")}</ul>`) : "";
}

export function renderRanking(index) {
  const r = index.ranking;
  if (!r || r.state !== "present") return rankingAbsent(r || { state: "absent", path: "", command: "" });
  const j = r.judge, c = r.counts, v = c.verdicts || {};
  const info = kv([
    [term("pairwise-judge", t("rk.judge")), `${esc(j.name)} (<code>${esc(j.model)}</code>, ${t("rk.effort")} ${esc(j.effort ?? "–")}) · ${t("rk.max_images", { n: j.max_images })}`],
    [term("judge-freeze", t("rk.freeze")), `<code>${esc(j.freeze_file)}</code> · sha256 <code>${esc(j.freeze_sha256)}</code>${j.frozen_at ? ` · ${t("rk.frozen_at", { time: fmtTime(j.frozen_at) })}` : ""}`],
    ...((j.freezes || []).length > 1 ? [[term("judge-freeze", t("rk.freezes", { n: j.freezes.length })), `<ul>${j.freezes.map((f) => `<li><code>${esc(f.freeze_file)}</code> · ${f.role === "current" ? t("rk.freeze_current") : t("rk.freeze_superseded")} · sha256 <code>${esc(f.freeze_sha256)}</code> · ${t("rk.freeze_runs", { n: f.runs })}${f.role === "superseded" ? ` · ${t("rk.freeze_diff", { files: (f.files || []).map((x) => esc(x.split("/").pop())).join(", ") || "–", constants: (f.constants || []).map(esc).join(", ") || "–", reason: esc(f.reason || "") })}` : ""}</li>`).join("")}</ul>`]] : []),
    [t("rk.inputs"), t("rk.inputs_text", { papers: c.papers, pairs: c.pairs, decided: c.decided_pairs, a: v.A ?? 0, b: v.B ?? 0, e: v.equal ?? 0, tasks: c.tasks })],
    [t("rk.generated"), fmtTime(r.generated_at)],
    [term("bradley-terry", t("rk.model")), t("rk.model_text", { prior: r.method.prior })],
  ]);
  const limits = `<ul>${[1, 2, 3, 4, 5, 6].map((k) => `<li>${t(`rk.limit.${k}`, { equal: v.equal ?? 0, decided: c.decided_pairs })}</li>`).join("")}</ul>`;
  return `${crumbs(["#/", t("nav.overview")], [null, t("rk.title")])}<h2>${t("rk.title")}</h2><p class="note">${t("rk.lead")}</p>${info}
    ${section(t("rk.s.conditions"), rankingConditions(r))}
    ${section(t("rk.s.winners"), rankingWinners(r))}
    ${section(t("rk.s.flips"), rankingFlips(r))}
    ${section(t("rk.s.split"), rankingSplit(r))}
    ${section(t("rk.s.missing", { n: r.missing.length }), rankingMissing(r))}
    ${section(t("rk.s.costs"), rankingCosts(r))}
    ${section(t("rk.s.limits"), `<p class="note">${t("rk.limits_note")}</p>${limits}`)}
    ${rankingExtra(index)}
    ${section(t("rk.s.papers"), rankingPapers(r, index.runs))}`;
}

const sideName = (p, run) => (run === p.a.run ? p.a.condition : p.b.condition);

function pairOrders(p) {
  return ["AB", "BA"].map((k) => {
    const o = p.orders?.[k];
    if (!o) return "";
    const said = o.better_as_shown === "A" ? sideName(p, o.shown_as_A) : o.better_as_shown === "B" ? sideName(p, o.shown_as_B) : t("rk.equal");
    const rows = CRITERIA.map((c) => `<tr><th class="rowhead">${t(`rk.crit.${c}`)}</th><td>${esc(o.reasons?.[c] ?? "–")}</td></tr>`).join("");
    return `<h4>${t("rk.order_head", { order: k, a: esc(sideName(p, o.shown_as_A)), b: esc(sideName(p, o.shown_as_B)) })}</h4>
      <p class="sub">${t("rk.order_said", { said: esc(said), conf: o.confidence ? t(`rk.conf.${o.confidence.replace(" ", "_")}`) : "–" })}${o.pages_seen ? ` · ${t("rk.pages_seen", { a: o.pages_seen.A, b: o.pages_seen.B })}` : ""}</p>
      <div class="scroll"><table class="kv"><tbody>${rows}</tbody></table></div>`;
  }).join("");
}

function pairRow(p) {
  const verdict = p.verdict == null ? `<span class="badge failed">${t("rk.no_verdict")}</span><div class="sub">${esc(p.reason_missing ?? "")}${verbatim()}</div>`
    : p.winner === "equal" ? `<span class="badge">${t("rk.equal")}</span>` : `<strong>${esc(p.winner)}</strong>`;
  const body = p.verdict == null ? "" : `<tr><td></td><td colspan="5"><details><summary>${t("rk.reasons")}</summary><p class="note">${t("rk.reasons_note")}</p>${pairOrders(p)}</details></td></tr>`;
  return `<tr id="pair-${esc(p.id)}"><td><code>${esc(p.id)}</code></td><td>${condLabel(p.a.condition, false)}<div class="sub">${p.a.pages ?? "–"} ${t("rk.pages")}</div></td>
    <td>${condLabel(p.b.condition, false)}<div class="sub">${p.b.pages ?? "–"} ${t("rk.pages")}</div></td>
    <td>${verdict}</td><td>${p.confidence ? t(`rk.conf.${p.confidence.replace(" ", "_")}`) : "–"}</td>
    <td>${p.agree == null ? "–" : p.agree ? t("rk.agree") : t("rk.disagree")}</td></tr>${body}`;
}

export function renderRankingTask(page) {
  const crumb = (last) => crumbs(["#/", t("nav.overview")], ["#/ranking", t("rk.title")], [null, last]);
  if (!page || !page.pairs) return `${crumb(esc(page?.task ?? ""))}<p>${t("rk.task_none")}</p>`;
  const w = page.winner || { winner: [], wins: {} };
  const wins = Object.entries(w.wins || {}).map(([c, n]) => `${condLabel(c, false)} <strong>${fmtNum(n, 1)}</strong>`).join(" · ");
  const rows = page.pairs.map((p) => pairRow(p));
  return `${crumb(esc(page.task))}<h2>${t("rk.task_title", { task: esc(page.task) })}</h2><p class="note">${t("rk.task_lead")}</p>
    ${kv([[term("task-winner", t("rk.winner")), w.winner.map((c) => condLabel(c, false)).join(", ") || "–"], [t("rk.wins"), wins || "–"],
      [term("pairwise-judge", t("rk.judge")), `${esc(page.judge.name)} (<code>${esc(page.judge.model)}</code>)`]])}
    ${table([t("rk.pair"), t("rk.a"), t("rk.b"), t("rk.verdict"), t("rk.confidence"), t("rk.orders")], rows)}`;
}

// ---- phase 1 analysis (Issue #262) ---------------------------------------------------------------------------------------
// dashboard/analysis.py: per batch, each ResearchWorld condition against its single-agent baseline, and where ResearchWorld's
// cost goes. dashboard/findings.py: the written conclusions, with the metrics they rest on.

const AN = { W: 760, H: 280, LEFT: 44, RIGHT: 12, TOP: 12, BOTTOM: 34 };
const anPct = (v) => (v == null ? "–" : `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`);
const anUsd = (v) => (v == null ? "–" : `$${Number(v).toFixed(v < 10 ? 2 : 1)}`);
const signed = (v, d = 2) => (v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(d)}`);

// Paired bars: per task the subject's and the baseline's score, side by side (tasks without both scores are not drawn).
export function pairBars(pair) {
  const rows = pair.paired || [];
  if (!rows.length) return `<p class="sub">${t("an.chart_empty")}</p>`;
  const w = (AN.W - AN.LEFT - AN.RIGHT) / rows.length, bw = Math.min(26, w * 0.34);
  const Y = (v) => AN.TOP + ((10 - v) / 10) * (AN.H - AN.TOP - AN.BOTTOM);
  const grid = [0, 2, 4, 6, 8, 10].map((v) => `<line class="p1-grid" x1="${AN.LEFT}" x2="${AN.W - AN.RIGHT}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/><text class="p1-tick" x="${AN.LEFT - 8}" y="${(Y(v) + 4).toFixed(1)}" text-anchor="end">${v}</text>`).join("");
  const bar = (x, v, style, who, task) => `<g><title>${esc(t("an.bar_tip", { task, system: who, score: v.toFixed(1) }))}</title><rect x="${x.toFixed(1)}" y="${Y(v).toFixed(1)}" width="${bw.toFixed(1)}" height="${(Y(0) - Y(v)).toFixed(1)}" style="fill:var(--series-${style.slot})"/><text class="p1-tick" x="${(x + bw / 2).toFixed(1)}" y="${(Y(v) - 3).toFixed(1)}" text-anchor="middle">${v.toFixed(1)}</text></g>`;
  const bars = rows.map((r, i) => {
    const cx = AN.LEFT + w * (i + 0.5);
    return bar(cx - bw - 1, r.subject, pair.subject_style, pair.subject, r.task) + bar(cx + 1, r.baseline, pair.baseline_style, pair.baseline, r.task)
      + `<text class="p1-task" x="${cx.toFixed(1)}" y="${AN.H - 12}" text-anchor="middle">${esc(r.task)}</text>`;
  }).join("");
  const key = (c, st) => `<span class="p1-key"><svg width="16" height="16" viewBox="-8 -8 16 16" aria-hidden="true">${p1Mark({ ...st, marker: "square" }, 0, 0, 5)}</svg>${esc(c)}</span>`;
  const label = t("an.bars_label", { subject: pair.subject, baseline: pair.baseline });
  return `<figure class="an-fig"><svg class="p1-svg" viewBox="0 0 ${AN.W} ${AN.H}" role="img" aria-label="${esc(label)}">${grid}${bars}</svg>`
    + `<figcaption class="sub">${esc(label)}</figcaption><div class="p1-legend">${key(pair.subject, pair.subject_style)}${key(pair.baseline, pair.baseline_style)}</div></figure>`;
}

// One horizontal bar split into parts whose sizes are shares of a whole (roles, turn classes). The colours step from the biggest
// part to the smallest in one hue, so the order carries the meaning and no part needs a colour of its own; each part is named in
// the table beside it and in its tooltip.
export function stackBar(parts, label) {
  const have = parts.filter((p) => p.share != null && p.share > 0);
  if (!have.length) return `<p class="sub">${t("an.chart_empty")}</p>`;
  const W = 760, H = 40, total = have.reduce((a, p) => a + p.share, 0);
  let x = 0;
  const segs = have.map((p, i) => {
    const wd = (p.share / total) * W, op = (1 - (i / Math.max(1, have.length)) * 0.75).toFixed(2);
    const seg = `<g><title>${esc(`${p.label}: ${anPct(p.share)}`)}</title><rect x="${x.toFixed(1)}" y="0" width="${wd.toFixed(1)}" height="${H}" style="fill:var(--series-s1);opacity:${op};stroke:var(--panel);stroke-width:1"/>`
      + (wd > 70 ? `<text x="${(x + wd / 2).toFixed(1)}" y="${H / 2 + 4}" text-anchor="middle" class="an-seg" style="${i < have.length / 2 ? "fill:#fff" : ""}">${esc(p.short || p.label)} ${anPct(p.share)}</text>` : "") + "</g>";
    x += wd;
    return seg;
  }).join("");
  return `<figure class="an-fig"><svg class="an-stack" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${segs}</svg><figcaption class="sub">${esc(label)}</figcaption></figure>`;
}

function mdInline(text) {
  return String(text).split("`").map((part, i) => (i % 2 ? `<code>${esc(part)}</code>` : esc(part).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>"))).join("");
}

export function renderReportBody(text) {
  const cells = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((c) => mdInline(c.trim()));
  const out = [];
  let list = [], para = [], rows = [];
  const flush = () => {
    if (para.length) out.push(`<p>${mdInline(para.join(" "))}</p>`);
    if (list.length) out.push(`<${list.tag}>${list.map((x) => `<li>${mdInline(x)}</li>`).join("")}</${list.tag}>`);
    if (rows.length) {
      const body = rows.slice(2).map((r) => `<tr>${cells(r).map((c) => `<td>${c}</td>`).join("")}</tr>`);
      out.push(table(cells(rows[0]), body));
    }
    para = []; list = []; rows = [];
  };
  for (const raw of String(text || "").split("\n")) {
    const line = raw.trimEnd();
    const head = line.match(/^(#{1,4})\s+(.*)$/);
    const item = line.match(/^(?:-|(\d+)\.)\s+(.*)$/);
    if (!line.trim()) { flush(); continue; }
    if (head) { flush(); out.push(`<h4>${mdInline(head[2])}</h4>`); continue; }
    if (line.startsWith("|")) { if (para.length || list.length) flush(); rows.push(line); continue; }
    if (item) {
      if (para.length || rows.length) flush();
      list.tag = list.tag || (item[1] ? "ol" : "ul");
      list.push(item[2]);
      continue;
    }
    if (list.length || rows.length) flush();
    para.push(line.trim());
  }
  flush();
  return out.join("");
}

function reportCard(r) {
  const body = L({ zh: r.body, en: r.body_en });
  return `<article class="card finding" id="report-${esc(r.id)}"><h3>${esc(L({ zh: r.title, en: r.title_en }))}</h3>
    <p>${esc(L({ zh: r.text, en: r.text_en }))}</p>
    <p class="sub">${t("an.finding_by", { by: esc(r.by), date: esc(r.date) })} · ${link(r.url, t("an.report_open"))} <span class="note">${t("an.report_access")}</span></p>
    <details open><summary>${t("an.report_body")}</summary>${body ? renderReportBody(body) : `<p class="sub">${t("an.report_withheld")}</p>`}</details></article>`;
}

function findingCard(f) {
  const basis = f.basis.map((b) => {
    const cur = b.current == null ? "–" : fmtNum(b.current, 3);
    const flag = !b.known ? ` <span class="badge failed">${t("an.unknown_metric")}</span>` : b.changed ? ` <span class="badge running">${t("an.changed")}</span>` : "";
    return `<tr><td><code>${esc(b.metric.split(":").slice(1).join(":"))}</code></td><td>${fmtNum(b.value, 3)}</td><td>${cur}${flag}</td></tr>`;
  });
  return `<article class="card finding${f.review ? " review" : ""}" id="finding-${esc(f.id)}"><h3>${esc(L({ zh: f.title, en: f.title_en }))}</h3>
    <p>${esc(L({ zh: f.text, en: f.text_en }))}</p>
    <p class="sub">${t("an.finding_by", { by: esc(f.by), date: esc(f.date) })}${f.review ? ` · <span class="badge running" title="${esc(t("an.review_tip"))}">${t("an.review")}</span>` : ""}</p>
    <details><summary>${t("an.basis")} (${f.basis.length})</summary>${table([t("an.metric"), t("an.recorded"), t("an.current")], basis)}</details></article>`;
}


const GROUPS = ["familiarize", "work", "collaborate", "wait", "overhead", "reply", "other"];

// What the requests were for (Issue #262): per purpose group the ResearchWorld condition's requests per run and shares, beside the
// baseline's; the fine categories; and, for ResearchWorld, sessions, the opening of turns, the split of the work and the wall clock.
function profileSection(pair, profile) {
  const sub = profile?.[pair.subject], base = profile?.[pair.baseline];
  if (!sub) return "";
  const n = (v, d = 1) => (v == null ? "–" : fmtNum(v, d));
  const gRows = GROUPS.filter((g) => (sub.groups[g]?.requests || 0) + (base?.groups[g]?.requests || 0) > 0).map((g) => {
    const a = sub.groups[g], b = base?.groups[g];
    return `<tr><th class="rowhead">${t(`an.grp.${g}`)}</th><td>${n(a.requests_per_run)}</td><td>${anPct(a.request_share)}</td><td>${anPct(a.seconds_share)}</td><td>${anPct(a.usd_share)}</td>`
      + `<td>${b ? n(b.requests_per_run) : "–"}</td><td>${b ? anPct(b.request_share) : "–"}</td></tr>`;
  });
  const head = [t("an.grp"), `${esc(pair.subject)} ${t("an.req_run_c")}`, t("an.share_req"), t("an.share_sec"), t("an.share_usd"), `${esc(pair.baseline)} ${t("an.req_run_c")}`, t("an.share_req")];
  const bar = (p, cond) => stackBar(GROUPS.map((g) => ({ label: t(`an.grp.${g}`), share: p.groups[g]?.request_share })), t("an.prof_bar_s", { cond }));
  const cats = [...new Set([...Object.keys(sub.categories), ...Object.keys(base?.categories || {})])]
    .sort((x, y) => (sub.categories[y]?.requests_per_run || 0) - (sub.categories[x]?.requests_per_run || 0));
  const cRows = cats.map((c) => `<tr><th class="rowhead">${t(`an.cat.${c}`)}</th><td>${n(sub.categories[c]?.requests_per_run ?? 0)}</td><td>${anPct(sub.categories[c]?.request_share ?? 0)}</td><td>${n(base?.categories[c]?.requests_per_run ?? 0)}</td><td>${anPct(base?.categories[c]?.request_share ?? 0)}</td></tr>`);
  const kv = (rows) => `<table class="an-sum"><tbody>${rows.map(([k, v]) => `<tr><th class="rowhead">${k}</th><td>${v}</td></tr>`).join("")}</tbody></table>`;
  const ss = sub.sessions, pf = sub.prefix, w = sub.work, tl = sub.timeline;
  const tlParts = [["executing", "an.time_exec"], ["compute_only", "an.time_comp"], ["queue_wait", "an.time_queue"], ["idle", "an.time_idle"]];
  const toolSec = sub.tool_seconds;
  return section(t("an.prof_title", { subject: esc(pair.subject) }), `
    <p class="note">${t("an.prof_note", { runs: sub.runs })}</p>
    <div class="an-grid">${bar(sub, pair.subject)}${base ? bar(base, pair.baseline) : ""}</div>
    ${table(head, gRows)}
    <details><summary>${t("an.cat_title")}</summary>${table([t("an.grp"), `${esc(pair.subject)} ${t("an.req_run_c")}`, t("an.share_req"), `${esc(pair.baseline)} ${t("an.req_run_c")}`, t("an.share_req")], cRows)}</details>
    <h3>${t("an.sess_title")}</h3><p class="note">${t("an.sess_note")}</p>
    ${kv([[t("an.sess_turns"), ss.with_requests], [t("an.sess_reused"), `${ss.reused} (${anPct(ss.reused_share)})`],
      [t("an.sess_ctx_reused"), ss.reused_conversation_kb == null ? "–" : `${n(ss.reused_conversation_kb)} KB`], [t("an.sess_ctx_fresh"), ss.fresh_conversation_kb == null ? "–" : `${n(ss.fresh_conversation_kb)} KB`],
      [t("an.pref_turns"), `${pf.turns} (${anPct(pf.turn_share)})`], [t("an.pref_reqs"), anPct(pf.request_share)], [t("an.pref_per"), n(pf.per_turn, 2)]])}
    <h3>${t("an.work_title")}</h3><p class="note">${t("an.work_note")}</p>
    ${kv([[t("an.work_pr"), n(w.pull_requests_per_run)], [t("an.work_issue"), n(w.issue_events_per_pr, 2)], [t("an.work_rel"), n(w.releases_per_run)], [t("an.work_rev"), n(w.reviews_per_pr, 2)],
      [t("an.work_rej_pr"), anPct(w.pr_rejected_share)], [t("an.work_rej_rev"), anPct(w.reviews_rejected_share)], [t("an.work_hand"), n(w.paper_figtab_handoffs_per_run)]])}
    <h3>${t("an.time_title")}</h3><p class="note">${t("an.time_note")}</p>
    ${stackBar(tlParts.map(([k, key]) => ({ label: t(key), share: tl[`${k}_share`] })), t("an.time_bar"))}
    ${kv([...tlParts.map(([k, key]) => [t(key), `${anPct(tl[`${k}_share`])} <span class="sub">(${fmtDuration(tl[`${k}_s`] / sub.runs)} ${t("an.per_run")})</span>`]),
      [t("an.time_qpt"), fmtDuration(tl.queue_s_per_turn)], [t("an.time_tools"), `${fmtDuration(toolSec.total / sub.runs)} ${t("an.per_run")}`]])}`, `profile-${esc(pair.subject)}`);
}

function pairSection(p) {
  const head = [t("an.measure"), condLabel(p.subject, false), condLabel(p.baseline, false)];
  const num = (v, d = 2) => (v == null ? "–" : fmtNum(v, d));
  const scoreRows = [
    [t("an.paired_n"), `${p.n}/${p.tasks}`, ""],
    [t("an.mean_score"), num(p.subject_mean), num(p.baseline_mean)],
    [t("an.score_sd"), num(p.subject_sd), num(p.baseline_sd)],
    [t("an.score_min"), num(p.subject_min, 1), num(p.baseline_min, 1)],
  ].map(([k, a, b]) => `<tr><th class="rowhead">${k}</th><td>${a}</td><td>${b}</td></tr>`);
  const summary = `<table class="an-sum"><tbody>
    <tr><th class="rowhead">${t("an.wlt", { subject: esc(p.subject) })}</th><td>${p.wins} / ${p.ties} / ${p.losses}</td></tr>
    <tr><th class="rowhead">${t("an.mean_diff")}</th><td><strong>${signed(p.mean_diff)}</strong></td></tr>
    <tr><th class="rowhead">${t("an.sd_diff")}</th><td>${num(p.sd_diff)}</td></tr>
    <tr><th class="rowhead">${t("an.corr", { subject: esc(p.subject) })}</th><td>${p.corr_usd_score == null ? "–" : signed(p.corr_usd_score, 3)} <span class="sub">(${p.corr_n})</span></td></tr></tbody></table>`;
  const pairedRows = p.paired.map((r) => `<tr><th class="rowhead"><a href="#/compare/${enc(r.task)}">${esc(r.task)}</a></th><td>${r.subject.toFixed(1)}</td><td>${r.baseline.toFixed(1)}</td><td class="${r.diff > 0 ? "an-up" : r.diff < 0 ? "an-down" : ""}">${signed(r.diff, 1)}</td></tr>`);
  const fmt = { list_usd: anUsd, wall_s: fmtDuration, net_wall_s: fmtDuration, model_s: fmtDuration, experiment_s: fmtDuration, requests: (v) => fmtNum(v, 0), turns: (v) => fmtNum(v, 0), tokens: kTokens, input: kTokens, output: kTokens, cache_read: kTokens, cache_write: kTokens };
  const names = { list_usd: t("sp.cost_list"), wall_s: t("metric.wall_s"), net_wall_s: t("metric.net_wall_s"), model_s: t("metric.model_s"), experiment_s: t("metric.experiment_s"), requests: t("metric.requests"), turns: t("metric.turns"), tokens: t("metric.tokens"), input: t("sp.tok.input"), output: t("sp.tok.output"), cache_read: t("sp.tok.cache_read"), cache_write: t("sp.tok.cache_write") };
  const costRows = Object.keys(fmt).filter((k) => p.cost[k]).map((k) => {
    const c = p.cost[k];
    const cell = (v, n) => (v == null ? `<span class="missing">${t("not_recorded")}</span>` : fmt[k](v) + (n != null && n < p.tasks ? ` <span class="sub">${t("sp.partial", { n, m: p.tasks })}</span>` : ""));
    return `<tr><th class="rowhead">${names[k]}</th><td>${cell(c.subject, c.n_subject)}</td><td>${cell(c.baseline, c.n_baseline)}</td><td>${c.ratio == null ? "–" : `${c.ratio.toFixed(2)}×`}</td></tr>`;
  });
  return section(t("an.pair_title", { subject: esc(p.subject), baseline: esc(p.baseline) }), `
    <h3>${t("an.scores")}</h3>
    <div class="an-grid"><div>${table(head, scoreRows)}${summary}</div><div>${pairBars(p)}</div></div>
    ${table([t("col.task"), esc(p.subject), esc(p.baseline), t("an.diff")], pairedRows, t("an.chart_empty"))}
    <h3>${t("an.cost")}</h3><p class="note">${t("an.cost_note")}</p>
    ${table([t("an.measure"), esc(p.subject), esc(p.baseline), t("an.ratio")], costRows)}`, `pair-${esc(p.subject)}`);
}

function roleSection(batch, cond, prof) {
  if (!prof) return "";
  const roleRows = Object.entries(prof.roles).map(([role, e]) => `<tr><th class="rowhead">${esc(role)}</th><td>${anUsd(e.list_usd / prof.runs)}</td><td>${anPct(e.usd_share)}</td><td>${fmtNum(e.requests / prof.runs, 0)}</td><td>${anPct(e.request_share)}</td><td>${fmtDuration(e.request_seconds / prof.runs)}</td><td>${anPct(e.seconds_share)}</td><td>${fmtNum(e.turns / prof.runs, 1)}</td></tr>`);
  const classRows = Object.entries(prof.classes).map(([c, e]) => `<tr><th class="rowhead">${t(`an.class.${c}`)}<div class="sub">${t(`an.class.${c}.means`)}</div></th><td>${e.turns}</td><td>${anPct(e.turn_share)}</td><td>${e.requests}</td><td>${anPct(e.request_share)}</td><td>${e.requests_per_turn ?? "–"}</td></tr>`);
  const effects = Object.entries(prof.effects).map(([k, v]) => `<tr><th class="rowhead">${esc(k)}</th><td>${fmtNum(v, 1)}</td><td>${prof.effects_total[k]}</td></tr>`);
  const roleParts = Object.entries(prof.roles).map(([role, e]) => ({ label: role, short: role.replace(/-repo$/, ""), share: e.usd_share }));
  const classParts = (key) => Object.entries(prof.classes).map(([c, e]) => ({ label: t(`an.class.${c}`), share: e[key] }));
  return section(t("an.roles_title", { cond: esc(cond) }), `<p class="note">${t("an.roles_note", { runs: prof.runs, cache: anPct(prof.total.cache_read_share) })}</p>
    ${stackBar(roleParts, t("an.roles_bar"))}
    ${table([t("an.role"), t("an.usd_run"), t("an.usd_share"), t("an.req_run"), t("an.req_share"), t("an.sec_run"), t("an.sec_share"), t("an.turns_run")], roleRows)}
    <h3>${t("an.classes_title")}</h3><p class="note">${t("an.classes_note")}</p>
    <div class="an-grid">${stackBar(classParts("turn_share"), t("an.classes_turns"))}${stackBar(classParts("request_share"), t("an.classes_reqs"))}</div>
    ${table([t("an.class"), t("an.turns"), t("an.turn_share"), t("an.requests"), t("an.req_share"), t("an.req_turn")], classRows)}
    <h3>${t("an.effects_title")}</h3><p class="note">${t("an.effects_note")}</p>
    ${table([t("an.effect"), t("an.per_run"), t("an.total")], effects)}`, `roles-${esc(cond)}`);
}

export function renderAnalysis(index, batch) {
  const list = index.analysis || [];
  const crumb = (last) => crumbs(["#/", t("nav.overview")], ...(last ? [["#/analysis", t("nav.analysis")], [null, esc(last)]] : [[null, t("nav.analysis")]]));
  const b = list.find((x) => x.batch === batch) || (!batch ? list[0] : null);
  if (!b) return `${crumb(batch)}<h2>${t("an.title")}</h2><p>${t("an.none")}</p>`;
  const tabs = list.length > 1 ? `<p class="chips">${list.map((x) => (x.batch === b.batch ? `<strong>${esc(x.batch)}</strong>` : `<a href="#/analysis/${enc(x.batch)}">${esc(x.batch)}</a>`)).join(" · ")}</p>` : "";
  const findings = (index.findings || []).filter((f) => f.batch === b.batch && f.kind !== "improvement");
  const improvements = (index.findings || []).filter((f) => f.batch === b.batch && f.kind === "improvement");
  const reports = (index.reports || []).filter((r) => r.batch === b.batch);
  const perf = (index.performance || []).find((x) => x.batch === b.batch);
  const usd = (v) => `$${Number(v).toFixed(v < 10 ? 2 : 1)}`;
  const body = [
    reports.length ? section(t("an.reports"), reports.map(reportCard).join(""), "reports") : "",
    section(t("an.findings"), `<p class="note">${t("an.findings_note")}</p>${findings.map(findingCard).join("") || `<p class="sub">${t("an.no_findings")}</p>`}`, "findings"),
    ...b.pairs.flatMap((p) => [pairSection(p), profileSection(p, b.profile)]),
    improvements.length ? section(t("an.improve"), `<p class="note">${t("an.improve_note")}</p>${improvements.map(findingCard).join("")}`, "improvements") : "",
    perf ? section(t("an.scatter"), `<div class="perf-plots">${perfScatter(perf.rows, "list_usd", usd, t("perf.x_usd"))}${perfScatter(perf.rows, "wall_s", fmtDuration, t("perf.x_wall"), [600, 3600, 10800, 36000, 108000, 360000])}</div>`) : "",
    ...Object.entries(b.roles).map(([cond, prof]) => roleSection(b.batch, cond, prof)),
  ].join("");
  return `${crumb(b.batch)}<h2>${t("an.title")} · ${esc(b.batch)}</h2><p class="note">${t("an.lead", { n: b.tasks.length })}</p>${tabs}${body}`;
}

// ---- cell matrix, cell page, known defects (Issue #237) ---------------------------------------------------------

// The states of a cell, in the order of the legend (dashboard/cells.py has the rule that picks one). Each has a colour, an
// icon and words: the state never depends on the colour alone.
export const CELL_STATES = ["scored", "awaiting-review", "not-reviewed", "no-paper", "running", "paused", "system-failure",
  "failed-unjudged", "environment-failure", "not-dispatched", "not-started"];
const CELL_ICON = { scored: "✓", "awaiting-review": "⌛", "not-reviewed": "⊘", "no-paper": "∅", running: "▶", paused: "‖", "system-failure": "✗",
  "failed-unjudged": "?", "environment-failure": "⚠", "not-dispatched": "–", "not-started": "·" };
const cellHref = (batch, condition, task) => `#/cell/${enc(batch)}/${enc(condition)}/${enc(task)}`;
const defectHref = (system, id) => `#/defect/${enc(system)}/${enc(id)}`;
const cellState = (state, tip = "") => `<span class="cx-state" title="${esc(tip)}"><span class="ic" aria-hidden="true">${CELL_ICON[state] || "·"}</span> ${t(`cx.state.${state}`)}</span>`;
const firstClause = (text, max = 64) => {
  const s = String(text || "").split(/[；。;]|\. /)[0].trim();
  return s.length > max ? `${s.slice(0, max).trimEnd()}…` : s;
};
const verdictText = (v) => (v ? L({ zh: v.reason, en: v.reason_en || v.reason }) : "");
const verdictWho = (v) => t("cx.verdict_who", { by: esc(v.by), date: esc(v.date), source: esc(v.source) });

// What a cell shows under its state: the score with its ratio and the solve line, the time a running cell has taken,
// the stop reason, or a clause of the verdict. The whole text is on the cell's page.
export function cellDetail(cell) {
  const s = cell.score;
  const bits = [];
  if (cell.state === "scored" && s) {
    bits.push(`<strong>${fmtNum(s.value, 1)}</strong>${s.ratio != null ? ` · ${fmtNum(s.ratio, 2)}×` : ""}${s.solved != null ? ` · ${t(s.solved ? "cx.solved" : "cx.not_solved")}` : ""}`);
  } else if (cell.state === "running") {
    bits.push(`${t("cx.elapsed", { d: fmtDuration(cell.elapsed_s) })}${cell.turns != null ? ` · ${t("cx.turns", { n: esc(cell.turns) })}` : ""}`);
  } else if (cell.state === "awaiting-review" && cell.pending_parse) {
    bits.push(t("cx.pending_parse"));
  } else if (cell.state === "paused" && cell.stop_reason) {
    bits.push(esc(firstClause(cell.stop_reason, 56)));
  } else if (["system-failure", "environment-failure", "not-dispatched", "not-reviewed"].includes(cell.state) && cell.verdict) {
    bits.push(esc(firstClause(verdictText(cell.verdict))));
  } else if (cell.state === "failed-unjudged" && cell.status) {
    bits.push(esc(tname(cell.status)));
  }
  return bits.map((b) => `<div class="cx-line">${b}</div>`).join("");
}

export function cellTags(cell) {
  return (cell.attempts > 1 && cell.attempt ? `<span class="tag" title="${t("cx.attempt_tip", { n: cell.attempts })}">${t("cx.attempt", { n: cell.attempt })}</span> ` : "")
    + (cell.rerunning ? `<span class="tag pending">${t("cx.rerunning")}</span> ` : "")
    + ((cell.extra || []).length ? `<span class="tag" title="${t("cx.extra_tag_tip")}">${t("cx.extra_tag")}</span> ` : "");
}

export function renderCellLegend() {
  return `<ul class="cx-legend">${CELL_STATES.map((s) => `<li><span class="cx cx-${s}">${cellState(s)}</span> <span class="sub">${esc(S.terms[s] ? L(S.terms[s].means) : "")}</span></li>`).join("")}</ul>`;
}

const batchTabs = (index, name) => (index.cellmatrix || []).map((x) => `<a href="#/cells/${enc(x.batch)}"${x.batch === name ? ' class="active"' : ""}>${esc(x.batch)}</a>`).join("");

export function renderCellMatrix(index, name) {
  const all = index.cellmatrix || [];
  const m = all.find((x) => x.batch === (name || all[0]?.batch));
  if (!m) return `${crumbs(["#/", t("nav.overview")], [null, t("nav.matrix")])}<p>${t("cx.no_batch", { name: esc(name || "") })}</p>`;
  const info = (k) => m.heads?.[k] || {};
  const head = m.tasks.map((k) => {
    const title = taskTitle(info(k));
    return `<th class="cx-task"><a href="#/task/${enc(k)}">${esc(k)}</a><div class="sub" title="${esc(title)}">${esc(title.length > 14 ? `${title.slice(0, 14)}…` : title)}</div></th>`;
  }).join("");
  const origin = m.tasks.map((k) => `<td class="cx-orig sub">${info(k).original != null ? t("cx.orig_line", { o: fmtNum(info(k).original, 1), l: info(k).solve_line != null ? fmtNum(info(k).solve_line, 2) : "–" }) : "–"}</td>`).join("");
  const cols = m.tasks.length + 2;
  const body = m.groups.map((g) => `<tr class="cx-group"><th colspan="${cols}">${esc(S.lang === "en" ? g.title_en || g.title : g.title)}</th></tr>` + g.conditions.map((c) => {
    const row = m.rows[c] || {};
    const tds = m.tasks.map((k) => {
      const cell = m.cells[`${k}|${c}`] || { state: "not-started", condition: c, task: k };
      const reason = cell.verdict ? verdictText(cell.verdict) : cell.stop_reason || "";
      return `<td class="cx cx-${cell.state}"><a href="${cellHref(m.batch, c, k)}" title="${esc(reason)}">${cellState(cell.state, S.terms[cell.state] ? L(S.terms[cell.state].means) : "")}${cellDetail(cell)}${cellSpend(cell)}</a>${cellTags(cell) ? `<div>${cellTags(cell)}</div>` : ""}</td>`;
    }).join("");
    const sum = `<td class="cx-sum"><div><strong>${t("cx.sum_scored", { n: row.scored ?? 0, m: row.tasks ?? m.tasks.length })}</strong></div>`
      + `<div>${row.mean != null ? t("cx.sum_mean", { x: fmtNum(row.mean, 2) }) : t("cx.sum_none")}</div><div>${t("cx.sum_solved", { k: row.solved ?? 0 })}</div>${rowSpend(row)}</td>`;
    return `<tr><th class="rowhead">${condLabel(c)}</th>${tds}${sum}</tr>`;
  }).join("")).join("");
  const b = (index.batches || []).find((x) => x.name === m.batch) || {};
  const desc = S.lang === "en" ? b.description_en || b.description : b.description;
  return `${crumbs(["#/", t("nav.overview")], ["#/matrix", t("nav.matrix")], [null, t("cx.title")])}
    <h2>${t("cx.batch", { name: esc(m.batch) })}</h2><nav class="tabs">${batchTabs(index, m.batch)}</nav>
    <p>${esc(desc)}</p><p class="note">${t("cx.lead")}</p>
    <p><a href="#/matrix/${enc(m.batch)}">${t("cx.legacy_link")}</a></p>
    <div class="scroll"><table class="matrix cxm"><thead><tr><th>${t("col.condition")}</th>${head}<th>${t("cx.summary")}</th></tr>
      <tr class="cx-origin"><th class="rowhead sub">${t("cx.original")}</th>${origin}<td></td></tr></thead><tbody>${body}</tbody></table></div>
    <p class="note">${t("cx.cell_note")}</p>
    ${section(t("cx.legend"), renderCellLegend())}`;
}

// ---- the cell page ----------------------------------------------------------------------------------------------

const ROLE_NOTE = { counted: "cx.role.counted", "environment-failure": "cx.role.environment", superseded: "cx.role.superseded", earlier: "cx.role.earlier", later: "cx.role.later" };

function verdictBlock(v) {
  if (!v) return "";
  return `<div class="cx-verdict"><span class="tag">${term(v.kind, tname(v.kind))}</span> ${esc(verdictText(v))}<div class="sub">${verdictWho(v)}</div></div>`;
}

function whyBlock(page) {
  const c = page.cell, runId = c.counted;
  const link_ = runId ? runLink(runId) : "";
  const rule = { result: "cx.why.result", live: "cx.why.live", latest: "cx.why.latest", excluded: "cx.why.excluded", none: "cx.why.none" }[c.rule] || "cx.why.none";
  const judged = (page.history || []).filter((h) => h.verdict);
  const list = judged.length ? `<ul>${judged.map((h) => `<li>${runLink(h.run_id)} — ${term(h.verdict.kind, tname(h.verdict.kind))}: ${esc(verdictText(h.verdict))}<div class="sub">${verdictWho(h.verdict)}</div></li>`).join("")}</ul>` : "";
  const cellVerdicts = (c.cell_verdicts || []).map((v) => verdictBlock(v)).join("");
  return `<p>${t(rule, { run: link_, n: c.attempt ?? "–", m: c.attempts })}</p>${c.rerunning ? `<p>${t("cx.why.rerunning")}</p>` : ""}${list}${cellVerdicts}
    <details><summary>${t("cx.why.rule_title")}</summary><ol><li>${t("cx.rule.1")}</li><li>${t("cx.rule.2")}</li><li>${t("cx.rule.3")}</li><li>${t("cx.rule.4")}</li><li>${t("cx.rule.5")}</li></ol><p class="note">${t("cx.rule.states")}</p></details>`;
}

const historySpend = (sp) => { const f = rawFigs(sp); return `<td>${fig(f, "model_s", true)}</td><td>${fig(f, "tokens", true)}</td><td>${fig(f, "turns", true)} / ${fig(f, "requests", true)}</td><td>${fig(f, "list_usd", true)}</td>`; };
const historyFoot = (page) => {
  const f = page.cell?.spend_total;
  return (page.history || []).length > 1 && f ? `<tr class="cx-total"><th colspan="6">${t("sp.total_row", { n: f.runs })}</th><td>${fig(f, "wall_s", true)}</td><td>${fig(f, "model_s", true)}</td><td>${fig(f, "tokens", true)}</td><td>${fig(f, "turns", true)} / ${fig(f, "requests", true)}</td><td>${fig(f, "list_usd", true)}</td></tr>` : "";
};

function extraBlock(page) {
  const list = (ids) => ids.length ? ids.map((i) => runLink(i)).join(", ") : `<span class="sub">${t("none")}</span>`;
  return (page.extra || []).map((e) => `<p class="note">${t("cx.extra_note")}</p>${kv([
    [t("cx.extra.asset"), `<code>${esc(e.asset)}</code>`],
    [t("cx.extra.target"), `<code>${esc(e.target)}</code>`],
    [t("cx.extra.decided"), `${esc(S.lang === "en" ? e.reason_en : e.reason)}<div class="sub">${esc(e.by)} · ${esc(e.date)} · ${esc(e.source)}</div>`],
    [t("cx.extra.given"), list(e.given || [])],
    [t("cx.extra.not_given"), list(e.not_given || [])],
  ])}`).join("");
}

export function renderCell(page, base = "data/") {
  const c = page.cell, res = page.result || {}, cfg = page.config || {}, ti = page.task_info || {};
  const sc = (res.scores || []).find((s) => PRIMARY_EVALUATORS.includes(s.evaluator) && s.summary);
  const sp = res.spend || {};
  const paper = res.paper;
  const paperLine = paper ? outputLine({ ...paper, role: "paper" }, base, res.run_id, true) : `<span class="sub">${t("cx.no_paper_file")}</span>`;
  const state = `<span class="cx cx-${c.state} cx-big">${cellState(c.state)}</span> ${cellTags(c)}`;
  const reason = c.verdict ? verdictBlock(c.verdict) : c.state === "paused" && c.stop_reason ? `<div>${t("run.stop_reason", { why: esc(c.stop_reason) })}</div>` : "";
  const result = kv([
    [t("cx.f.state"), `${state}<div class="sub">${esc(S.terms[c.state] ? L(S.terms[c.state].means) : "")}</div>${reason}`],
    [t("cx.f.run"), res.run_id ? `${runLink(res.run_id)} ${c.status ? statusBadge(c.status, c.state === "running") : ""}` : `<span class="sub">${t("cx.no_run")}</span>`],
    sc ? [t("cx.f.score"), `${term(sc.evaluator, tname(sc.evaluator))}: ${scoreText(sc)}${roleTag(sc.evaluator)}${relativeText(sc) ? `<div class="sub">${relativeText(sc)}</div>` : ""}`]
      : c.pending_parse ? [t("cx.f.score"), pendingTag()] : [t("cx.f.score"), `<span class="sub">${t("cx.no_score")}</span>`],
    [t("cx.f.paper"), paperLine],
    res.run_id ? [t("cx.f.review"), `<a href="#/run/${enc(res.run_id)}">${t("cx.review_link")}</a> <span class="sub">${t("cx.review_note")}</span>`] : null,
    [t("cx.f.time"), `${fmtDuration(sp.wall_s)} · ${fmtTime(res.started_at)} → ${fmtTime(res.ended_at)}`],
    ...(res.run_id ? spendRows(rawFigs(sp)).filter(([k]) => k !== t("metric.wall_s")) : []),
    [t("cx.f.billing"), fmtUsd(sp)],
    ...((c.spend_total?.runs || 0) > 0 ? [[`${t("sp.all_attempts")} <span class="sub">${t("sp.n_attempts", { n: c.spend_total.runs })}</span>`,
      spendRows(c.spend_total).map(([k, v]) => `<div>${k}: ${v}</div>`).join("")]] : []),
  ]);
  const cond = cfg.condition || {};
  const accounts = (cfg.accounts || []).length ? (cfg.accounts || []).map((a) => `<code>${esc(a)}</code>`).join(" ") : missing();
  const credNames = Object.entries(cond.credentials || {}).map(([k, v]) => `${esc(k)} = <code>${esc(v)}</code>`).join(", ");
  const config = `${kv([
    [t("col.condition"), `${condLabel(cond.name)} <div class="sub">${esc(L(cond.description_en && S.lang === "en" ? cond.description_en : cond.description))}</div>`],
    [t("col.system"), sysLink(cond.system)],
    [t("cx.f.accounts"), `${accounts}${credNames ? `<div class="sub">${t("cx.f.condition_accounts")}: ${credNames}</div>` : ""}<div class="sub">${t("cx.accounts_note")}</div>`],
  ])}
    <p class="note">${cfg.run ? t("cx.config_run", { run: runLink(cfg.run_id) }) : t("cx.config_planned")}</p>
    ${renderSetup(cfg.run || cfg.planned)}`;
  const taskBlock = `<h3>${esc(ti.id)} ${esc(taskTitle(ti))}</h3>${S.lang === "zh" && ti.title_en ? `<div class="sub">${esc(ti.title_en)}</div>` : S.lang === "en" && ti.title ? `<div class="sub">${esc(ti.title)}</div>` : ""}
    <h3>${t("tk.original_paper")}</h3>${paperBlock(ti.original)}
    <h3>${term("candidate-side", t("tk.candidate"))}</h3><p class="note">${t("cx.candidate_note")}</p>
    <ul class="plain">${(ti.candidate || []).map((f) => `<li><code>${esc(f.name)}</code> <span class="sub">${t("bytes", { n: esc(f.size) })}</span></li>`).join("") || `<li class="sub">${t("none")}</li>`}</ul>
    <p><a href="#/task/${enc(ti.id)}">${t("cx.task_page")}</a></p>`;
  const history = table([t("col.run"), t("col.start"), t("col.status"), t("cx.h.verdict"), t("cx.h.counts"), t("col.score"), t("col.elapsed"), t("metric.model_s"), t("metric.tokens"), t("sp.turns_requests"), t("sp.cost_list")],
    (page.history || []).map((h) => `<tr class="${h.role === "counted" ? "cx-counted" : ""}"><td>${runLink(h.run_id)}${(h.extra || []).length ? `<div class="sub"><span class="tag">${t("cx.extra_tag")}</span></div>` : ""}${h.credited_from ? `<div class="sub">${t("mx.credited", { batch: esc(h.credited_from) })}</div>` : ""}</td><td>${fmtTime(h.started_at)}</td>
      <td>${statusBadge(h.shown_status, h.live)}${h.status_reason ? `<div class="sub">${term(h.status_reason, tname(h.status_reason))}</div>` : ""}${h.stop_reason ? `<div class="sub">${t("run.stop_reason", { why: esc(h.stop_reason) })}</div>` : ""}</td>
      <td>${h.verdict ? `<span class="tag">${term(h.verdict.kind, tname(h.verdict.kind))}</span><div class="sub">${esc(firstClause(verdictText(h.verdict), 120))}</div><div class="sub">${verdictWho(h.verdict)}</div>` : "–"}</td>
      <td>${t(ROLE_NOTE[h.role] || "cx.role.earlier")}</td><td>${h.score ? `${fmtNum(h.score.value, 1)}${h.score.ratio != null ? ` · ${fmtNum(h.score.ratio, 2)}×` : ""}` : h.has_paper ? `<span class="sub">${t("cx.state.awaiting-review")}</span>` : "–"}</td>
      <td>${fmtDuration(h.wall_s)}</td>${historySpend(h.spend)}</tr>`), t("cx.no_runs"), historyFoot(page));
  const defects = (page.defects || []).length
    ? `<ul>${page.defects.map((d) => `<li><a href="${defectHref(d.system, d.id)}">${esc(S.lang === "en" ? d.title_en || d.title : d.title)}</a></li>`).join("")}</ul>` : "";
  return `${crumbs(["#/", t("nav.overview")], ["#/matrix", t("nav.matrix")], [`#/cells/${enc(page.batch)}`, esc(page.batch)], [null, `${esc(page.condition)} × ${esc(page.task)}`])}
    <h2>${t("cx.page_title", { condition: esc(page.condition), task: esc(page.task) })}</h2>
    <p class="lead">${esc(L(cond.full_name))} · ${esc(taskTitle(ti))}</p>
    <p><a href="${compareHref(page.task, page.condition)}">${t("cmp.from_run")}</a> · <a href="#/cells/${enc(page.batch)}">${t("cx.back")}</a></p>
    ${section(t("cx.sec.result"), result)}
    ${section(t("cx.sec.why"), whyBlock(page))}
    ${section(t("cx.sec.history", { n: (page.history || []).length }), history)}
    ${(page.extra || []).length ? section(t("cx.sec.extra"), extraBlock(page)) : ""}
    ${defects ? section(t("cx.sec.defects"), `<p class="note">${t("cx.defects_note")}</p>${defects}`) : ""}
    ${section(t("cx.sec.config"), config)}
    ${section(t("cx.sec.task"), taskBlock)}`;
}

// ---- known defects of the systems under test -----------------------------------------------------------------------

function defectBody(index, d, full = true) {
  const title = S.lang === "en" ? d.title_en || d.title : d.title;
  const text = S.lang === "en" ? d.text_en || d.text : d.text;
  const cells = (d.cells || []).map((c) => `<a href="${cellHref(c.batch, c.condition, c.task)}">${esc(c.condition)} × ${esc(c.task)}</a>`).join(" · ");
  const runs = (d.runs || []).map((r) => runLink(r)).join(" · ");
  const paths = (d.paths || []).length ? d.paths.map((p) => `<code>${esc(p)}</code>`).join("<br>") : `<span class="sub">${t("df.no_path")}</span>`;
  return `<div class="summary" id="defect-${esc(d.id)}"><h3>${full ? esc(title) : `<a href="${defectHref(d.system, d.id)}">${esc(title)}</a>`}</h3><p>${esc(text)}</p>${kv([
    [t("df.upstream"), `${paths}<div class="sub">${t("df.commit", { commit: esc(d.commit) })}</div>`],
    [t("df.evidence"), runs || `<span class="sub">${t("none")}</span>`],
    [t("df.cells"), cells || `<span class="sub">${t("df.no_cells")}</span>`],
    [t("df.decided"), t("cx.verdict_who", { by: esc(d.by), date: esc(d.date), source: esc(d.source) })],
  ])}</div>`;
}

export function renderDefects(index, f = {}) {
  const all = (index.defects || []).filter((d) => !f.system || d.system === f.system);
  const systems = [...new Set((index.defects || []).map((d) => d.system))];
  const groups = [...new Set(all.map((d) => d.system))].map((s) => `<section id="sys-${esc(s)}"><h2>${sysLink(s)} <span class="sub">(${all.filter((d) => d.system === s).length})</span></h2>${all.filter((d) => d.system === s).map((d) => defectBody(index, d, false)).join("")}</section>`).join("");
  const tabs = systems.length > 1 ? `<nav class="tabs"><a href="#/defects"${f.system ? "" : ' class="active"'}>${t("filter.all")}</a>${systems.map((s) => `<a href="#/defects?system=${enc(s)}"${f.system === s ? ' class="active"' : ""}>${esc(tname(s))}</a>`).join("")}</nav>` : "";
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.defects")])}<h2>${t("df.title")}</h2><p class="note">${t("df.lead")}</p>${tabs}${groups || `<p>${t("df.none")}</p>`}`;
}

export function renderDefect(index, system, id) {
  const d = (index.defects || []).find((x) => x.system === system && x.id === id);
  if (!d) return `<p>${t("df.not_found", { id: esc(id) })}</p>`;
  return `${crumbs(["#/", t("nav.overview")], ["#/defects", t("nav.defects")], [null, esc(S.lang === "en" ? d.title_en || d.title : d.title)])}
    <p>${sysLink(system)}</p>${defectBody(index, d, true)}`;
}

// A system's own page lists its known defects with a link to each.
export function systemDefects(index, name) {
  const mine = (index.defects || []).filter((d) => d.system === name);
  if (!mine.length) return "";
  return section(t("df.on_system", { n: mine.length }), `<p class="note">${t("df.system_note")} <a href="#/defects?system=${enc(name)}">${t("df.all_link")}</a></p>
    <ul>${mine.map((d) => `<li><a href="${defectHref(d.system, d.id)}">${esc(S.lang === "en" ? d.title_en || d.title : d.title)}</a> <span class="sub">${t("df.n_cells", { n: (d.cells || []).length })}</span></li>`).join("")}</ul>`);
}

// ---- glossary -------------------------------------------------------------------------------------------------------

const KINDS = ["condition", "system", "agent", "agent-setting", "model", "provider", "effort", "benchmark", "evaluator", "metric", "status", "purpose", "term"];

export function renderGlossary(index, focus = "") {
  const all = index.glossary || [];
  const groups = KINDS.map((k) => [k, all.filter((g) => g.kind === k)]).filter(([, gs]) => gs.length);
  const body = groups.map(([k, gs]) => `<h3>${t(`gl.kind.${k}`)}</h3><dl class="glossary">${gs.map((g) =>
    `<div id="term-${esc(g.id)}" class="${g.id === focus ? "focus" : ""}"><dt><code>${esc(g.id)}</code>${g.short && g.short !== g.id ? ` <span class="sub">(${esc(g.short)})</span>` : ""} — ${esc(L(g.name))}</dt><dd>${esc(L(g.means))}${g.url ? ` ${link(g.url, t("prov.link"))}` : ""}${g.kind === "condition" ? ` <a href="#/condition/${enc(g.id)}">${t("gl.details")}</a>` : g.kind === "system" ? ` <a href="#/system/${enc(g.id)}">${t("gl.details")}</a>` : g.kind === "benchmark" ? ` <a href="#/benchmark/${enc(g.id)}">${t("gl.details")}</a>` : ""}</dd></div>`).join("")}</dl>`).join("");
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.glossary")])}<h2>${t("gl.title")}</h2><p class="note">${t("gl.lead")}</p>${body}`;
}

// ---- about ------------------------------------------------------------------------------------------------------------

export function renderAbout(index, checks) {
  const c = checks || { problems: 0, explained: 0, items: [] };
  const areas = ["provenance", "setup", "item", "text", "glossary"];
  const counts = areas.map((a) => {
    const its = c.items.filter((i) => i.area === a);
    return `<tr><th class="rowhead">${t(`ck.area.${a}`)}</th><td>${its.filter((i) => !i.reason).length}</td><td>${its.filter((i) => i.reason).length}</td></tr>`;
  });
  const list = (sel) => `<ul class="checks">${sel.map((i) => `<li><span class="tag">${t(`ck.area.${i.area}`)}</span> ${esc(i.item)}: <code>${esc(i.field)}</code>${i.reason ? ` — ${esc(i.reason)}${verbatim()}` : ""}</li>`).join("")}</ul>`;
  const problems = c.items.filter((i) => !i.reason);
  const explained = c.items.filter((i) => i.reason && i.area !== "setup");
  const setupRuns = new Set(c.items.filter((i) => i.reason && i.area === "setup").map((i) => i.item));
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.about")])}<h2>${t("ab.title")}</h2>
    <p>${t("ab.p1")}</p><p>${t("ab.p2")}</p><p>${t("ab.p3")}</p>
    ${kv([[t("ab.updated"), fmtTime(index.generated_at)], [t("ab.sources"), t("ab.sources_text")]])}
    ${section(t("ab.checks"), `<p class="note">${t("ab.checks_note")}</p>${table([t("ck.area"), t("ck.problems"), t("ck.explained")], counts)}
      ${problems.length ? `<h3>${t("ck.problem_list")}</h3>${list(problems)}` : `<p>${t("ck.no_problems")}</p>`}
      ${explained.length ? `<details><summary>${t("ck.explained_list", { n: explained.length })}</summary>${list(explained)}</details>` : ""}
      ${setupRuns.size ? `<p class="note">${t("ck.setup_runs", { n: setupRuns.size })}</p>` : ""}`)}`;
}

// ---- browser glue ------------------------------------------------------------------------------------------------------

export function parseHash(hash) {
  const raw = String(hash || "").replace(/^#\/?/, "");
  const [path, query = ""] = raw.split("?");
  const parts = path.split("/");
  const params = Object.fromEntries(new URLSearchParams(query));
  return { view: parts[0] || "overview", arg: decodeURIComponent(parts.slice(1).join("/")), params };
}

export function pickLang(saved, navLang, urlLang) {
  if (LANGS.includes(urlLang)) return urlLang;
  if (LANGS.includes(saved)) return saved;
  return /^zh/i.test(navLang || "") ? "zh" : "en";
}

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch { /* private window or blocked storage: the choice lasts for this page only */ }
  return value;
}

async function main() {
  const root = document.getElementById("app");
  const stampEl = document.getElementById("stamp");
  const fetchJson = async (u) => { const r = await fetch(u, { cache: "no-store" }); if (!r.ok) throw new Error(`${u}: HTTP ${r.status}`); return r.json(); };
  const [site, strings] = await Promise.all([fetchJson("site.json"), fetchJson("strings.json")]);
  const base = site.data;
  const get = (p) => fetchJson(`${base}${p}?v=${Math.floor(Date.now() / 60000)}`);
  const lang = pickLang(store("rwe.lang"), navigator.language, new URLSearchParams(location.search).get("lang"));
  configure({ lang, strings });
  const applyTheme = (th) => { document.documentElement.dataset.theme = th === "auto" ? "" : th; };
  let theme = store("rwe.theme") || "auto";
  applyTheme(theme);
  let index = null;
  let checks = null;
  const chrome = (view) => {
    document.documentElement.lang = S.lang === "zh" ? "zh-CN" : "en";
    document.title = S.strings[S.lang]["site.title"];
    document.getElementById("site-title").textContent = S.strings[S.lang]["site.title"];
    document.getElementById("tagline").textContent = S.strings[S.lang]["site.tagline"];
    document.getElementById("nav").innerHTML = renderNav(view);
    document.getElementById("lang").textContent = S.lang === "zh" ? "English" : "中文";
    document.getElementById("theme").textContent = t(`theme.${theme}`);
    if (index) stampEl.textContent = S.strings[S.lang]["stamp"].replace("{time}", String(index.generated_at).replace("T", " ").replace("Z", " UTC"));
  };
  const render = async () => {
    const { view, arg, params } = parseHash(location.hash);
    try {
      index = await get("index.json");
      configure({ glossary: index.glossary, batches: index.conditions.plan.batches });
      chrome(view);
      let html;
      if (view === "matrix" && arg) html = renderBatch(index, arg, params);
      else if (view === "matrix") html = renderMatrix(index, params);
      else if (view === "batch") html = renderBatch(index, arg, params);
      else if (view === "cells") html = renderCellMatrix(index, arg);
      else if (view === "cell") html = renderCell(await get(`cells/${arg.split("/").map(enc).join("/")}.json`), base);
      else if (view === "defects") html = renderDefects(index, params);
      else if (view === "defect") { const [sys, ...rest] = arg.split("/"); html = renderDefect(index, sys, rest.join("/")); }
      else if (view === "tasks") html = renderTasks(index);
      else if (view === "task") html = renderTask(await get(`tasks/${enc(arg)}.json`));
      else if (view === "experiment") { location.replace(compareHref(arg)); return; }
      else if (view === "compare") {
        const path = arg.split("/").map(enc).join("/");
        const [cmp, task] = await Promise.all([get(`compare/${path}.json`), get(arg.includes("/") ? `items/${path}.json` : `tasks/${enc(arg)}.json`).catch(() => ({}))]);
        html = renderCompare(cmp, task, base, params.condition);
      }
      else if (view === "items") html = renderItems(index, params);
      else if (view === "item") {
        const [page, bench] = await Promise.all([get(`items/${arg.split("/").map(enc).join("/")}.json`), get(`tasks/${enc(taskUnit(arg))}.json`).catch(() => ({}))]);
        html = renderItem(page, bench);
      }
      else if (view === "conditions") html = renderConditions(index);
      else if (view === "condition") html = renderCondition(index, arg);
      else if (view === "systems") html = renderSystems(index);
      else if (view === "system") html = renderSystem(index, arg);
      else if (view === "benchmarks") html = renderBenchmarks(index);
      else if (view === "benchmark") html = renderBenchmark(index, await get(`tasks/${enc(arg)}.json`));
      else if (view === "runs") html = renderRuns(index, params);
      else if (view === "run") html = renderRun(await get(`runs/${enc(arg)}.json`), base);
      else if (view === "results") html = renderResults(index, params);
      else if (view === "performance") html = renderPerformance(index);
      else if (view === "ranking" && arg) html = renderRankingTask(await get(`ranking/${enc(arg)}.json`).catch(() => ({ task: arg })));
      else if (view === "ranking") html = renderRanking(index);
      else if (view === "analysis") html = renderAnalysis(index, arg);
      else if (view === "glossary") html = renderGlossary(index, arg);
      else if (view === "about") { checks = await get("checks.json").catch(() => null); html = renderAbout(index, checks); }
      else html = renderOverview(index);
      root.innerHTML = html;
      const form = document.getElementById("filters");
      if (form) form.addEventListener("change", () => {
        const q = new URLSearchParams([...new FormData(form)].filter(([, v]) => v)).toString();
        location.hash = `#/${view}${arg ? "/" + enc(arg) : ""}${q ? "?" + q : ""}`;
      });
      if (view === "glossary" && arg) document.getElementById(`term-${arg}`)?.scrollIntoView({ block: "center" });
      if (view === "compare" && params.condition) document.getElementById(`cmp-${params.condition}`)?.scrollIntoView({ block: "start" });
    } catch (err) {
      root.innerHTML = `<p class="badge failed">${t("error.data", { msg: esc(err.message) })}</p>`;
    }
  };
  document.getElementById("lang").addEventListener("click", () => { configure({ lang: store("rwe.lang", S.lang === "zh" ? "en" : "zh") }); render(); });
  document.getElementById("theme").addEventListener("click", () => {
    theme = store("rwe.theme", { auto: "light", light: "dark", dark: "auto" }[theme]);
    applyTheme(theme);
    chrome(parseHash(location.hash).view);
  });
  // Files on the data branch come from raw.githubusercontent.com, which serves a PDF as a download: such a file is
  // fetched and shown from a blob of its own type. A file of this site (the local preview) is used as it is.
  let held = false;   // the reader opened something on this page: no automatic refresh until the next page
  const sameOrigin = (u) => new URL(u, location.href).origin === location.origin;
  const blobUrl = async (u, type) => {
    if (sameOrigin(u)) return u;
    const r = await fetch(u);
    if (!r.ok) throw new Error(`${u}: HTTP ${r.status}`);
    return URL.createObjectURL(new Blob([await r.arrayBuffer()], { type }));
  };
  root.addEventListener("click", async (ev) => {
    const el = ev.target.closest("[data-open],[data-embed],[data-image],[data-preview],[data-tab]");
    if (!el || !root.contains(el)) return;
    held = true;
    if (el.dataset.tab != null && el.dataset.idx != null && el.tagName === "BUTTON") {
      const card = el.closest(".card");
      card.querySelectorAll(`[data-tab="${CSS.escape(el.dataset.tab)}"]`).forEach((x) => {
        if (x.tagName === "BUTTON") x.setAttribute("aria-selected", String(x === el));
        else x.hidden = x.dataset.idx !== el.dataset.idx;
      });
      return;
    }
    if (el.dataset.open != null) {
      if (!el.dataset.type || sameOrigin(el.dataset.open)) return;   // the link opens it
      ev.preventDefault();
      const w = window.open("", "_blank");
      try { const u = await blobUrl(el.dataset.open, el.dataset.type); if (w) w.location = u; else location.assign(u); }
      catch (err) { if (w) w.close(); alert(err.message); }
      return;
    }
    const box = el.closest(".actions")?.nextElementSibling;
    if (!box) return;
    if (!box.hidden) { box.hidden = true; box.innerHTML = ""; return; }
    box.hidden = false;
    box.innerHTML = `<p class="sub">…</p>`;
    try {
      if (el.dataset.embed) box.innerHTML = `<iframe title="PDF" src="${esc(await blobUrl(el.dataset.embed, "application/pdf"))}"></iframe>`;
      else if (el.dataset.image) box.innerHTML = `<img alt="" src="${esc(el.dataset.image)}">`;
      else {
        const r = await fetch(el.dataset.preview);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        box.innerHTML = `<pre>${esc(await r.text())}</pre>`;
      }
    } catch (err) { box.innerHTML = `<p class="badge failed">${esc(err.message)}</p>`; }
  });
  window.addEventListener("hashchange", () => { held = false; render(); window.scrollTo(0, 0); });
  setInterval(() => { if (!document.hidden && !held && !document.querySelector("details[open]")) render(); }, 60000);
  render();
}

if (typeof document !== "undefined" && typeof window !== "undefined") main();
