"""Numbers transcribed from the frozen inputs (provenance in comments). No other numbers are introduced."""

# /initial-state/inputs/8/table_kf.tex  (Task 1, closed-set classification)
# (name, type, F1, R@1, R@3, R@5)
TASK1 = [
    ("GPT-4o",                      "LMM", 0.3732, 0.4243, 0.4991, 0.5221),
    ("Qwen2.5-VL-7B-Instruct",      "LMM", 0.2349, 0.3684, 0.4609, 0.4859),
    ("Qwen2-VL-7B-Instruct",        "LMM", 0.1594, 0.3656, 0.4590, 0.4781),
    ("llava-onevision-qwen2-7b-ov", "LMM", 0.1546, 0.3629, 0.4497, 0.4639),
    ("Qwen2-VL-3B-Instruct",        "LMM", 0.1386, 0.2663, 0.3250, 0.3517),
    ("llava-v1.6-34b",              "LMM", 0.1354, 0.2432, 0.3779, 0.4063),
    ("llava-v1.5-7b",               "LMM", 0.0991, 0.2140, 0.2721, 0.2973),
    ("llava-v1.6-mistral-7b",       "LMM", 0.0944, 0.1932, 0.2595, 0.2831),
    ("EVA-CLIP (ViT-g)",            "CLIP", 0.2465, 0.2654, 0.4897, 0.5944),
    ("CLIP (ViT-L/14)",             "CLIP", 0.2393, 0.2567, 0.4885, 0.6000),
]

# table_vs.tex  (Task 3, description-guided classification); model named in the source caption
VS_MODEL = "a Qwen-VL-7B-Instruct model"  # source caption: Qwen2.5-VL-7B-Instruct, but all four shared numbers equal the Qwen2-VL-7B row of table_kf; kept version-neutral until the analysis owner resolves (paper-repo#4)
VS = {  # metric order: F1, P@1, R@1, R@3, R@5
    "w/o description": (0.1594, 0.1019, 0.3656, 0.4590, 0.4781),
    "w/ description":  (0.2304, 0.1788, 0.3240, 0.4032, 0.4336),
}

# table_xj.tex  (distribution metrics; order per metric: CLIP, EVA-CLIP, Swin)
XJ = {
    "UEC-Food 256":    dict(trace=(71.21, 45.09, 264.00), sil=(0.0335, 0.0577, -0.0064),
                            db=(3.64, 3.02, 4.11), ch=(74.05, 115.80, 49.17)),
    "FoodLogAthl-218": dict(trace=(81.70, 49.92, 282.57), sil=(-0.0210, 0.0036, -0.0288),
                            db=(4.52, 3.68, 4.51), ch=(27.51, 51.51, 21.29)),
}

# table_zn.tex  (step, operation, images, bboxes, classes); step 0 is raw data
ZN = [
    (0, "Raw data",                               11460, 61414, 5889),
    (1, "Remove samples w/o image",               11460, 26646, 3167),
    (2, "Remove samples w/o bounding box",        11285, 26065, 3071),
    (3, r"Remove classes w/ $<$10 samples",        9121, 21944, 1180),
    (4, "Remove outliers based on image features", 7537, 17513, 1180),
    (5, "Manual review, remove invalid images",    6925, 14349, 1180),
    (6, "Merge similar classes, clean labels",     6925, 14349,  218),
]
# diff printed in the source for step 6 classes is -982 (1,180 -> 218 is -962)
