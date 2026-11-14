#!/bin/bash
. /work/venv/bin/activate; cd /work/code
M=/work/models; C=/work/cache
( python -u grid2.py $M/qwen2-1_5b-instruct-q8_0.gguf $C/m_qwen2_15b chatml 24 > /work/logs/m_qwen2_15b.log 2>&1 ) &
( python -u grid2.py $M/Qwen3-1.7B-Q8_0.gguf $C/m_qwen3_17b qwen3 24 > /work/logs/m_qwen3_17b.log 2>&1 ) &
( python -u grid2.py $M/Qwen3-0.6B-Q8_0.gguf $C/m_qwen3_06b qwen3 24 > /work/logs/m_qwen3_06b.log 2>&1; python -u grid2.py $M/qwen2.5-0.5b-instruct-q8_0.gguf $C/m_qwen25_05b chatml 24 > /work/logs/m_qwen25_05b.log 2>&1 ) &
wait
