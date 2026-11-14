#!/usr/bin/env bash
set -euo pipefail
export CC=/hutian/.mamba/bin/x86_64-conda-linux-gnu-cc
export CXX=/hutian/.mamba/bin/x86_64-conda-linux-gnu-c++
export CMAKE_BUILD_PARALLEL_LEVEL=2
export CMAKE_ARGS='-DGGML_NATIVE=OFF -DGGML_AVX=ON -DGGML_AVX2=ON -DGGML_FMA=ON -DGGML_F16C=ON -DGGML_OPENMP=OFF'
python3 -m pip install --no-index --no-deps --no-build-isolation --force-reinstall /hutian/llama_cpp_python-0.3.18.tar.gz
python3 -c 'import llama_cpp; print("HUTIAN_WAKE: native llama-cpp-python ready",llama_cpp.__version__)'
