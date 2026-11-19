"""Family of each model (cluster label): HELM organisation from the name prefix; OLLB resolved base-model root organisation."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbprice.boards import load_helm, load_ollb, ollb_family


def fam_map(name):
    if name == "helm":
        b = load_helm(); org = {"Amazon": "Amazon", "Arctic": "Snowflake", "Claude": "Anthropic", "Command": "Cohere", "DBRX": "Databricks", "DeepSeek": "DeepSeek", "GPT": "OpenAI", "Gemini": "Google",
                                "Gemma": "Google", "PaLM": "Google", "Jamba": "AI21", "Llama": "Meta", "Mistral": "Mistral", "Mixtral": "Mistral", "OLMo": "AI2", "Palmyra": "Writer", "Phi": "Microsoft",
                                "Qwen": "Alibaba", "Solar": "Upstage", "Yi": "01.AI"}
        return b, dict(zip(b["names"], [org.get(n.split()[0].split("-")[0], n.split()[0]) for n in b["names"]]))
    b = load_ollb(name); return b, dict(zip(b["names"], ollb_family(b["meta"])[1]))
