#!/bin/bash
# Build script for metal_nws, including its kernel
# Exit on error
set -e

THREADS=4096
UNROLL=32

echo "--- Compiling with THREADS=$THREADS, UNROLL=$UNROLL ---"

echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/nws.metal -o bin/nws.air \
    -D THREADS=$THREADS -D UNROLL=$UNROLL
xcrun -sdk macosx metallib bin/nws.air -o bin/nws.metallib

echo "--- Compiling C Code ---"
# -g -fsanitize=address may be useful.
# -O2 for speed
clang++ -std=c++17 -O2 -o bin/metal_nws c_src/metal_nws.mm \
    -I$HOME/metal-cpp \
    -D THREADS=$THREADS -D UNROLL=$UNROLL \
    -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compilation Successful ---"
echo "To run: ./bin/metal_nws"