# Synthetic package in the official root PDF

Checked paper-repo main `07a6b51f5277f3e5606c3c87ccafc7b908683ba0`, root `paper.pdf` SHA-256 `f9fbea6534724ccadb4c5d3f9911fa5da45b7709fb37d4ee207ba308b2b36e98`. This is a check of the integrated scientific figures/table, not an independent approval of the full study or a claim that the real-model requirement is complete.

The 17-page PDF was read directly from that revision, not rebuilt locally. All seven pages containing delivered synthetic artwork/table were rasterized with PyMuPDF at 1.4x (100.8 dpi), opened as a contact sheet, and opened individually at their exported size:

| Root page | Delivered material | Inspection |
| --- | --- | --- |
| 4 | Figure 1: selection optimism / coverage | Axes, method/setting legends, nominal line, markers and caption readable; no clipping. |
| 5 | Table 1: numerical protocol comparison | All six columns within text area; setting rows, MCSEs and horizontal rules readable. Caption and prose correctly say declared settings. |
| 6 | Figure 2: width / quality / resource tradeoffs | Both rows and both legends readable; labels and long caption within the text area. |
| 11 | Figure 3: false-superiority rule | Three panels, 5% reference, method distinction and exact decision caption readable. |
| 12 | Figure 4: complete optimism grid | Both rows, colorbar, labels and scope caption readable. |
| 13 | Figure 5: complete coverage grid | Nominal-coverage diagnostic dots, colorbar and caveats readable. Vertical centering on the float page does not clip content. |
| 14 | Figure 6: MSE comparison | Logarithmic axis, six panels, protocol legend and squared-percentage-point unit readable. |

The six PDF assets, six PNG assets, numerical table LaTeX/CSV, render generator and two pinned input files (17 files) are byte-identical between paper main and the delivered figtab package. Direct inspection of each source PDF confirms 396 PDF-point native width and 8.0 pt minimum text. The root placement retains native full-line width, and the table is readable in its actual manuscript placement. The paper owner's integration record also reports embedded fonts and successful build checks; this presentation check did not repeat an unchanged manuscript build.

The original source and generators remain in `presentation/`, `figures/` and `tables/`. No experimental value, artwork or caption correction is needed. Paper-repo #2's integration answer is accepted, and figtab-repo #4's concrete typography/integration request is complete. Any later real-result integration will require another check of the changed root PDF.
