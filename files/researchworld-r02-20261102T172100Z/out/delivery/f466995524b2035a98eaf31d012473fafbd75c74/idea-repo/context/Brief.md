# Brief: reliability of conformal regions for compositional responses

## Authority and frozen material

The task is `world/idea-repo#1` (Research objective), whose frozen material is `/initial-state/inputs/0/{TASK.md,data.md,resources.md,deliverable.md,starter_literature.md}`. All five files have been read in full. The SHA-256 manifest supplied with the objective is authoritative; `context/input_manifest.json` copies it for provenance. This brief interprets requirements; the objective wins in any disagreement.

## Binding requirements (quoted)

The central question is: **“如何评价保形预测方法在组成型输出上的可靠性？不同方法在哪些条件下更适用？”** (How should the reliability of conformal prediction for compositional outputs be evaluated, and under which conditions are different methods more suitable?)

The requested research steps are:

> 1. 梳理现有保形方法与评价方式的做法与局限，明确你要回答的具体研究问题与假设；
> 2. 设计并实现能回答你的研究问题的实验方案，说明选择依据，并量化结果的不确定性；
> 3. 可以使用自行生成的合成数据，也可以使用公开真实数据集（可用数据的类别见 `data.md`）；
> 4. 如能给出理论分析，给出推导并用实验核对；
> 5. 说明你的结论在什么条件下成立、哪些条件下不应外推。

Thus literature, specific questions/hypotheses, a justified implemented design, experimental uncertainty, and explicit external-validity limits are required. Theory is optional; any theory included needs derivation and empirical checking. Negative or unexpected results are acceptable.

> 结论必须有可复现的实验证据支持，并报告不确定性

> 时间上限一周（含阅读、实现、实验、写作），以 CPU 为主、至多数个 GPU 小时，存储 < 10 GB，不需要付费 API

`resources.md` gives an indicative, unmeasured estimate of 10^3–10^4 samples and tens of CPU-hours; these are planning estimates, not required sample counts or measured costs. Actual sandbox/resource ceilings control execution.

`data.md` explicitly permits **“下列公开数据、其他公开数据，或完全使用自行生成的合成数据”**. CIFAR-10 is an option, not a required experiment. It describes the 60,000-image/10-class dataset, the 50,000/10,000 split, acquisition URL/torchvision, and citation request; its page supplies no explicit license. If public data are selected, verify access/license/version and record them. A wholly synthetic study needs a specified generator, parameters, seeds, and limitations rather than a download.

`deliverable.md` requires:

> 一篇完整的研究论文（PDF 与 LaTeX 源文件）。从 ICML、ICLR、NeurIPS 中自选一个会议，使用该会议最新一届的官方 LaTeX 模板，遵守其正文页数上限（参考文献、附录是否计入页数按该会议的规定）；该会议要求随文提交的 checklist（例如 NeurIPS 的 paper checklist）一并填写。

> 论文至少包含摘要、引言、相关工作、方法、实验、讨论与局限、参考文献。

> 全部代码与复现说明：环境与依赖版本、数据获取步骤和所用数据的版本、随机种子、运行命令和预计耗时，以及论文中每张表、每张图由哪个脚本生成。

The paper is judged to the chosen venue's main-conference standards: novelty/positioning, design and controls, uncertainty, sufficient evidence for every conclusion, clarity/reproducibility, and honest limitations. A permitted synthetic scope does not by itself establish novelty or adequate evidence.

> 论文中的每个数字、每张表和每张图都必须来自你在本任务中实际运行、随附代码可以重新产生的结果；不得编造数据或结果，不得用占位数字、估计值或“示意”的合成结果冒充实测结果。

> 失败的运行、与预期不符的结果和放弃的方案如实报告；因预算没有完成的实验写明未完成，不写成已完成。

> 只引用真实存在、你确实查阅过的文献，不得编造引用。

The supplied task also prohibits searching for, accessing, reading, using, or guessing the identity/results of a withheld published study, including its mirrors, abstract/review pages, code, and pages citing/discussing/reproducing it. Starter sources are expressly allowed. Stop any accidental encounter immediately and record the URL, material, and amount read in reproduction notes. We use exact starter identifiers, no broad topic search and no citation traversal. No prohibited encounter was recognized during this context work.

## Operational question and target

The study plan owner settled the concrete question in protocol v1.2: for **observed compositional responses** Y in Δ^(K−1), how do joint split-conformal scores, calibration schemes, and coordinatewise controls trade marginal and group reliability against region size under specified synthetic mechanisms?

Three tasks must remain distinct:

1. A classifier supplies a probability vector p̂(X), but the target is a class label L. Coverage is P(L in a subset of labels). APS/RAPS and class-conditional classification address this task.
2. A latent probability vector p(X) is the target, inferred from finite/noisy labels. Covering that latent vector requires observation assumptions beyond standard label coverage.
3. An observed vector Y is the response (synthetic proportions or empirically observed distribution labels). Coverage is P(Y in a region of the simplex). This is the proposed benchmark. A random Y need not equal p(X) or a noiseless truth.

The allowed credal-set source already studies distribution-vector labels and conformal simplex regions, so it is close prior work. It cannot be dismissed as wholly a different target. Its interpretation of vectors as class distributions and noisy annotation labels differs from the synthetic response generator; the mathematical overlap is substantial.

The paper must state this scope in its abstract/introduction and must not claim that its experiments establish calibrated softmax probabilities, latent clean-probability coverage, classification-set performance, human utility, or universal fairness.

## What permitted prior work establishes

Source locations, versions, read extents, and limitations are in `context/literature.md`; exact PDF URLs and hashes are in `context/retrieval.json`. This is a deliberately bounded background assessment, not an exhaustive novelty search.

- Split conformal calibrates a scalar nonconformity score held fixed independently of calibration/test data. Exchangeable scores give finite-sample **marginal** coverage. Any score can be valid; usefulness/adaptivity depends on its geometry and predictor (Angelopoulos & Bates, §§1, 3).
- Full conformal, split conformal and refitting-based alternatives have computation/statistical tradeoffs. Jackknife+ has a general worst-case 1−2α bound in the ordinary construction; it must not be described as having the same unconditional 1−α theorem as split conformal (Lei et al.; Barber et al.). The proposed study can focus on split calibration, but must not claim to benchmark every conformal family.
- Standard marginal coverage can hide poor subgroup coverage. Fixed-group calibration gives within-group coverage under the appropriate exchangeability conditions; it can require larger or infinite sets in sparse groups. Classwise and clustered classification work illustrates the granularity/data tradeoff; it does not prove arbitrary conditional validity for our regions (Ding et al.; Angelopoulos & Bates §4.1).
- Multivalid methods target richer finite collections of groups/thresholds than ordinary global calibration (Jung et al.). Merely reporting two groups is not a multivalid theorem.
- Weighted conformal under covariate shift uses invariant Y|X, support/absolute-continuity assumptions and likelihood ratios (Tibshirani et al.). Unweighted calibration has no general shift guarantee. A group-mixture shift preserving all within-group joint laws is a special, explicit mechanism under which group calibration remains defensible.
- Javanmardi et al. §§4–5 already conformalize simplex-valued distribution labels, using TV, KL, Wasserstein, inner-product and Dirichlet-likelihood scores. They evaluate coverage and discretized-simplex fractions and repeat random splits. TV and preferably KL are relevant inexpensive baselines for the proposed first-order predictor comparison. Include them or justify exclusion in the plan. No necessity to reproduce their neural/second-order predictor when holding predictor fixed to isolate geometry.
- Javanmardi et al. §4.1 distinguishes noisy distribution-label coverage from clean latent-distribution coverage; no transfer is automatic. Likewise, pseudocount/zero replacement changes the scored target or requires an explicit inverse-image region.
- Cresswell et al.'s human-subject classification study cautions against equating coverage parity with equitable decisions. Our simulation cannot support a human-utility/fairness claim.
- Aitchison (1982), Vovk et al. (2005), and Papadopoulos et al. (2002) appear in the supplied reading list; original full text was not obtained in our attempts. Do not imply these originals were consulted or include them in the manuscript merely on this ledger's authority. The log-ratio definitions used here are explicit mathematical conventions; relevant original access remains a stated background limitation.

## Evaluation and reporting conventions

**Validity.** Use whole-vector membership, not mean coordinate coverage, as the principal reliability endpoint. For calibration size n, use k=ceil((n+1)(1−α)), the kth smallest score, and q=+∞ when k=n+1; include score≤q. The lower guarantee allows ties; the standard near-exact upper bound needs no ties or appropriate randomization. Include a rank/quantile check and a calibration-size check. Bonferroni coordinate calibration at α/K controls familywise error by a union bound; per-coordinate α does not in general.

**Conditional diagnostics.** Report prespecified group coverages and group sizes alongside marginal coverage. Finite collections of diagnostics do not certify coverage at every X. Distinguish estimating each group's coverage across independent trials from simultaneous confidence bands across all groups/cells. Identify groups selected using training information versus oracle generator metadata.

**Uncertainty.** Repeated fresh independent synthetic train/calibration/test draws allow replication-based uncertainty. Methods should share draws for paired comparisons. Do not treat all test memberships across shared calibration sets as independent Bernoulli observations. Separate calibration/training variation, finite-test error and numerical volume estimation error. The tutorial's Beta/beta-binomial reference applies to iid continuous scores conditional on a frozen training fit, not arbitrary ties, shifts, or group mixtures without conditioning.

**Efficiency.** Report size only with a declared common measure and coverage context. Radii from raw Euclidean and log-ratio coordinates have different units. Uniform-simplex area fraction for K=3 is a useful common measure with MC uncertainty, but favors a particular measure on compositions; it is not a universal utility metric. In high dimension, a zero Monte Carlo hit fraction is not proof of zero region size. Mark unresolved estimates and avoid cross-geometry claims based on incompatible radii. TV/KL regions can be evaluated using the same candidate-simplex samples.

**Geometry/zeros.** clr(y)_j=log(y_j)−K^−1∑log(y_l) is defined only for strictly positive compositions. State distance normalization; ||clr(y)−clr(μ)||₂ is isometric to a norm in an orthonormal ilr basis, so these are not independent method families. Raw distance regions should be intersected with the simplex. Exact zeros cannot simply be logged. For Tε(y)=(y+ε)/(1+Kε), distinguish coverage of Tε(Y) from coverage of Y under the inverse-image region {y:Tε(y) in Cε(x)}. Applying a transformed-space set directly to untransformed outcomes is a different diagnostic without the same theorem.

**Figures/tables.** The source conventions suggest nominal-versus-achieved coverage curves, split/replication distributions or intervals, grouped coverage with target reference lines, coverage-versus-size comparisons, and a K=3 simplex illustration of actual measured regions. Any plotted region/example must be generated by included code using saved fit/calibration information. Do not compare classification cardinality with simplex area. Every number and graphic needs run/script/input provenance.

## Research hypotheses and settled scope

H1: joint split-calibrated scores attain nominal marginal coverage under iid positive-response mechanisms despite geometry differences; the efficiency ordering is mechanism/measure dependent.

H2: heterogeneous noise can yield marginally reliable but undercovered groups; training-only local scaling or group calibration may improve group reliability, at costs affected by calibration size.

H3: naive coordinatewise calibration need not attain simultaneous nominal coverage; Bonferroni is a conservative valid control.

H4: group-mixture shift can break global calibration while preserving the conditions for within-group calibration; this does not establish robustness to arbitrary shift.

H5: boundary/zero handling affects region geometry and target interpretation; conclusions about positive logistic-normal outcomes need not extend to structural zeros.

These are research questions, not results. They overlap known conformal facts; any contribution must be in the rigorous controlled evaluation and diagnostic insight actually supported by runs. The plan owner has settled their operational scope; measured answers remain pending.

## Ownership and completion map

- Context (idea-repo): this Brief, permitted-source ledger/bibliography, target and prior-work bounds.
- Plan (story-repo): final questions/hypotheses, experiment matrix, comparisons, responsibility split, CODEOWNERS and integration of supplied context.
- Feasibility (idea-review-repo): independent assessment of achievable scope/resources before costly work.
- Analysis (experiment-repo): generator/model, theory derivations and checks, seeds/runs, controls, diagnostics and all result uncertainty/provenance.
- Presentation (figtab-repo): faithful figures/tables with their scripts and visual uncertainty.
- Venue (venue-repo): latest official template, page-count and checklist requirements.
- Report (paper-repo): complete paper PDF/LaTeX, integrated code/reproduction instructions, evidence-linked claims and limitations.
- Reviews (internal/external review owners): independent claim/objective checks and reader assessment.

Protocol alignment checked against story-repo revision `a72186db8dfbf281e89e0af632ce07e4f12426c2` (`plan/study_protocol.md`, v1.2): the target, shared fitted predictor, marginal/group distinctions, common K=3 area, uncertainty and zero/rank checks agree with this Brief. TV and forward KL are now required source-motivated supplements, and known-ratio weighted conformal is an explicitly oracle shift comparison. The plan records that score supplements were added after the seven-method core job started, with no confirmatory outcome inspected by its owner; they must retain their separate chronology rather than being described as part of the original prespecification. On K=3, TV equals raw maximum residual algebraically, so those results are a duplicate region, not independent evidence. Final protocol maintenance belongs to story-repo; venue details belong to venue-repo; measured empirical effects belong to experiment-repo. Context does not hold back established implementation or consume judging-only material. The objective imposes no numerical effect target and permits negative findings. A complete paper and code remain required even if a hypothesis is contradicted.
