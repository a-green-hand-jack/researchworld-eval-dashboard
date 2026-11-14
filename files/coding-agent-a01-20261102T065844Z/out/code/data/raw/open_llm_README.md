---
dataset_info:
  features:
  - name: eval_name
    dtype: string
  - name: Precision
    dtype: string
  - name: Type
    dtype: string
  - name: T
    dtype: string
  - name: Weight type
    dtype: string
  - name: Architecture
    dtype: string
  - name: Model
    dtype: string
  - name: fullname
    dtype: string
  - name: Model sha
    dtype: string
  - name: Average ⬆️
    dtype: float64
  - name: Hub License
    dtype: string
  - name: Hub ❤️
    dtype: int64
  - name: '#Params (B)'
    dtype: float64
  - name: Available on the hub
    dtype: bool
  - name: MoE
    dtype: bool
  - name: Flagged
    dtype: bool
  - name: Chat Template
    dtype: bool
  - name: CO₂ cost (kg)
    dtype: float64
  - name: IFEval Raw
    dtype: float64
  - name: IFEval
    dtype: float64
  - name: BBH Raw
    dtype: float64
  - name: BBH
    dtype: float64
  - name: MATH Lvl 5 Raw
    dtype: float64
  - name: MATH Lvl 5
    dtype: float64
  - name: GPQA Raw
    dtype: float64
  - name: GPQA
    dtype: float64
  - name: MUSR Raw
    dtype: float64
  - name: MUSR
    dtype: float64
  - name: MMLU-PRO Raw
    dtype: float64
  - name: MMLU-PRO
    dtype: float64
  - name: Merged
    dtype: bool
  - name: Official Providers
    dtype: bool
  - name: Upload To Hub Date
    dtype: string
  - name: Submission Date
    dtype: string
  - name: Generation
    dtype: int64
  - name: Base Model
    dtype: string
  splits:
  - name: train
    num_bytes: 4004719
    num_examples: 4576
  download_size: 1109997
  dataset_size: 4004719
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
---
