# Framework Diagram Prompt

**Paper**: Why the reviewer's request (more references) cannot be met by revision

## Image Generation Prompt

Clean academic architecture overview diagram, flat vector-art style, white background, left-to-right data flow, rounded-corner modules with subtle soft drop shadows, thin dark-grey outlines, sans-serif labels (Helvetica style), no photorealism.

Stage 1, far left, muted blue #4477AA box titled "Pairwise Comparison Data" with three small stacked sub-boxes: "Crowdsourced Votes", "Expert Annotation", "Model Judges", plus a fourth "Sports Matches". Arrow into Stage 2.

Stage 2, teal #44AA99 box "Bradley-Terry Fit", containing a small icon of a score ladder and the label "Scores + Confidence Intervals". Arrow into Stage 3.

Stage 3, center, warm gold #CCBB44 box "Perturbation Module" split into two stacked sub-boxes: "Random Noise (Resampling)" and "Targeted Edits (Adversarial)", with a small slider icon labeled "Perturbation Size". Arrow into Stage 4.

Stage 4, soft purple #AA3377 box "Refit and Re-rank", with a small before/after rank-bar icon. Arrow into Stage 5.

Stage 5, right side, muted blue #4477AA box "Sensitivity Metrics" with three short bullets: "Rank Shift", "Kendall Tau", "Top-k Stability".

Far right, teal #44AA99 box "Cross-Dataset Comparison" with caption "Conditions and Limitations". A thin dashed feedback arrow loops from Stage 5 back to Stage 3, labeled "Vary Magnitude". Small step numbers 1 to 5 in circles above each module. Even spacing, aligned baselines, generous margins, high information density without clutter, minimal text, publication-quality conference figure.

## Usage Instructions

1. Copy the prompt above into an AI image generator (DALL-E 3, Midjourney, Ideogram, etc.)
2. Generate the image at high resolution (2048x1024 or similar landscape)
3. Save as `framework_diagram.png` in the same `charts/` folder
4. Insert into the paper's Method section using:
   - LaTeX: `\includegraphics[width=\textwidth]{charts/framework_diagram.png}`
   - Markdown: `![Framework Overview](charts/framework_diagram.png)`
