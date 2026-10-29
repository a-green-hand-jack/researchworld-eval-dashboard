# Chatbot-Arena

- https://www.kaggle.com/competitions/lmsys-chatbot-arena/data
- Single-turn data: https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges
- #examples = 49938
- split: A_win =  17312 (34.67%), B_win = 16985 (34.01%), tie = 15641 (31.32%)
- #2-way only examples = 34297 (68.68%)

## This repository
- `train.single-turn.json`: data extracted from the train file from LMSys on Kaggle
  - each example has attributes - id, model\_[a, b], winne\_model\_[a, b, tie], question, answer\_[a, b]
- `llm-judges` folder contains predictions made by each judge (logits over `a` winning, `b` winning, and `tie`)
- `llm-judges-reversed` folder contains predictions like `llm-judges` but model_A is swapped with model_B (to mitigate positional bias) 

## LLM Judge Statistics
| Judge                        | 3-way Acc | 2-way (A_win or B_win) | 3-way (Reversed) | 2-way (Reversed) | 3-way (Avg) | 2-way (Avg) |    
|:-----------------------------|:----------|:-----------------------|:-----------------|:-----------------|:------------|:------------|
| Random Guessing              | 33.33     | 50.00                  | 33.33            | 50.00            | 33.33       | 50.00       | 
| dolphin-2.1-mistral-7b       | 36.23     | 53.23                  | 36.41            | 53.80            | 39.16       | 54.33       |
| StableBeluga-7B              | 37.77     | 55.03                  | 37.08            | 54.21            | 42.26       | 60.29       |
| Meta-Llama-3-8B              | 37.49     | 55.03                  | 36.48            | 53.66            | 43.95       | 61.90       |
| Mistral-7B-Instruct-v0.1     | 43.15     | 62.68                  | 43.11            | 62.58            | 44.50       | 63.90       |
| Mistral-7B-Instruct-v0.2     | 41.32     | 59.92                  | 41.05            | 59.61            | 44.97       | 64.63       |
| zephyr-7b-beta               | 42.11     | 59.03                  | 41.61            | 58.32            | 45.43       | 62.42       |
| Mistral-7B-OpenOrca          | 43.68     | 63.31                  | 43.63            | 63.14            | 45.69       | 65.34       |
| Meta-Llama-3-8B-Instruct     | 45.34     | 64.68                  | 45.37            | 64.66            | 47.02       | 66.55       |
| OpenHermes-2-Mistral-7B      | 44.23     | 63.22                  | 43.97            | 62.99            | 45.87       | 65.12       |
| OpenHermes-2.5-Mistral-7B    | 43.70     | 61.74                  | 43.10            | 60.96            | 46.73       | 65.48       |
| Starling-LM-7B-alpha         | 45.34     | 64.68                  | 46.01            | 64.31            | 47.50       | 65.46       |
|:-----------------------------|:----------|:-----------------------|:-----------------|:-----------------|:------------|:------------|
| Meta-Llama-3-70B-Instruct    | 51.37     | 70.81                  | 51.29            | 70.43            | 51.90       | 70.27       |
| Mixtral-8x7B-Instruct-v0.1   | 46.72     | 65.01                  | 46.40            | 64.49            | 48.20       | 65.60       |
| Qwen2-72B-Instruct           | 52.06     | 70.66                  | 51.72            | 70.47            | 52.89       | 59.70       |
| Hermes-3-Llama-3.1-70B       | 50.83     | 69.52                  | 51.13            | 69.96            | 51.50       | 68.95       |
| Athene-70B                   | 50.04     | 69.48                  | 50.18            | 69.49            | 50.84       | 69.85       |
| dolphin-2.5-mixtral-8x7b     | 35.75     | 52.48                  | 35.31            | 51.81            | 39.19       | 55.95       |


## Example of Judge's prompt

```
system_prompt = """Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. Do not provide any explanation, please provide your final verdict after \"Verdict:\" by strictly following this format: \"[[A]]\" if assistant A is better, \"[[B]]\" if assistant B is better, and \"[[C]]\" for a tie."""

prompt_template = """[User Question]\n{question}\n\n[The Start of Assistant A's Answer]\n{answer_a}\n[The End of Assistant A's Answer]\n\n[The Start of Assistant B's Answer]\n{answer_b}\n[The End of Assistant B's Answer]"""

partial_answer = """Verdict: [["""

messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": prompt},
    {"role": "assistant", "content": partial_answer}
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False) # then remove all special tokens after `Verdict: [[`
```

