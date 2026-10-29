# Literature: verified entries and where they belong (idea-repo)

All keys are in `literature/related.bib` (45 entries; compiles with `iclr2025_conference.bst`, no BibTeX warnings). Each entry was matched by title/authors/date against OpenAlex and/or the arXiv API on 2026-10-28; all are dated before 2024-10. The paper may cite a subset; it must cite only keys present in its own `references.bib`.

## Must-cite (named or implied by the supplied material)
| Key | What it is | Where |
|---|---|---|
| dagan2024getting | Token healing baseline (the Fig. 6 caption attributes it to "Dagan et al., 2024") | Related work, Experiments (FIM baselines), Fig. 6 caption |
| athiwaratkun2024token | Token alignment baseline ("Athiwaratkun et al., 2024" in the Fig. 6 caption) | same |
| bavarian2022efficient | FIM training; PSM/SPM templates; HumanEval Random Span benchmark ("Bavarian et al., 2022" in the Fig. 6 caption) | Intro, Related work, Experiments |
| chen2021evaluating | HumanEval, pass@k | Experiments |
| austin2021program | MBPP | Experiments |
| hendrycks2021measuring, bisk2020piqa, kwiatkowski2019natural, joshi2017triviaqa, cobbe2021training | MMLU, PIQA, NQ, TriviaQA, GSM8K | Experiments |
| touvron2023llama2, roziere2023code, jiang2023mistral, young2024yi | Llama2-7B; CodeLlama-7b/13b; Mistral-7B-v0.3; Yi-1.5-6B (Yi family). Yi-Coder-1.5B has no paper found before 2024-10 — name it as a model, do not invent a citation | Experiments |
| radford2019language | GPT-2 architecture of the synthetic 3rd-order Markov experiment | Experiments |
| sennrich2016neural | BPE (Fig. 4 uses BPE; deterministic merges define invalid encodings) | Method, Related work |
| kudo2018sentencepiece | SentencePiece (tokenizer of the Llama/Mistral family; "MPE"/SPM-style tokenizers) | Method, Related work |

## Related work — recommended
- **Tokenization theory / marginalizing tokenizations**: rajaraman2024toward (theory of tokenization; Markov-chain analysis of tokenized LMs — the closest prior framing for the synthetic experiments), cao2021you and chirkova2023should (marginal likelihood over tokenizations — the prior idea of marginalizing; contrast: they estimate string likelihood, this work computes exact next-byte probabilities for sampling), zouhar2023formal (formal BPE), zouhar2023tokenization, kudo2018subword and provilkov2020bpe (stochastic tokenization — encodings other than the canonical one), schuster2012japanese (WordPiece), bostrom2020byte, ali2024tokenizer, petrov2023language, mielke2021between (survey).
- **Byte-level / token-free LMs** (alternative: train token-free; this work converts existing tokenized models without retraining): xue2022byt5, clark2022canine, tay2022charformer, yu2023megabyte, wang2024mambabyte, nawrot2022hierarchical.
- **FIM / code infilling**: bavarian2022efficient, fried2023incoder, donahue2020enabling, li2023starcoder, roziere2023code (Code Llama FIM, PSM/SPM).
- **Prompt-boundary heuristics**: dagan2024getting (token healing), athiwaratkun2024token (token alignment); willard2023efficient (constrained/guided generation at the token level — vocabulary-level masking, related to filtering tokens by a byte prefix).
- **Ensembling LLMs**: jiang2023llmblender (ranking + fusion at output level), wan2024knowledge (FuseLLM; aligns distributions across vocabularies via training), huang2024ensemble (DeePEn; maps heterogeneous vocabularies to a relative-representation space), yu2024breaking (GaC; union vocabulary for token-level ensembling). Contrast: those need vocabulary alignment/training or output-level selection; the proposed byte space is exact and training-free.
- **General**: vaswani2017attention, brown2020language.

## Deliberately excluded
- Works dated after 2024-10 (e.g. later work on converting token-level LMs to character-level LMs) — cutoff rule.
- An arXiv paper on "tokenization bias" in LMs could not be verified by the index searches this turn; not included. Do not cite it unless verified.
- No entry is reconstructed from memory of any paper describing the studied method itself (knowledge-isolation rule).
