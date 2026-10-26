#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$project_dir/runtimes/llama.cpp"
pin=caa8191df159f764fb0160e3d2fc6be008948aee
if [[ ! -d "$source_dir/.git" ]]; then
    git clone https://github.com/ggml-org/llama.cpp.git "$source_dir"
    git -C "$source_dir" checkout --detach "$pin"
fi
[[ "$(git -C "$source_dir" rev-parse HEAD)" == "$pin" ]] || {
    echo 'Unexpected llama.cpp revision; review it before building.' >&2
    exit 1
}
cmake -S "$source_dir" -B "$source_dir/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
    -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_C_COMPILER=gcc-13 \
    -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CUDA_HOST_COMPILER=g++-13 \
    -DLLAMA_BUILD_TESTS=ON
cmake --build "$source_dir/build" --target \
    llama-cli llama-server llama-bench test-backend-ops -j "${BUILD_JOBS:-8}"
