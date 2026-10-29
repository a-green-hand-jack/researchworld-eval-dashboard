Official NeurIPS 2026 LaTeX template, unmodified.
Source: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
(linked as "Paper template" from https://neurips.cc/Conferences/2026/CallForPapers; fetched 2026-10-28)
sha256 of the zip: 82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9
sha256 neurips_2026.sty  c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a
sha256 checklist.tex     780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6
sha256 neurips_2026.tex  cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797
Checked: compiles with latexmk -pdf (TeX Live in the sandbox); the unmodified example is 12 pages.
Usage: `\usepackage{neurips_2026}` (default = Main Track, double-blind). `neurips_2026.tex` ends with
`\input{checklist.tex}`; fill the 16 checklist items in place, using only \answerYes/\answerNo/\answerNA
and a 1-2 sentence justification pointing to sections.
