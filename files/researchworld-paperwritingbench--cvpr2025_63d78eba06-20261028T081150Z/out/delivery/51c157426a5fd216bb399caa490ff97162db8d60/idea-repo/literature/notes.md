# Literature notes: what each verified entry supports (all in `literature/refs.bib`, 34 entries, all <= 2024-11)

Verification: titles/authors/year/venue checked 2026-10-28 against Semantic Scholar (batch by arXiv id: `literature/s2_meta.json`), Crossref (DOIs; `tools/crossref.py`), OpenAlex; JiT arXiv v1 title checked on arxiv.org/abs/2402.01401v1. arXiv itself was rate-limited (429), `tools/verify_arxiv.py` is kept but `arxiv_meta.json` was not produced.
Page numbers/volumes were left out (not verified) - bibtex entries are complete enough for `ieeenat_fullname`.
**Not verified by any index**: `khosla2011novel` (Stanford Dogs; standard dataset-page citation). Everything else matched a record. The Foster arXiv paper was later retitled "An Information Theoretic Approach to Machine Unlearning" (TMLR 2024); `foster2024zero` cites the arXiv v1 title that matches the name "JiT / Lipschitz regularization" in the log.
The log names baselines but gives no citations; the mapping below is my identification from the descriptions in the log and should be phrased in the paper as "following/adapted from", not as a claim of the original authors' protocol.

## Problem, motivation, definitions
- `cao2015towards`, `voigt2017eu` (GDPR), `ginart2019making`: the right-to-be-forgotten motivation / the unlearning problem; `xu2023machine`, `nguyen2022survey`: surveys.
- `bourtoule2021machine` (exact, sharded retraining), `neel2021descent`, `ullah2021machine`, `izzo2021approximate`: approximate/exact unlearning with and without guarantees.
## Newton / influence / Hessian-based removal (the update the method builds on)
- `koh2017understanding` (influence functions), `guo2020certified` (Newton-step certified removal; needs the remaining-data Hessian = the "Unlearned(+)" setting), `sekhari2021remember` (generalization-guarantee unlearning with Hessian, needs remaining-data statistics), `golatkar2020eternal` / `golatkar2020forgetting` (Fisher/NTK scrubbing), `warnecke2023machine` (influence-based unlearning of features/labels), `thudi2022unrolling`.
## Mixed linear networks / linearization (Section on deep nets)
- `golatkar2021mixed` (mixed-linear forgetting: the log's "Mixed Linear Networks" setup). `he2016deep`, `deng2009imagenet`: ResNet-18 ImageNet-pretrained feature extractor.
## Zero-shot / source-free and the log's baselines
- JiT (Lipschitz regularization): `foster2024zero`. Zero-shot class-level unlearning: `chundawat2023zero`, `kodge2024deep`; teacher/selective methods: `chundawat2023bad`, `foster2024fast`, `chen2023boundary` (class-level / decision boundary).
- NegGrad: gradient ascent on forget data, used as a baseline in `kurmanji2023towards` (SCRUB paper) and described in `golatkar2020forgetting`; Random Labels: relabelling forget samples and fine-tuning (cf. `graves2021amnesiac`, `golatkar2020forgetting`, `tarun2023fast`).
- Adversarial (adversarial examples + weight importance): `cha2024learning` (instance-wise unlearning). `fan2024salun`: saliency-based unlearning, further context for instance/class forgetting.
## Evaluation
- MIA: `shokri2017membership` (the log does not state its MIA protocol; do not describe it). Datasets: `krizhevsky2009learning` (CIFAR-10/100), `khosla2011novel` (Stanford Dogs, UNVERIFIED), `griffin2007caltech` (Caltech-256).

## Not cited / avoid
- Do not cite anything for specific claims the log does not supply (e.g. SDP solver, theorem statements).
- Do not use arXiv 2303.12033 for Boundary Unlearning (that id is a different paper); `chen2023boundary` is verified by DOI instead.
