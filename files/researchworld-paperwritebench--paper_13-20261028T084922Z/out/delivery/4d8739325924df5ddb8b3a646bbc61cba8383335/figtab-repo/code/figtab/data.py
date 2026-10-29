"""Numbers transcribed from the supplied tables (/initial-state/inputs/8/table_kf.tex, table_zn.tex)."""
# model, family, F1, R@1, R@3, R@5   (table_kf.tex)
TASK1 = [
    ("GPT-4o", "LMM", 0.3732, 0.4243, 0.4991, 0.5221),
    ("Qwen2.5-VL-7B", "LMM", 0.2349, 0.3684, 0.4609, 0.4859),
    ("Qwen2-VL-7B", "LMM", 0.1594, 0.3656, 0.4590, 0.4781),
    ("Qwen2-VL-3B", "LMM", 0.1386, 0.2663, 0.3250, 0.3517),
    ("LLaVA-OneVision-7B", "LMM", 0.1546, 0.3629, 0.4497, 0.4639),
    ("EVA-CLIP (ViT-g)", "CLIP", 0.2465, 0.2654, 0.4897, 0.5944),
    ("CLIP (ViT-L/14)", "CLIP", 0.2393, 0.2567, 0.4885, 0.6000),
    ("LLaVA-v1.6-34B", "LMM", 0.1354, 0.2432, 0.3779, 0.4063),
    ("LLaVA-v1.5-7B", "LMM", 0.0991, 0.2140, 0.2721, 0.2973),
    ("LLaVA-v1.6-Mistral-7B", "LMM", 0.0944, 0.1932, 0.2595, 0.2831),
]
# step, operation, images, bboxes, classes   (table_zn.tex; step 0 raw)
FUNNEL = [
    ("0 Raw", 11460, 61414, 5889),
    ("1 No image", 11460, 26646, 3167),
    ("2 No bbox", 11285, 26065, 3071),
    ("3 Class <10", 9121, 21944, 1180),
    ("4 CLIP outliers", 7537, 17513, 1180),
    ("5 Manual review", 6925, 14349, 1180),
    ("6 Merge classes", 6925, 14349, 218),
]
