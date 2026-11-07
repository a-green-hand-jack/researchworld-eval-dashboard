#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.venv/bin:$PATH"
revision=785322d17f2d51e5185cf996a1f4e46d87640841
if [ ! -d vendor/llama.cpp/.git ]; then
  git clone https://github.com/ggml-org/llama.cpp.git vendor/llama.cpp
fi
git -C vendor/llama.cpp checkout "$revision"
cmake -S vendor/llama.cpp -B vendor/llama.cpp/build -G Ninja \
  -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build vendor/llama.cpp/build --target llama-server -j 4
