# Framework Diagram Prompt

**Paper**: JIMP: Scale-Invariant Importance Shares for Shared-vs-Distinct Joint NMF Components

## Image Generation Prompt

Create a clean, vector-style methodology framework diagram for a top-tier ML paper titled "JIMP: Scale-Invariant Importance Shares for Shared-vs-Distinct Joint NMF Components." Layout: left-to-right data flow across four columns on a pure white background. Column 1 (input): two stacked rounded rectangles labeled "High-resolution data" and "Low-resolution data," filled with muted blue #4477AA at 15% opacity with #4477AA outlines. Column 2 (joint factorization): a large rounded box labeled "Joint NMF" in soft teal #44AA99, with four small output tiles beneath it labeled W_high, W_low, H_high, H_low, arranged in a 2x2 grid, connected by thin dark-grey arrows. Column 3 (component decomposition): two vertically split panels, one labeled "Common component (column 1)" in warm gold #CCBB44 and one labeled "Distinct component (column 2)" in soft purple #AA3377, each with small icons of stacked bars representing H-column energy. Column 4 (scoring): six compact rounded boxes stacked vertically with short labels: "Common error," "Common importance," "High importance," "Low importance," "Distinct error," "Distinct importance," colored by component family (gold for common, purple for distinct). Connect column 3 to column 4 with directional arrows. Add a small annotation near the output: "Scale-invariant shares → JSON." Use flat design, subtle drop shadows, consistent 1.5pt rounded corners, sans-serif typography (Helvetica/Arial style), dark grey #333333 text, uniform spacing, and a thin dashed bracket grouping the scoring stage. No photorealism, no gradients, no 3D effects, no decorative clutter.

## Usage Instructions

1. Copy the prompt above into an AI image generator (DALL-E 3, Midjourney, Ideogram, etc.)
2. Generate the image at high resolution (2048x1024 or similar landscape)
3. Save as `framework_diagram.png` in the same `charts/` folder
4. Insert into the paper's Method section using:
   - LaTeX: `\includegraphics[width=\textwidth]{charts/framework_diagram.png}`
   - Markdown: `![Framework Overview](charts/framework_diagram.png)`
