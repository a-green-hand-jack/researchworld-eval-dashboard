// ResearchWorld-Eval experiment dashboard. Read-only: it shows the facts in data/ and draws no conclusions.
// Pure render functions (data in, HTML string out) are exported for the tests; `configure` sets the language,
// the page strings (strings.json) and the glossary they use. The browser glue at the end fetches the data
// (site.json says from where) and routes on the URL hash; every page has its own address:
//   #/                      overview          #/matrix, #/matrix/<batch>     plan matrix, one batch
//   #/tasks, #/task/<id>    E2E tasks         #/compare/<task key>           one task under every condition
//   #/conditions, #/condition/<name>          #/systems, #/system/<name>
//   #/benchmarks, #/benchmark/<id>            #/items, #/item/<benchmark>/<item>  benchmark items, one item
//   #/runs, #/run/<run-id>
//   #/results               summaries         #/glossary, #/glossary/<term>  #/about
// A query after the route (#/runs?system=coding-agent) holds a page's filters; ?lang=en in the address picks
// the language.

export const LANGS = ["zh", "en"];
const S = { lang: "zh", strings: { zh: {}, en: {} }, terms: {} };

export function configure({ lang, strings, glossary } = {}) {
  if (strings) S.strings = strings;
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

// An extra score's name: its glossary term, also for a per-model extra "<name> (<model>)"
function extraName(k) {
  const m = /^(.*) \(([^()]+)\)$/.exec(k);
  return m && S.terms[m[1]] ? `${term(m[1], tname(m[1]))} (${esc(m[2])})` : term(k, S.terms[k] ? tname(k) : k);
}

function mainScore(run) {
  const s = (run.scores || []).find((x) => x.summary);
  return s ? `${term(s.evaluator, tname(s.evaluator))}: ${scoreText(s)}` : "–";
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
const section = (title, body, id = "") => `<section${id ? ` id="${id}"` : ""}><h2>${title}</h2>${body}</section>`;
const table = (head, rows, empty) => `<div class="scroll"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.length ? rows.join("") : `<tr><td colspan="${head.length}" class="sub">${empty || t("none")}</td></tr>`}</tbody></table></div>`;
const crumbs = (...items) => `<nav class="crumbs">${items.map(([href, label]) => (href ? `<a href="${href}">${label}</a>` : `<span>${label}</span>`)).join(" › ")}</nav>`;

function link(url, text) {
  if (!url) return esc(text || "–");
  return /^https?:\/\//.test(url) ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text || url)}</a>` : esc(text || url);
}

// ---- navigation ---------------------------------------------------------------------------------------

export const NAV = ["overview", "matrix", "tasks", "benchmarks", "items", "conditions", "systems", "runs", "results", "glossary", "about"];

export function renderNav(view) {
  const active = { batch: "matrix", task: "tasks", experiment: "tasks", condition: "conditions", system: "systems", benchmark: "benchmarks", item: "items", run: "runs" }[view] || view;
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
    <div class="stats">${stats}</div>
    ${section(t("ov.plan"), renderPlan(index, {}, true))}
    ${section(t("ov.running"), liveList)}
    ${section(t("ov.recent"), table([t("col.run"), t("col.system"), t("col.purpose"), t("col.status"), t("col.start")], recent) + `<p><a href="#/runs">${t("ov.all_runs_link")}</a></p>`)}`;
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
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.matrix")])}<h2>${t("mx.title")}</h2>
    <nav class="tabs">${tabs}</nav>${renderFilters(index, f, ["system", "condition"])}${renderPlan(index, f)}`;
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
    return `<td class="cell ${cell.state}">${linkTo}${sc ? `<div>${scoreText(sc)}</div>` : ""}${cell.runs?.length > 1 ? `<div class="sub">${t("mx.n_runs", { n: cell.runs.length })}</div>` : ""}${plan}</td>`;
  }).join("") + `</tr>`).join("");
  const desc = S.lang === "en" && m.description_en ? m.description_en : m.description;
  return `${crumbs(["#/", t("nav.overview")], ["#/matrix", t("nav.matrix")], [null, esc(name)])}
    <h2>${t("mx.batch", { name: esc(name) })}</h2><nav class="tabs">${tabs}</nav>
    <p>${esc(desc || "")}${m.error ? ` <span class="badge failed">${esc(m.error)}</span>` : ""}</p>
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
      <td><a href="#/run/${enc(cell.latest)}">${esc(tname(cell.status || cell.state))}</a>${why ? `<div class="sub">${esc(why)}</div>` : ""}${cell.stop_reason ? `<div class="sub">${t("run.stop_reason", { why: esc(cell.stop_reason) })}</div>` : ""}${cell.conclusion ? `<div class="sub">${t("rep.concluded", { why: esc(L({ zh: cell.conclusion, en: cell.conclusion_en || cell.conclusion })) })}</div>` : ""}</td>
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
export function fileWhy(f) {
  const r = f.reason || f.file_reason;
  if (r === "credential") return t("dl.why.credential");
  if (r === "unreadable-pdf") return t("dl.why.unreadable_pdf");
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
  const scores = (r.scores || []).map((s) => `<div>${term(s.evaluator, tname(s.evaluator))}: <strong>${scoreText(s)}</strong>` +
    (s.result ? `<details><summary>${t("run.rationale")}</summary><pre>${esc(JSON.stringify(s.result, null, 1))}</pre></details>` : "") + `</div>`)
    .concat((r.unscored || []).map((e) => `<div>${term(e, tname(e))}: <span class="missing">${t("run.unscored")}</span></div>`));
  const key = r.key_outputs || [];
  const [lead, ...rest] = key;
  const others = r.outputs || [];
  const otherList = others.slice(0, OUTPUTS_SHOWN).map((f) => outputLine(f, base, r.run_id)).join("");
  return `<div class="status">${runStatus(r)}${r.purpose !== "evaluation" ? ` <span class="sub">(${purpose(r.purpose)})</span>` : r.unfinished ? ` ${runPurpose(r)}` : ""}</div>
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
    <p class="lead">${cmp.kind === "e2e" ? `<a href="#/task/${enc(cmp.key)}">${t("cmp.task_page")}</a>` : `<a href="${itemHref(cmp.key)}">${t("cmp.item_page")}</a>`}${(task.batches || []).length ? ` · ${t("col.batch")}: ${task.batches.map((b) => `<a href="#/matrix/${enc(b)}">${esc(b)}</a>`).join(", ")}` : ""}</p>
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
    <td>${(x.batches || []).map((b) => `<a href="#/matrix/${enc(b)}">${esc(b)}</a>`).join(", ") || "–"}</td>
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
    <p class="lead"><a href="${compareHref(page.key)}">${t("tk.under_conditions")}</a> · <a href="#/benchmark/${enc(page.benchmark)}">${t("it.benchmark_page")}</a>${(page.batches || []).length ? ` · ${t("col.batch")}: ${page.batches.map((b) => `<a href="#/matrix/${enc(b)}">${esc(b)}</a>`).join(", ")}` : ""}</p>`;
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
      c.pending?.length ? [t("cd.pending"), esc(c.pending.join(", "))] : null])}
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
    ${section(t("sy.runs", { n: runs.length }), renderRunsTable(runs))}`;
}

// ---- benchmarks ------------------------------------------------------------------------------------------------

export function renderBenchmarks(index) {
  const rows = Object.values(index.tasks || {}).filter((x) => x.kind === "benchmark").map((b) => {
    const p = b.provenance || {};
    return `<tr><th class="rowhead"><a href="#/benchmark/${enc(b.id)}">${esc(tname(b.id))}</a><div class="sub"><code>${esc(b.id)}</code></div></th>
      <td>${p.paper?.none ? `<span class="sub">${t("prov.none")}</span>` : p.paper?.url ? link(p.paper.url, p.paper.title) : missing()}</td>
      <td>${p.subset?.count ?? "–"}</td><td><a href="#/items?benchmark=${enc(b.id)}">${b.items ?? "–"}</a></td><td>${esc(p.licence?.code || "–")}</td></tr>`;
  });
  return `${crumbs(["#/", t("nav.overview")], [null, t("nav.benchmarks")])}<h2>${t("bm.title")}</h2><p class="note">${t("bm.lead")}</p>
    ${table([t("bm.name"), t("prov.paper"), t("bm.items_used"), t("bm.items_all"), t("bm.code_licence")], rows)}`;
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
      [t("col.batch"), batches.map((b) => `<a href="#/matrix/${enc(b.name)}">${esc(b.name)}</a>`).join(", ") || "–"],
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
  const scores = (page.scores || []).map((s) => `<tr><td>${term(s.evaluator, tname(s.evaluator))}<div class="sub">${esc(s.version || "")}</div></td>
    <td>${scoreText(s)}${s.summary?.label ? `<div class="sub">${esc(s.summary.label)}${S.lang === "en" ? verbatim() : ""}</div>` : ""}</td>
    <td>${Object.entries(s.summary?.extras || {}).map(([k, v]) => `${extraName(k)} ${fmtNum(v)}`).join(", ") || "–"}</td>
    <td>${s.result ? `<details><summary>${t("run.rationale")}</summary><pre>${esc(JSON.stringify(s.result, null, 1))}</pre></details>` : "–"}</td></tr>`)
    .concat((page.unscored || []).map((e) => `<tr><td>${term(e, tname(e))}</td><td><span class="missing">${t("run.unscored")}</span><div class="sub">${t("run.unscored_note")}</div></td><td>–</td><td>–</td></tr>`));
  const files = (page.deliverables || []).map((f) => {
    const href = `${dataBase}files/${enc(page.run_id)}/${String(f.path).split("/").map(enc).join("/")}`;
    const name = f.status === "published" ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(f.path)}</a>` : esc(f.path);
    return `<tr><td>${t(`dl.${f.kind}`)}${f.key ? ` <span class="tag">${t("cmp.key_output")}</span>` : ""}</td><td>${name}</td><td>${esc(f.size ?? "–")}</td><td>${f.status === "published" ? t("dl.published") : `${f.status === "withheld" ? t("dl.withheld") : t("dl.listed")}: ${fileWhy(f)}`}</td></tr>`;
  });
  const audit = page.audit ? Object.entries(page.audit).map(([k, v]) => `${esc(k)}=${esc(v)}`).join(", ") : why(page, "audit");
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
    ${section(t("run.results"), scores.length ? table([t("run.evaluator"), t("col.score"), t("run.extras"), t("run.basis")], scores) : `<p class="sub">${t("run.no_scores")}</p>`)}
    ${section(t("run.deliverables"), files.length ? table([t("dl.kind"), t("dl.file"), t("dl.bytes"), t("dl.public")], files) : `<p class="sub">${t("run.no_deliverables")}</p>`)}`;
}

// ---- results ------------------------------------------------------------------------------------------------------

export function renderAggregates(rows, key) {
  const evs = [...new Set(rows.flatMap((r) => Object.keys(r.scores || {})))].sort();
  const head = [key === "condition" ? t("col.condition") : t("col.system"), t("res.runs"), t("res.completed"), t("res.failed"), t("res.running"),
    ...evs.map((e) => `${term(e, tname(e))}<div class="sub">${t("res.mean_sd")}</div>`), t("res.cost"), t("res.wall")];
  const body = rows.map((r) => `<tr><th class="rowhead">${key === "condition" ? condLabel(r[key]) : sysLink(r[key])}</th><td>${r.runs}</td><td>${r.completed}</td><td>${r.failed}</td><td>${r.running}</td>` +
    evs.map((e) => {
      const s = r.scores[e];
      if (!s) return "<td>–</td>";
      const sd = s.variance != null ? ` ± ${fmtNum(Math.sqrt(s.variance))}` : "";
      return `<td title="${esc(s.label)}, max ${esc(s.max)}">${fmtNum(s.mean)}${sd} (${s.n})</td>`;
    }).join("") +
    `<td>${r.usd != null ? t("res.usd_runs", { usd: Number(r.usd).toFixed(2), n: r.usd_runs }) : "–"}</td><td>${fmtDuration(r.wall_s)}</td></tr>`);
  return table(head, body, t("run.none"));
}

const PROCESS = ["wall_s", "model_s", "turns", "requests", "tokens", "usd", "equivalent_usd"];

export function renderProcess(rows, key) {
  const fmt = { wall_s: fmtDuration, model_s: fmtDuration, turns: (v) => fmtNum(v, 1), requests: (v) => fmtNum(v, 1), tokens: kTokens,
    usd: (v) => `$${Number(v).toFixed(2)}`, equivalent_usd: (v) => `$${Number(v).toFixed(2)}` };
  const head = [key === "condition" ? t("col.condition") : t("col.system"), t("res.finished"), ...PROCESS.map((m) => `${t(`metric.${m}`)}<div class="sub">${t("res.mean_n")}</div>`)];
  const body = rows.map((r) => {
    const p = r.process || { runs: 0 };
    return `<tr><th class="rowhead">${key === "condition" ? condLabel(r[key]) : sysLink(r[key])}</th><td>${p.runs}</td>` +
      PROCESS.map((m) => { const e = p[m] || {}; return e.mean == null ? `<td>–</td>` : `<td>${fmt[m](e.mean)} <span class="sub">(${e.n}/${p.runs})</span></td>`; }).join("") + "</tr>";
  });
  return table(head, body, t("run.none")) + `<p class="note">${t("res.process_note")}</p>`;
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
    <nav class="tabs">${tabs}</nav><p class="note">${t("res.note")}</p>
    ${section(t("res.by_condition"), renderAggregates(agg.condition, "condition"))}
    ${section(t("res.by_system"), renderAggregates(agg.system, "system"))}
    ${section(t("res.process_by_condition"), renderProcess(agg.condition, "condition"))}
    ${section(t("res.process_by_system"), renderProcess(agg.system, "system"))}
    ${section(t("res.spend"), renderSpend((index.runs || []).filter((r) => p === "all" || r.purpose === p)))}`;
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
      configure({ glossary: index.glossary });
      chrome(view);
      let html;
      if (view === "matrix" && arg) html = renderBatch(index, arg, params);
      else if (view === "matrix") html = renderMatrix(index, params);
      else if (view === "batch") html = renderBatch(index, arg, params);
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
