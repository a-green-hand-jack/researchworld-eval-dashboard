---
license: apache-2.0
task_categories:
- text-classification
language:
- en
pretty_name: LMSYS Chatbot Arena Human Preference Predictions
size_categories:
- 10K<n<100K
---
Dataset for [Kaggle competition](https://www.kaggle.com/competitions/lmsys-chatbot-arena/overview) on predicting human preference on Chatbot Arena battles. 
The training dataset includes over 55,000 real-world user and LLM conversations and user preferences across over 70 state-of-the-art LLMs, such as GPT-4, Claude 2, Llama 2, Gemini, and Mistral models.
Each sample represents a battle consisting of 2 LLMs which answer the same question, with a user label of either prefer model A, prefer model B, tie, or tie (both bad).

### Citation
Please cite the following paper if you find our leaderboard or dataset helpful.
```
@misc{chiang2024chatbot,
    title={Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference},
    author={Wei-Lin Chiang and Lianmin Zheng and Ying Sheng and Anastasios Nikolas Angelopoulos and Tianle Li and Dacheng Li and Hao Zhang and Banghua Zhu and Michael Jordan and Joseph E. Gonzalez and Ion Stoica},
    year={2024},
    eprint={2403.04132},
    archivePrefix={arXiv},
    primaryClass={cs.AI}
}
```
